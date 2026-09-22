"""Critical regression tests for DPP visual/content import and student answer-visibility rules."""

import io
import os
import time
import uuid

import fitz
import pytest
import requests


def _base_url() -> str:
    base = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if not base:
        with open("/app/frontend/.env", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    base = line.split("=", 1)[1].strip()
                    break
    assert base, "REACT_APP_BACKEND_URL missing"
    return base.rstrip("/")


BASE = _base_url()
API = f"{BASE}/api"

ADMIN = {"email": "admin@examnest.io", "password": "Admin@123", "role": "admin"}
STUDENT3 = {"email": "student3@examnest.io", "password": "Student@123", "role": "student"}

DPP9_ID = "0e87d454-f910-5e29-824f-6f37a26a14ff"
DPP10_ID = "93498a34-4acf-5660-b70e-ebdefcb810f7"
CBSE_ID = "d57fa55c-fe98-51ec-a701-4e9ebc0c59d2"


def _login(creds: dict) -> str:
    res = requests.post(f"{API}/auth/login", json=creds, timeout=40)
    assert res.status_code == 200, f"login failed: {res.status_code} {res.text}"
    token = res.json().get("token")
    assert isinstance(token, str) and token
    return token


def _fresh_student_headers() -> dict:
    # Existing dedicated, unsubmitted account; recorded in memory/test_credentials.md.
    tok = _login({"email": "autotest_9a7230e39d@examnest.io", "password": "Student@123", "role": "student"})
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def admin_h():
    return {"Authorization": f"Bearer {_login(ADMIN)}"}


@pytest.fixture(scope="module")
def student3_h():
    return {"Authorization": f"Bearer {_login(STUDENT3)}"}


def _table_count(questions):
    return sum("| ---" in (q.get("text") or "") or "| :---" in (q.get("text") or "") for q in questions)


def _image_count(questions):
    return sum(bool(q.get("image_url")) for q in questions)


# --- Seeded DPP and CBSE dataset verification ---
@pytest.mark.parametrize(
    "tid,expected_images,expected_tables",
    [
        (DPP9_ID, 7, 4),
        (DPP10_ID, 6, 5),
    ],
)
def test_seeded_dpp_structure_and_marking_contract(admin_h, tid, expected_images, expected_tables):
    res = requests.get(f"{API}/tests/{tid}", params={"include_questions": "true"}, headers=admin_h, timeout=60)
    assert res.status_code == 200, res.text
    test_doc = res.json()

    assert test_doc["id"] == tid
    assert test_doc.get("total_marks") == 80
    assert test_doc.get("negative_marking") is True

    questions = test_doc.get("questions", [])
    assert len(questions) == 20
    assert _image_count(questions) == expected_images
    assert _table_count(questions) == expected_tables

    for q in questions:
        assert q.get("content_origin") == "ai_adapted"
        assert len(q.get("options") or []) == 4
        correct = q.get("correct") or []
        assert len(correct) == 1
        assert correct[0] in ["A", "B", "C", "D"]
        assert q.get("marks") == 4
        assert q.get("negative_marks") == 1


def test_cbse_matching_questions_have_real_markdown_tables_and_count(admin_h):
    res = requests.get(f"{API}/tests/{CBSE_ID}", params={"include_questions": "true"}, headers=admin_h, timeout=60)
    assert res.status_code == 200, res.text
    test_doc = res.json()
    questions = test_doc.get("questions", [])

    assert len(questions) == 75
    assert _image_count(questions) == 17

    q_by_num = {idx + 1: q for idx, q in enumerate(questions)}
    for num in range(31, 39):
        text = q_by_num[num].get("text") or ""
        assert "| --- | --- |" in text, f"Q{num} table separator missing"
        assert "|" in text and "\n|" in text, f"Q{num} not rendered as markdown table text"
        assert len(q_by_num[num].get("options") or []) == 4
        assert len(q_by_num[num].get("correct") or []) == 1


# --- Student pre/post submit answer visibility contract ---
def test_student_pre_submit_hides_correct_hint_explanation_keeps_question_images():
    fresh_student_h = _fresh_student_headers()
    res = requests.get(
        f"{API}/tests/{DPP10_ID}",
        params={"include_questions": "true"},
        headers=fresh_student_h,
        timeout=60,
    )
    assert res.status_code == 200, res.text
    t = res.json()
    qs = t.get("questions") or []
    assert len(qs) == 20

    for q in qs:
        assert "correct" not in q
        assert "hint" not in q
        assert "explanation" not in q
        assert "explanation_image_url" not in q
    assert _image_count(qs) == 6


def test_student3_submit_attempt_and_post_submit_reveals_solutions(student3_h):
    started = requests.post(
        f"{API}/attempts/start",
        json={"test_id": DPP10_ID},
        headers=student3_h,
        timeout=40,
    )
    assert started.status_code == 200, started.text
    attempt = started.json()
    assert attempt.get("id")

    if attempt.get("status") == "submitted":
        attempt_id = attempt["id"]
    else:
        # Pre-submit pull (hidden answer key), answer with deterministic safe choice
        test_doc = requests.get(
            f"{API}/tests/{DPP10_ID}",
            params={"include_questions": "true"},
            headers=student3_h,
            timeout=60,
        ).json()
        answers = [{"question_id": q["id"], "answer": ["A"], "marked_review": False} for q in test_doc.get("questions", [])]

        submitted = requests.post(
            f"{API}/attempts/submit",
            json={"attempt_id": attempt["id"], "answers": answers},
            headers=student3_h,
            timeout=70,
        )
        assert submitted.status_code == 200, submitted.text
        attempt_id = submitted.json()["id"]

    # after submit, include_questions should now reveal explanation fields for student
    after = requests.get(
        f"{API}/tests/{DPP10_ID}",
        params={"include_questions": "true"},
        headers=student3_h,
        timeout=60,
    )
    assert after.status_code == 200, after.text
    aq = after.json().get("questions") or []
    assert len(aq) == 20

    assert all("correct" not in q for q in aq), "answer key leaked post-submit"
    assert any(bool((q.get("explanation") or "").strip()) for q in aq), "expected explanation after submit"
    assert any(bool(q.get("explanation_image_url")) for q in aq), "expected at least one explanation image after submit"

    # score/totals should be server-computed and stable
    ares = requests.get(f"{API}/attempts/{attempt_id}", headers=student3_h, timeout=40)
    assert ares.status_code == 200
    ad = ares.json()
    assert ad.get("status") == "submitted"
    assert isinstance(ad.get("score"), (int, float))
    assert ad.get("total_marks") == 80


# --- Multimodal PDF import regression ---
def _make_solutions_only_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 60), "DPP 10 Solutions", fontsize=16)
    page.insert_text((50, 100), "1) Solution: Cardiac output = stroke volume x heart rate", fontsize=12)
    page.insert_text((50, 124), "2) Solution: Monocytes are largest WBC and become macrophages", fontsize=12)
    page.insert_text((50, 148), "Answer key: 1-B, 2-C", fontsize=12)
    data = doc.tobytes()
    doc.close()
    return data


