"""One-time content preparation; generated output is reviewed before seeding."""
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
from visual_pdf import parse_visual_pdf


async def main():
    for n in (9, 10):
        target = ROOT / f"dpp_{n}_content.json"
        if target.exists():
            print(f"DPP {n}: existing output retained", flush=True)
            continue
        questions, warnings, kind = await parse_visual_pdf(
            (ROOT / "source_documents" / f"dpp-{n}-solutions.pdf").read_bytes(), "Biology", "adapt")
        target.write_text(json.dumps({"questions":questions,"warnings":warnings,"document_kind":kind},indent=2))
        print(f"DPP {n}: {len(questions)} questions prepared", flush=True)


if __name__ == "__main__":
    asyncio.run(main())