"""Batch 1 tests: AI Doubt-Solver, Notes->Quiz, personal-quiz regression.

Focus: verify backend contract used by the new frontend pages.
"""
import os, time
import pytest, requests

_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not _URL:
    with open("/app/frontend/.env") as f:
        for l in f:
            if l.startswith("REACT_APP_BACKEND_URL="):
                _URL = l.split("=", 1)[1].strip()
                break
BASE = _URL.rstrip("/") + "/api"


def _login(email, password, role):
    r = requests.post(f"{BASE}/auth/login",
                      json={"email": email, "password": password, "role": role})
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def student_token():
    # use student2 to avoid colliding with any login-limiter tests
    return _login("student2@examnest.io", "Student@123", "student")


@pytest.fixture(scope="module")
def admin_token():
    return _login("admin@examnest.io", "Admin@123", "admin")


def _h(t): return {"Authorization": f"Bearer {t}"}


# ---------- AI Doubt Solver ----------
class TestDoubtSolver:
    def test_doubt_solve_returns_solution(self, student_token):
        payload = {"question": "State Newton's second law and explain briefly.",
                   "subject": "Physics"}
        r = requests.post(f"{BASE}/ai/doubt-solve", json=payload,
                          headers=_h(student_token), timeout=45)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "solution" in d and isinstance(d["solution"], str)
        assert len(d["solution"]) > 30
        assert d["question"].startswith("State Newton")

    def test_doubt_solve_rejects_short(self, student_token):
        r = requests.post(f"{BASE}/ai/doubt-solve",
                          json={"question": "hi"}, headers=_h(student_token))
        assert r.status_code == 400

    def test_doubt_history(self, student_token):
        r = requests.get(f"{BASE}/ai/doubt-history", headers=_h(student_token))
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list)
        # our just-solved doubt should be here
        assert any("Newton" in (d.get("question") or "") for d in arr)


# ---------- Notes -> Quiz ----------
NOTES = (
    "Newton's laws of motion. First law: an object stays at rest or moves at "
    "constant velocity unless acted on by a net external force (inertia). "
    "Second law: F = m*a; the net force on a body equals mass times acceleration. "
    "Third law: for every action there is an equal and opposite reaction. "
    "Momentum p = m*v is conserved when net external force is zero. "
    "Weight W = m*g on Earth where g ~ 9.8 m/s^2."
)


@pytest.fixture(scope="module")
def generated_quiz(student_token):
    data = {"raw_text": NOTES, "subject_default": "Physics",
            "num_questions": "5", "title": "TEST_NewtonNotes"}
    r = requests.post(f"{BASE}/practice/from-document", data=data,
                      headers=_h(student_token), timeout=60)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["count"] >= 3
    return j


class TestNotesQuiz:
    def test_quiz_generated(self, generated_quiz):
        assert "test_id" in generated_quiz
        assert generated_quiz["title"].startswith("TEST_")

    def test_my_quizzes_lists_it(self, student_token, generated_quiz):
        r = requests.get(f"{BASE}/practice/my-quizzes", headers=_h(student_token))
        assert r.status_code == 200
        ids = [q["id"] for q in r.json()]
        assert generated_quiz["test_id"] in ids

    def test_can_load_generated_test(self, student_token, generated_quiz):
        tid = generated_quiz["test_id"]
        r = requests.get(f"{BASE}/tests/{tid}",
                         params={"include_questions": "true"},
                         headers=_h(student_token))
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("questions"), "no questions on generated test"
        # answer key hidden pre-submit
        for q in body["questions"]:
            assert "correct" not in q

    def test_attempt_and_submit_no_coins(self, student_token, generated_quiz):
        tid = generated_quiz["test_id"]
        # coins before
        me1 = requests.get(f"{BASE}/auth/me", headers=_h(student_token)).json()
        c1 = me1.get("reward_coins", 0)
        start = requests.post(f"{BASE}/attempts/start", json={"test_id": tid},
                              headers=_h(student_token))
        assert start.status_code == 200, start.text
        aid = start.json()["id"]
        # answer first question with option 0
        qs = start.json().get("questions") or []
        answers = [{"question_id": q["id"], "answer": 0} for q in qs[:2]]
        sub = requests.post(f"{BASE}/attempts/submit",
                            json={"attempt_id": aid, "answers": answers},
                            headers=_h(student_token))
        assert sub.status_code == 200, sub.text
        assert "score" in sub.json()
        # coins unchanged (personal quizzes must not award coins)
        me2 = requests.get(f"{BASE}/auth/me", headers=_h(student_token)).json()
        c2 = me2.get("reward_coins", 0)
        assert c2 == c1, f"personal quiz awarded coins: {c1} -> {c2}"


# ---------- Regression: admin bank excludes personal ----------
class TestAdminBankExcludesPersonal:
    def test_admin_questions_excludes_personal(self, admin_token, generated_quiz):
        r = requests.get(f"{BASE}/questions", headers=_h(admin_token))
        assert r.status_code == 200
        for q in r.json():
            assert q.get("personal") is not True, "personal question leaked into bank"


# ---------- Regression: counselling ----------
class TestLandingCounselling:
    def test_counselling_submit(self):
        payload = {"name": "TEST_Buyer", "phone": "9999999999",
                   "email": "test_buyer@example.com", "message": "info"}
        # try both JSON and form
        r = requests.post(f"{BASE}/counselling", json=payload)
        assert r.status_code in (200, 201), r.text
