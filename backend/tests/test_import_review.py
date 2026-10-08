"""Regression tests for iteration 2: regex_extractor fixes (raw_text 2-option case,
answer key propagation), PDF/PMD parse+commit, partial batch, subjective+image submit,
courses pricing."""
import os
import time
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@examnest.io", "password": "Admin@123", "role": "admin"}
STUDENT = {"email": "student1@examnest.io", "password": "Student@123", "role": "student"}

PDF_PATH = "/tmp/uploads/physics.pdf"
PMD_PATH = "/tmp/uploads/chem.pmd"

TINY_PNG_B64 = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_h():
    return {"Authorization": f"Bearer {_login(ADMIN)}"}


@pytest.fixture(scope="module")
def student_ctx():
    tok = _login(STUDENT)
    r = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {tok}"}, timeout=15)
    return {"h": {"Authorization": f"Bearer {tok}"}, "user": r.json()}


# ---- REGRESSION 1: raw_text 2-option snippet (was buggy in iter 1) ----
def test_raw_text_2option_with_answer_key(admin_h):
    snippet = ("1. What is 2+2?\n1) 3   2) 4\n"
               "2. What is capital of India?\n1) Mumbai   2) Delhi\n"
               "Answer key:\n1) 2   2) 2")
    r = requests.post(f"{API}/import/parse", headers=admin_h,
                      data={"raw_text": snippet, "subject_default": "GK", "use_ai": "false"}, timeout=30)
    assert r.status_code == 200, r.text
    b = r.json()
    print(f"raw_text 2opt: count={b['count']} qs={[(q.get('text')[:40], q.get('type'), q.get('options'), q.get('correct')) for q in b['questions']]}")
    assert b["count"] == 2, f"expected 2, got {b['count']}"
    for q in b["questions"]:
        assert q["type"] == "mcq_single", f"expected mcq_single, got {q['type']}"
        assert len(q["options"]) == 2
        assert q["correct"] == ["B"], f"expected ['B'], got {q['correct']}"


# ---- REGRESSION 2: 4-option 3-question with answer key covering all 3 ----
def test_raw_text_4option_multi_answer_key(admin_h):
    snippet = (
        "1. Which is SI unit of force?\n1) Watt   2) Newton   3) Joule   4) Pascal\n\n"
        "2. Value of g?\n1) 8.9   2) 9.8   3) 10.1   4) 11.2\n\n"
        "3. Speed of light m/s?\n1) 3e5   2) 3e6   3) 3e7   4) 3e8\n\n"
        "Answer Key:\n1) 2   2) 2   3) 4"
    )
    r = requests.post(f"{API}/import/parse", headers=admin_h,
                      data={"raw_text": snippet, "subject_default": "Physics", "use_ai": "false"}, timeout=30)
    assert r.status_code == 200, r.text
    b = r.json()
    print(f"raw_text 4opt: count={b['count']} corrects={[q.get('correct') for q in b['questions']]}")
    assert b["count"] == 3
    corr = [q["correct"] for q in b["questions"]]
    assert corr == [["B"], ["B"], ["D"]], f"unexpected corrects: {corr}"
    for q in b["questions"]:
        assert q["type"] == "mcq_single"
        assert len(q["options"]) == 4


# ---- Physics PDF regex-only parse + commit ----
def test_physics_pdf_regex_only(admin_h):
    if not os.path.exists(PDF_PATH):
        pytest.skip("PDF not present")
    with open(PDF_PATH, "rb") as f:
        files = {"file": ("physics.pdf", f, "application/pdf")}
        data = {"subject_default": "Physics", "use_ai": "false"}
        t0 = time.time()
        r = requests.post(f"{API}/import/parse", headers=admin_h, files=files, data=data, timeout=180)
        el = time.time() - t0
    assert r.status_code == 200, r.text
    b = r.json()
    print(f"PDF parse: count={b['count']} used_regex={b['used_regex']} used_ai={b['used_ai']} elapsed={el:.1f}s")
    assert b["used_ai"] is False
    assert b["used_regex"] is True
    assert b["count"] >= 25, f"expected >=25 got {b['count']}"
    # every question should have 4 options
    opts_ok = sum(1 for q in b["questions"] if len(q.get("options", [])) == 4)
    print(f"PDF: {opts_ok}/{b['count']} questions have exactly 4 options")
    assert opts_ok >= 25

    payload = {"questions": b["questions"]}
    rc = requests.post(f"{API}/import/commit", headers={**admin_h, "Content-Type": "application/json"},
                       json=payload, timeout=120)
    assert rc.status_code == 200, rc.text
    cb = rc.json()
    print(f"PDF commit: inserted={cb['inserted']} skipped={cb['skipped']}")
    assert cb["inserted"] >= 25
    assert cb["skipped"] == 0
    # verify saved as mcq_single (fetch a few)
    rq = requests.get(f"{API}/questions?subject=Physics&limit=5", headers=admin_h, timeout=15)
    if rq.status_code == 200:
        arr = rq.json() if isinstance(rq.json(), list) else rq.json().get("questions", [])
        types = [q.get("type") for q in arr[:5]]
        print(f"Saved question types sample: {types}")


