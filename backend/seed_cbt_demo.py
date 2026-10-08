"""Seed a JEE-Advanced-style demo CBT exam (idempotent, deterministic ids).

Creates 3 subjects (Physics, Chemistry, Mathematics), each with two sections:
  Section 1 — Single Correct MCQ  (+3 / -1)
  Section 2 — Numerical / Integer (+4 /  0)
Each section carries the standard NTA marking-scheme instruction text so the
exam screen can show it above the questions, exactly like the real interface.
"""
import uuid
from datetime import datetime, timezone

DEMO_TEST_ID = "demo-cbt-jee-advanced"
_NS = uuid.UUID("7f1c0b2e-0000-4000-8000-000000000001")


def _qid(subject: str, sec: int, n: int) -> str:
    return str(uuid.uuid5(_NS, f"{subject}-{sec}-{n}"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


MCQ_INSTR = (
    "This section contains THREE (03) questions.\n"
    "Each question has FOUR options (A), (B), (C) and (D). ONLY ONE of these four "
    "options is the correct answer.\n"
    "For each question, choose the option corresponding to the correct answer.\n"
    "Marking scheme:\n"
    "Full Marks: +3  If ONLY the correct option is chosen.\n"
    "Zero Marks:  0  If none of the options is chosen (i.e. the question is unanswered).\n"
    "Negative Marks: -1  In all other cases."
)
NUM_INSTR = (
    "This section contains TWO (02) questions.\n"
    "The answer to each question is a NON-NEGATIVE INTEGER.\n"
    "For each question, enter the correct integer using the on-screen keypad.\n"
    "Marking scheme:\n"
    "Full Marks: +4  If ONLY the correct integer is entered.\n"
    "Zero Marks:  0  In all other cases."
)

# subject -> { "mcq": [ (text, [A,B,C,D], correct_letter) ], "num": [ (text, answer) ] }
CONTENT = {
    "Physics": {
        "mcq": [
            ("A particle moves with constant acceleration. If it covers 10 m in the 1st second and 20 m in the 3rd second, its acceleration is:",
             ["2.5 m/s²", "5 m/s²", "7.5 m/s²", "10 m/s²"], "B"),
            ("The dimensional formula of coefficient of viscosity is:",
             ["[ML⁻¹T⁻¹]", "[MLT⁻¹]", "[ML⁻¹T⁻²]", "[M L² T⁻¹]"], "A"),
            ("A convex lens of focal length 20 cm forms a real image at 60 cm. The object distance is:",
             ["15 cm", "30 cm", "40 cm", "60 cm"], "B"),
        ],
        "num": [
            ("A body of mass 2 kg is acted upon by a force giving it an acceleration of 3 m/s². The magnitude of the net force (in newton) is:", "6"),
            ("The number of significant figures in 0.00430 is:", "3"),
        ],
    },
    "Chemistry": {
        "mcq": [
            ("Which of the following has the highest first ionisation enthalpy?",
             ["Na", "Mg", "Al", "Si"], "D"),
            ("The hybridisation of the central atom in SF₆ is:",
             ["sp³", "sp³d", "sp³d²", "sp³d³"], "C"),
            ("The number of sigma bonds in benzene (C₆H₆) is:",
             ["6", "9", "12", "3"], "C"),
        ],
        "num": [
            ("The oxidation number of chromium in K₂Cr₂O₇ is:", "6"),
            ("How many moles of electrons are needed to reduce 1 mole of MnO₄⁻ to Mn²⁺?", "5"),
        ],
    },
    "Mathematics": {
        "mcq": [
            ("If the roots of x² − 5x + 6 = 0 are α and β, then α + β equals:",
             ["5", "6", "−5", "1"], "A"),
            ("The derivative of sin(x²) with respect to x is:",
             ["cos(x²)", "2x·cos(x²)", "2x·sin(x²)", "−cos(x²)"], "B"),
            ("The value of ∫₀¹ 2x dx is:",
             ["0", "1", "2", "1/2"], "B"),
        ],
        "num": [
            ("The number of ways to arrange the letters of the word 'LEVEL' is:", "30"),
            ("If ⁿC₂ = 15, then n equals:", "6"),
        ],
    },
}


async def run_cbt_demo_seed(db):
    existing = await db.tests.find_one({"id": DEMO_TEST_ID}, {"_id": 0, "id": 1})
    # Always (re)build questions idempotently via deterministic ids.
    sections = []
    question_ids = []
    total_marks = 0
    for subject, blocks in CONTENT.items():
        # ----- Section 1: MCQ single -----
        sec1_qids = []
        for i, (text, opts, correct) in enumerate(blocks["mcq"], start=1):
            qid = _qid(subject, 1, i)
            doc = {
                "id": qid, "type": "mcq_single", "subject": subject,
                "chapter": "", "topic": "", "difficulty": "medium",
                "marks": 3, "negative_marks": 1, "text": text,
                "options": opts, "correct": [correct], "explanation": "",
                "language": "English", "status": "approved", "source": "demo-cbt",
                "section": "Section 1", "created_at": _now(),
            }
            await db.questions.update_one({"id": qid}, {"$set": doc}, upsert=True)
            sec1_qids.append(qid); question_ids.append(qid); total_marks += 3
        sections.append({
            "id": f"{subject}::{subject} Section 1",
            "name": f"{subject} Section 1",
            "question_ids": sec1_qids,
            "instructions": MCQ_INSTR,
        })
        # ----- Section 2: Numerical -----
        sec2_qids = []
        for i, (text, ans) in enumerate(blocks["num"], start=1):
            qid = _qid(subject, 2, i)
            doc = {
                "id": qid, "type": "integer", "subject": subject,
                "chapter": "", "topic": "", "difficulty": "medium",
                "marks": 4, "negative_marks": 0, "text": text,
                "options": [], "correct": [ans], "explanation": "",
                "language": "English", "status": "approved", "source": "demo-cbt",
                "section": "Section 2", "created_at": _now(),
                "numerical_validation": {"integerOnly": True, "allowDecimal": False,
                                         "allowNegative": False, "maxDecimalPlaces": 0, "maxLength": 6},
            }
            await db.questions.update_one({"id": qid}, {"$set": doc}, upsert=True)
            sec2_qids.append(qid); question_ids.append(qid); total_marks += 4
        sections.append({
            "id": f"{subject}::{subject} Section 2",
            "name": f"{subject} Section 2",
            "question_ids": sec2_qids,
            "instructions": NUM_INSTR,
        })

    test_doc = {
        "id": DEMO_TEST_ID,
        "title": "JEE Advanced 2026 — Demo Mock Test",
        "exam_type": "full_mock",
        "description": "A short demo mock in the official computer-based-test (CBT) interface.",
        "subjects": list(CONTENT.keys()),
        "duration_minutes": 60,
        "total_marks": total_marks,
        "negative_marking": True,
        "shuffle_questions": False,
        "shuffle_options": False,
        "show_solutions_after": True,
        "assigned_to": [],
        "sections": sections,
        "question_ids": question_ids,
        "published": True,
        "is_demo": True,
        "instructions_en": (
            "Total duration of the paper is 60 minutes. The on-screen countdown timer in the "
            "top-right corner shows the remaining time; when it reaches zero the exam ends "
            "automatically. Only answers you have SAVED will be recorded and submitted."
        ),
        "created_by_role": "system",
        "created_at": _now(),
    }
    await db.tests.update_one({"id": DEMO_TEST_ID}, {"$set": test_doc}, upsert=True)
    return {"test_id": DEMO_TEST_ID, "questions": len(question_ids),
            "sections": len(sections), "created": not bool(existing)}
