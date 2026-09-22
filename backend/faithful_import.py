"""Faithful copy with independent page inventory, original crops and review diagnostics."""
import asyncio
import base64
from collections import Counter
import json
import logging
import os
import re
import tempfile
import uuid
from pathlib import Path

import pymupdf
from faithful_prompts import INVENTORY, TRANSCRIBE
from visual_pdf import crop_image

log = logging.getLogger(__name__)
_lock = asyncio.Semaphore(1)


async def read_json(path, system, prompt):
    from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType, TextDelta
    async with _lock:
        chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"faithful-{uuid.uuid4()}",
                       system_message=system).with_model("gemini", "gemini-3-flash-preview").with_params(max_tokens=32768)
        parts = []
        async with asyncio.timeout(240):
            async for ev in chat.stream_message(UserMessage(text=prompt, file_contents=[
                FileContentWithMimeType(file_path=path, mime_type="application/pdf")])):
                if isinstance(ev, TextDelta): parts.append(ev.content)
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", "".join(parts).strip())
        value = json.loads(raw)
        if not isinstance(value, dict): raise ValueError("Document reader returned an invalid response. Please retry.")
        return value


def regions(doc, values, issues, name):
    output = []
    for crop in values if isinstance(values, list) else []:
        image = crop_image(doc, crop)
        if image:
            output.append({"image_url": image, "page": int(crop["page"]), "bbox": crop["bbox"], "alt": f"Original {name}, page {crop['page']}"})
        else:
            issues.append(f"An original {name} region could not be copied; review the source page.")
    return output


def question_from_source(doc, raw, subject):
    issues = [str(x) for x in raw.get("issues", [])]
    snapshots = regions(doc, raw.get("source_regions"), issues, "question")
    if not snapshots: issues.append("Original question crop missing — select its region from the source page.")
    opts = raw.get("options") or []
    labels = raw.get("option_labels") or []
    option_images = []
    for i in range(len(opts)):
        crop = (raw.get("option_regions") or [])[i:i+1]
        image = crop_image(doc, crop[0]) if crop else None
        if crop and crop[0] and not image: issues.append(f"Option {i+1} image could not be copied.")
        option_images.append(image)
    solutions = regions(doc, raw.get("solution_regions"), issues, "solution")
    correct = raw.get("correct") or []
    if not correct: issues.append("Answer key absent — set it before publishing an automatically scored question.")
    return {
        "text": raw.get("text") or "[Unreadable question — review original]", "options": opts,
        "option_labels": [str(labels[i]) if i < len(labels) else chr(65+i) for i in range(len(opts))],
        "correct": correct if isinstance(correct, list) else [str(correct)],
        "type": raw.get("type", "mcq_single"), "subject": raw.get("subject") or subject,
        "chapter": raw.get("chapter") or "", "difficulty": "medium", "marks": 4, "negative_marks": 1,
        "explanation": raw.get("explanation") or "", "source_images": snapshots, "option_images": option_images,
        "explanation_images": solutions, "image_url": snapshots[0]["image_url"] if snapshots else None,
        "image_alt": "Original question with all its source content", "explanation_image_url": None,
        "source_number": raw.get("source_number"), "source_label": str(raw.get("source_label", "")),
        "source_page": raw.get("source_page"), "faithful_copy": True, "source_verified": False,
        "import_issues": list(dict.fromkeys(issues)), "status": "review", "content_origin": "pdf_extracted",
    }


async def parse_faithful(pdf, subject, page_names):
    errors, questions, report = [], [], []
    with pymupdf.open(stream=pdf, filetype="pdf") as doc:
        # Full-page originals remain admin-only in the transient import response, never a question field.
        pages = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=pymupdf.Matrix(1800/max(page.rect.width,page.rect.height), 1800/max(page.rect.width,page.rect.height)), alpha=False)
            pages.append({"page": i+1, "label": page_names[i], "image_url": "data:image/png;base64," + base64.b64encode(pix.tobytes("png")).decode()})
        with tempfile.TemporaryDirectory(prefix="faithful-") as tmp:
            path = str(Path(tmp) / "original.pdf"); Path(path).write_bytes(pdf)
            inventory = await read_json(path, INVENTORY, f"Inventory all {len(doc)} pages. Only original question starts, not solution entries.")
            listed = {int(p["page"]): p for p in inventory.get("pages", []) if isinstance(p,dict) and isinstance(p.get("page"),int)}
            for page in range(1,len(doc)+1):
                row = listed.get(page, {"page":page,"kind":"unknown","starts":[],"issues":["Page was not inventoried; manual review required."]})
                report.append(row)
                errors.extend(f"Page {page}: {issue}" for issue in row.get("issues", []))
            kind = inventory.get("document_kind", "unknown")
            if kind == "solutions":
                errors.append("This upload contains solutions, not original questions. Exact question copying requires the original paper. Adapted practice remains a separate, non-exact mode.")
            else:
                for start in range(1,len(doc)+1,4):
                    stop = min(start+3,len(doc))
                    expected = [r for r in report if start <= r["page"] <= stop]
                    if all(r.get("kind") in ("solutions","blank","other","continuation") and not r.get("starts") for r in expected): continue
                    try:
                        result = await read_json(path, TRANSCRIBE,
                            f"Subject hint: {subject}. Transcribe ONLY questions whose stems START on pages {start}–{stop}; include their continuation and shared passage regions anywhere in the full PDF. Use the full document's answer key if supplied. Inventory: {json.dumps(expected)}")
                        errors.extend(str(e) for e in result.get("issues", []))
                        for raw in result.get("questions", []):
                            if not isinstance(raw,dict):
                                errors.append(f"Pages {start}–{stop}: an unreadable question record needs manual review."); continue
                            if not isinstance(raw.get("source_page"),int) or not start <= raw["source_page"] <= stop:
                                errors.append(f"Question {raw.get('source_label','?')} has an ambiguous start page; check for omissions.")
                                continue
                            questions.append(question_from_source(doc,raw,subject))
                    except Exception:
                        log.exception("Faithful transcription batch failed")
                        errors.append(f"Pages {start}–{stop} could not be transcribed completely. Retry the upload or add their questions manually from the source pages.")
            expected = Counter((p["page"],str(label)) for p in report for label in p.get("starts", []))
            actual = Counter((q["source_page"],q["source_label"]) for q in questions)
            for (page,label),count in (expected-actual).items(): errors.append(f"Missing from extraction: page {page}, question {label} ({count}).")
            for (page,label),count in (actual-expected).items(): errors.append(f"Inventory mismatch: page {page}, question {label} ({count}); verify numbering and duplicates.")
            coverage = {"pages":report,"expected_questions":sum(expected.values()),"extracted_questions":len(questions),
                        "matched":expected == actual and not errors,"review_required":True}
            return questions, list(dict.fromkeys(errors)), kind, {"source_pages":pages,"coverage":coverage}