def _make_two_question_fixture_pdf(tag: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    y = 55
    page.insert_text((40, y), f"{tag} Biology Practice", fontsize=15)
    y += 35
    page.insert_text((40, y), "1. Which value equals cardiac output from this table?", fontsize=12)
    y += 18
    page.insert_text((40, y), "| Measurement | Value |", fontsize=11)
    y += 16
    page.insert_text((40, y), "| --- | --- |", fontsize=11)
    y += 16
    page.insert_text((40, y), "| Stroke volume | 70 mL/beat |", fontsize=11)
    y += 16
    page.insert_text((40, y), "| Heart rate | 80 beats/min |", fontsize=11)
    y += 18
    page.insert_text((40, y), "A. 1500 mL/min   B. 5600 mL/min   C. 700 mL/min   D. 1120 mL/min", fontsize=11)
    y += 35
    page.insert_text((40, y), "2. In the schematic, label P carries blood from intestine to liver.", fontsize=12)
    y += 18
    page.draw_rect(fitz.Rect(55, y, 165, y + 45), color=(0, 0, 0), width=1)
    page.insert_text((66, y + 25), "Intestine", fontsize=10)
    page.draw_rect(fitz.Rect(245, y, 355, y + 45), color=(0, 0, 0), width=1)
    page.insert_text((278, y + 25), "Liver", fontsize=10)
    page.draw_line((166, y + 22), (244, y + 22), color=(0, 0, 0), width=1)
    page.insert_text((197, y + 14), "P", fontsize=11)
    y += 65
    page.insert_text((40, y), "A. Pulmonary artery  B. Hepatic portal vein  C. Hepatic vein  D. Vena cava", fontsize=11)
    y += 38
    page.insert_text((40, y), "Answer key: 1) B   2) B", fontsize=12)
    data = doc.tobytes()
    doc.close()
    return data


def test_pdf_extract_mode_solutions_only_returns_zero_and_warning(admin_h):
    # Prefer requested local file; if unavailable, use generated solutions-only fixture.
    local_path = "/app/backend/source_documents/dpp-10-solutions.pdf"
    payload_bytes = None
    filename = "dpp-10-solutions.pdf"
    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            payload_bytes = f.read()
    else:
        payload_bytes = _make_solutions_only_pdf()
        filename = "generated-solutions-only.pdf"

    files = {"file": (filename, io.BytesIO(payload_bytes), "application/pdf")}
    data = {"use_ai": "true", "subject_default": "Biology", "import_mode": "extract"}
    t0 = time.time()
    res = requests.post(f"{API}/import/parse", headers=admin_h, files=files, data=data, timeout=260)
    elapsed = time.time() - t0

    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("document_kind") == "solutions"
    assert body.get("count") == 0
    errs = " ".join(body.get("errors") or []).lower()
    assert "solutions" in errs and "adapt" in errs
    assert elapsed < 250


def test_pdf_extract_two_question_fixture_commit_and_cleanup(admin_h):
    tag = f"TEST_FIX_{uuid.uuid4().hex[:8]}"
    fixture_pdf = _make_two_question_fixture_pdf(tag)
    files = {"file": (f"{tag}.pdf", io.BytesIO(fixture_pdf), "application/pdf")}
    data = {"use_ai": "true", "subject_default": "Biology", "import_mode": "extract"}

    parse = requests.post(f"{API}/import/parse", headers=admin_h, files=files, data=data, timeout=260)
    assert parse.status_code == 200, parse.text
    parsed = parse.json()

    assert parsed.get("document_kind") == "questions"
    assert parsed.get("count", 0) >= 2, f"fixture extraction too low: {parsed}"

    # Data contract checks from parser output before commit
    q1 = parsed["questions"][0]
    assert "|" in q1["text"] and "---" in q1["text"], "Table was flattened"
    assert parsed["questions"][1].get("image_url", "").startswith("data:image/png;base64,"), "Source diagram was lost"
    assert all(q.get("correct") == ["B"] for q in parsed["questions"][:2])
    assert isinstance(q1.get("image_alt"), str)
    assert "content_origin" in q1
    assert q1.get("content_origin") == "pdf_extracted"

    commit = requests.post(
        f"{API}/import/commit",
        headers={**admin_h, "Content-Type": "application/json"},
        json={"questions": parsed["questions"][:2], "subject_default": "Biology"},
        timeout=90,
    )
    assert commit.status_code == 200, commit.text
    cbody = commit.json()
    assert cbody.get("inserted", 0) >= 1

    # cleanup: locate committed rows using source filename and remove via admin API
    listed = requests.get(f"{API}/questions", params={"limit": 1000}, headers=admin_h, timeout=50)
    assert listed.status_code == 200
    rows = listed.json() or []
    for row in rows:
        if row.get("source") == f"{tag}.pdf":
            requests.delete(f"{API}/questions/{row['id']}", headers=admin_h, timeout=20)


# --- Targeted checks: _strip_q image fields for adaptive / battles ---
def test_adaptive_flow_returns_question_image_fields_and_post_answer_explanation_image(student3_h):
    start = requests.post(
        f"{API}/adaptive/start",
        json={"subject": "Biology", "length": 5},
        headers=student3_h,
        timeout=50,
    )
    assert start.status_code == 200, start.text
    body = start.json()
    q = body.get("question") or {}
    assert "image_url" in q
    assert "image_alt" in q

    ans = requests.post(
        f"{API}/adaptive/answer",
        json={"session_id": body["session_id"], "question_id": q["id"], "selected": ["A"]},
        headers=student3_h,
        timeout=50,
    )
    assert ans.status_code == 200, ans.text
    adb = ans.json()
    assert "explanation_image_url" in adb


def test_battle_state_question_contains_image_fields(student3_h):
    create = requests.post(
        f"{API}/battles/create",
        json={"subject": "Biology", "num_questions": 3},
        headers=student3_h,
        timeout=50,
    )
    assert create.status_code == 200, create.text
    room = create.json()

    start = requests.post(f"{API}/battles/{room['id']}/start", headers=student3_h, timeout=40)
    assert start.status_code == 200, start.text

    state = requests.get(f"{API}/battles/{room['id']}", headers=student3_h, timeout=40)
    assert state.status_code == 200, state.text
    sb = state.json()
    q = sb.get("question") or {}
    assert "image_url" in q
    assert "image_alt" in q
