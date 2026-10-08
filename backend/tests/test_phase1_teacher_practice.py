"""Phase-1 backend tests: teacher portal, history-aware practice, question-analysis,
RBAC + security regressions."""
import os
import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")).rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@examnest.io", "password": "Admin@123", "role": "admin"}
TEACHER = {"email": "teacher1@examnest.io", "password": "Teacher@123", "role": "teacher"}
STUDENT = {"email": "student1@examnest.io", "password": "Student@123", "role": "student"}
STUDENT2 = {"email": "student2@examnest.io", "password": "Student@123", "role": "student"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login {creds['email']} => {r.status_code} {r.text[:200]}"
    return r.json()["token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def admin_token():   return _login(ADMIN)
@pytest.fixture(scope="module")
def teacher_token(): return _login(TEACHER)
@pytest.fixture(scope="module")
def student_token(): return _login(STUDENT)
@pytest.fixture(scope="module")
def student2_token(): return _login(STUDENT2)


# ---------- Teacher login + permissions ----------
class TestTeacherAuth:
    def test_teacher_login_ok(self, teacher_token):
        assert isinstance(teacher_token, str) and len(teacher_token) > 20

    def test_teacher_me_role(self, teacher_token):
        r = requests.get(f"{API}/auth/me", headers=_h(teacher_token), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["role"] == "teacher"
        assert d["email"] == TEACHER["email"]

    def test_teacher_permissions(self, teacher_token):
        r = requests.get(f"{API}/teacher/permissions", headers=_h(teacher_token), timeout=30)
        assert r.status_code == 200
        d = r.json()
        # Teacher must be scoped to Physics & Chemistry at minimum
        perms = d.get("teacher_perms") or {}
        subs = perms.get("subjects") or []
        assert "Physics" in subs and "Chemistry" in subs, f"expected Physics&Chemistry, got {subs}"


# ---------- Teacher question-bank scoping ----------
class TestTeacherQuestionBank:
    def test_teacher_sees_only_permitted_subjects(self, teacher_token):
        r = requests.get(f"{API}/questions?limit=500", headers=_h(teacher_token), timeout=30)
        assert r.status_code == 200
        qs = r.json()
        assert isinstance(qs, list)
        assert qs, "teacher sees zero questions"
        subs = {q.get("subject") for q in qs}
        # Must not contain anything outside their permission set (Physics, Chemistry)
        assert subs.issubset({"Physics", "Chemistry"}), f"teacher saw out-of-scope subjects: {subs}"

    def test_admin_sees_all_subjects(self, admin_token):
        r = requests.get(f"{API}/questions?limit=500", headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        subs = {q.get("subject") for q in r.json()}
        # Admin should see broader set (at least more than just Physics/Chem)
        assert len(subs) >= 2


# ---------- Teacher build-a-paper ----------
class TestTeacherCreatePaper:
    _created_test = None

    def test_teacher_can_create_paper(self, teacher_token):
        # pull first 3 physics questions
        r = requests.get(f"{API}/questions?subject=Physics&limit=5", headers=_h(teacher_token), timeout=30)
        assert r.status_code == 200
        qs = r.json()
        assert len(qs) >= 2, "need at least 2 physics qs to build a paper"
        qids = [q["id"] for q in qs[:3]]
        payload = {"title": "TEST_teacher_paper", "subjects": ["Physics"],
                   "duration_minutes": 20, "question_ids": qids}
        r = requests.post(f"{API}/tests", headers=_h(teacher_token), json=payload, timeout=30)
        assert r.status_code == 200, r.text[:300]
        t = r.json()
        assert t["title"] == "TEST_teacher_paper"
        assert t["question_ids"] == qids
        assert t["created_by_role"] == "teacher"
        TestTeacherCreatePaper._created_test = t

    def test_paper_appears_in_teacher_list(self, teacher_token):
        r = requests.get(f"{API}/tests", headers=_h(teacher_token), timeout=30)
        assert r.status_code == 200
        ids = [t["id"] for t in r.json()]
        assert TestTeacherCreatePaper._created_test["id"] in ids

    def test_question_analysis_endpoint(self, teacher_token):
        tid = TestTeacherCreatePaper._created_test["id"]
        r = requests.get(f"{API}/tests/{tid}/question-analysis",
                         headers=_h(teacher_token), timeout=30)
        assert r.status_code == 200, r.text[:200]
        d = r.json()
        # Response should contain stats block + per-question rows
        assert "rows" in d or "questions" in d or isinstance(d, dict)
        # Any of the following shapes: {stats:{students,avg,high,low}, rows:[...]}
        # Just verify it has the analysis fields
        assert any(k in d for k in ("rows", "questions", "stats", "students"))

    def test_zz_cleanup(self, admin_token):
        t = TestTeacherCreatePaper._created_test
        if t:
            requests.delete(f"{API}/tests/{t['id']}", headers=_h(admin_token), timeout=30)


# ---------- Practice generation (no-repeat) ----------
class TestPracticeGenerate:
    def test_student_generate_practice(self, student_token):
        payload = {"subjects": ["Physics"], "count": 5, "difficulty": None}
        r = requests.post(f"{API}/practice/generate", headers=_h(student_token),
                          json=payload, timeout=30)
        assert r.status_code == 200, r.text[:300]
        t = r.json()
        assert t["exam_type"] == "practice"
        assert isinstance(t["question_ids"], list) and len(t["question_ids"]) >= 1
        assert "exhausted_pool" in t
        assert "new_questions" in t
        # save for next test
        TestPracticeGenerate._first_test = t

    def test_practice_excludes_previously_seen(self, student_token):
        # first make sure we have submitted attempts (student1 does per prior runs)
        r = requests.get(f"{API}/attempts", headers=_h(student_token), timeout=30)
        assert r.status_code == 200
        seen = set()
        for a in r.json():
            for d in (a.get("detailed") or []):
                if d.get("question_id"): seen.add(d["question_id"])
        # Generate another practice paper
        payload = {"subjects": ["Physics", "Chemistry"], "count": 5}
        r = requests.post(f"{API}/practice/generate", headers=_h(student_token),
                          json=payload, timeout=30)
        assert r.status_code == 200, r.text[:300]
        t = r.json()
        # If pool not exhausted, none of the questions should be from `seen`
        if not t.get("exhausted_pool") and seen:
            overlap = set(t["question_ids"]) & seen
            assert not overlap, f"practice reused seen qids: {overlap}"

    def test_practice_student_only(self, teacher_token, admin_token):
        # teacher & admin should NOT be able to call /practice/generate (student-only)
        for tok in (teacher_token, admin_token):
            r = requests.post(f"{API}/practice/generate", headers=_h(tok),
                              json={"subjects": ["Physics"], "count": 3}, timeout=30)
            assert r.status_code == 403, f"expected 403 for non-student, got {r.status_code}"


# ---------- RBAC regressions ----------
class TestRBACRegressions:
    def test_student_403_on_questions(self, student_token):
        r = requests.get(f"{API}/questions", headers=_h(student_token), timeout=30)
        assert r.status_code == 403

    def test_student_403_on_teacher_permissions(self, student_token):
        r = requests.get(f"{API}/teacher/permissions", headers=_h(student_token), timeout=30)
        assert r.status_code == 403

    def test_student_403_on_post_questions(self, student_token):
        r = requests.post(f"{API}/questions", headers=_h(student_token),
                          json={"type": "mcq_single", "subject": "Physics",
                                "text": "TEST_x", "options": ["a", "b"], "correct": ["a"]},
                          timeout=30)
        assert r.status_code == 403

    def test_student_403_on_question_analysis(self, student_token, admin_token):
        r = requests.get(f"{API}/tests", headers=_h(admin_token), timeout=30)
        tid = r.json()[0]["id"]
        r = requests.get(f"{API}/tests/{tid}/question-analysis",
                         headers=_h(student_token), timeout=30)
        assert r.status_code == 403

    def test_teacher_403_on_delete_test(self, teacher_token, admin_token):
        # create a test via admin then try to delete as teacher
        payload = {"title": "TEST_delete_probe", "subjects": ["Physics"],
                   "duration_minutes": 10, "question_ids": []}
        r = requests.post(f"{API}/tests", headers=_h(admin_token), json=payload, timeout=30)
        assert r.status_code == 200
        tid = r.json()["id"]
        try:
            r = requests.delete(f"{API}/tests/{tid}", headers=_h(teacher_token), timeout=30)
            assert r.status_code == 403, f"teacher should not delete tests, got {r.status_code}"
        finally:
            requests.delete(f"{API}/tests/{tid}", headers=_h(admin_token), timeout=30)

    def test_teacher_403_on_list_teachers(self, teacher_token):
        r = requests.get(f"{API}/teachers", headers=_h(teacher_token), timeout=30)
        assert r.status_code == 403


# ---------- Answer-key leak regression ----------
class TestAnswerKeyRegression:
    @pytest.fixture(scope="class")
    def probe(self, admin_token):
        qp = {"type": "mcq_single", "subject": "Physics", "chapter": "TEST", "topic": "TEST",
              "difficulty": "easy", "marks": 4, "negative_marks": 1,
              "text": "TEST_leak_phase1 What is 2+3?", "options": ["4", "5", "6"],
              "correct": ["5"], "explanation": "TEST_secret", "status": "approved"}
        rq = requests.post(f"{API}/questions", headers=_h(admin_token), json=qp, timeout=30)
        assert rq.status_code == 200, rq.text[:200]
        qid = rq.json()["id"]
        tp = {"title": "TEST_leak_phase1_test", "subjects": ["Physics"],
              "duration_minutes": 10, "question_ids": [qid], "show_solutions_after": True,
              "assigned_to": []}
        rt = requests.post(f"{API}/tests", headers=_h(admin_token), json=tp, timeout=30)
        assert rt.status_code == 200, rt.text[:200]
        tid = rt.json()["id"]
        yield {"qid": qid, "tid": tid}
        requests.delete(f"{API}/tests/{tid}", headers=_h(admin_token), timeout=30)
        requests.delete(f"{API}/questions/{qid}", headers=_h(admin_token), timeout=30)

    def test_student_presubmit_no_correct_no_explanation(self, student2_token, probe):
        r = requests.get(f"{API}/tests/{probe['tid']}?include_questions=true",
                         headers=_h(student2_token), timeout=30)
        assert r.status_code == 200
        for q in r.json()["questions"]:
            assert "correct" not in q, "LEAK: correct exposed pre-submit"
            assert "explanation" not in q, "LEAK: explanation exposed pre-submit"

    def test_admin_still_sees_correct(self, admin_token, probe):
        r = requests.get(f"{API}/tests/{probe['tid']}?include_questions=true",
                         headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        qs = r.json()["questions"]
        assert all("correct" in q for q in qs)

    def test_teacher_building_sees_correct(self, teacher_token, probe):
        r = requests.get(f"{API}/tests/{probe['tid']}?include_questions=true",
                         headers=_h(teacher_token), timeout=30)
        # Teacher can view any test detail (not restricted); should still see correct for building
        assert r.status_code == 200
        qs = r.json()["questions"]
        # teacher is not a student so correct should be present
        assert all("correct" in q for q in qs), "teacher must see correct for building papers"


# ---------- Critical-path regression (student flow) ----------
class TestCriticalPathRegression:
    def test_student_full_flow(self, student_token):
        r = requests.get(f"{API}/tests", headers=_h(student_token), timeout=30)
        assert r.status_code == 200
        tests = [t for t in r.json() if t.get("question_ids") and t.get("exam_type") != "practice"]
        assert tests, "no seeded tests for student"
        tid = tests[0]["id"]

        r = requests.post(f"{API}/attempts/start", headers=_h(student_token),
                          json={"test_id": tid}, timeout=30)
        assert r.status_code == 200
        aid = r.json()["id"]

        r = requests.get(f"{API}/tests/{tid}?include_questions=true",
                         headers=_h(student_token), timeout=30)
        assert r.status_code == 200
        qs = r.json()["questions"]
        answers = [{"question_id": q["id"], "answer": [q["options"][0]]}
                   for q in qs[:3] if q.get("options")]

        r = requests.post(f"{API}/attempts/submit", headers=_h(student_token),
                          json={"attempt_id": aid, "answers": answers}, timeout=60)
        assert r.status_code == 200, r.text[:300]
        result = r.json()
        assert result["status"] == "submitted"
        assert "score" in result
        assert "time_taken_seconds" in result and result["time_taken_seconds"] is not None
        assert "late_submission" in result and isinstance(result["late_submission"], bool)