# ---- PMD: no NameError ----
def test_chem_pmd_no_name_error(admin_h):
    if not os.path.exists(PMD_PATH):
        pytest.skip("PMD not present")
    with open(PMD_PATH, "rb") as f:
        files = {"file": ("chem.pmd", f, "application/octet-stream")}
        data = {"subject_default": "Chemistry", "use_ai": "false"}
        r = requests.post(f"{API}/import/parse", headers=admin_h, files=files, data=data, timeout=180)
    assert r.status_code == 200, r.text
    b = r.json()
    print(f"PMD parse: count={b['count']} errors={b['errors'][:2]}")
    for e in b["errors"]:
        assert "regex_extract_questions" not in e, f"NameError still present: {e}"
    assert b["count"] >= 0


# ---- Commit tolerates bad row ----
def test_commit_partial_batch(admin_h):
    payload = {
        "questions": [
            {"text": "", "subject": "Physics", "type": "mcq_single"},
            {"text": "TEST_partial Valid question?", "options": ["A", "B", "C", "D"],
             "correct": ["A"], "subject": "Physics", "type": "mcq_single"},
        ]
    }
    r = requests.post(f"{API}/import/commit", headers={**admin_h, "Content-Type": "application/json"},
                      json=payload, timeout=30)
    assert r.status_code == 200
    d = r.json()
    print(f"partial commit: {d}")
    assert d["inserted"] == 1
    assert d["skipped"] == 1
    skipped_details = d.get("skipped_details", [])
    assert skipped_details, "expected skipped_details to be populated"
    reason = str(skipped_details[0].get("reason", "")).lower()
    assert "empty" in reason and "question" in reason and "text" in reason, f"reason mismatch: {reason}"


# ---- Subjective + image_answer -> pending_grading ----
def test_subjective_image_answer(admin_h, student_ctx):
    q_payload = {
        "type": "subjective", "subject": "Physics", "chapter": "TEST_sub",
        "topic": "TEST_sub", "difficulty": "medium", "marks": 4, "negative_marks": 0,
        "text": "TEST_subjective Derive lens formula.", "options": [], "correct": [],
        "explanation": "", "language": "English", "status": "approved",
    }
    rq = requests.post(f"{API}/questions", json=q_payload, headers=admin_h, timeout=15)
    assert rq.status_code == 200, rq.text
    qid = rq.json()["id"]

    rt = requests.post(f"{API}/tests", json={
        "title": "TEST_subjective_flow", "exam_type": "chapter_wise",
        "subjects": ["Physics"], "duration_minutes": 30, "question_ids": [qid],
    }, headers=admin_h, timeout=15)
    assert rt.status_code == 200
    tid = rt.json()["id"]

    sid = student_ctx["user"]["id"]
    requests.post(f"{API}/tests/assign", json={"test_id": tid, "student_ids": [sid]},
                  headers=admin_h, timeout=10)

    sh = student_ctx["h"]
    rs = requests.post(f"{API}/attempts/start", json={"test_id": tid}, headers=sh, timeout=15)
    assert rs.status_code == 200, rs.text
    aid = rs.json()["id"]

    rsub = requests.post(f"{API}/attempts/submit", headers=sh, json={
        "attempt_id": aid,
        "answers": [{"question_id": qid, "answer": [], "image_answer": TINY_PNG_B64, "marked_review": False}],
    }, timeout=30)
    assert rsub.status_code == 200, rsub.text
    d = rsub.json()
    print(f"subjective submit: status={d['status']} detailed[0]={d['detailed'][0]}")
    dd = d["detailed"][0]
    assert dd["result"] == "pending_grading", f"expected pending_grading got {dd['result']}"

    requests.delete(f"{API}/tests/{tid}", headers=admin_h, timeout=10)
    requests.delete(f"{API}/questions/{qid}", headers=admin_h, timeout=10)


# ---- Courses pricing ----
def test_courses_pricing():
    r = requests.get(f"{API}/courses", timeout=30)
    assert r.status_code == 200
    courses = r.json()
    print(f"courses: {[(c.get('title'), c.get('price')) for c in courses]}")
    assert len(courses) == 6
    bio = [c for c in courses if "Masterclass" in c.get("title", "") and "Biology" in c.get("title", "")]
    assert bio and bio[0]["price"] == 399
    aiims = [c for c in courses if "Target AIIMS" in c.get("title", "")]
    assert aiims and aiims[0]["price"] == 1499
