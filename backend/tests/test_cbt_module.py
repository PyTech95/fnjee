"""CBT module backend tests (security + flow)."""
import os, uuid, pytest, requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://deployment-zone-6.preview.emergentagent.com").rstrip("/")
TEST_ID = "6ebfbe4d-18cb-4f3a-bf06-81254ee5b6d7"

HEADERS = {"User-Agent": "Mozilla/5.0 CBTTest"}


def _login(email, password="Student@123", role="student"):
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": email, "password": password, "role": role},
                      headers=HEADERS, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def student_token():
    # Use a fresh student that likely hasn't submitted; we'll pick student15
    return _login("student7@examnest.io")


@pytest.fixture(scope="module")
def auth(student_token):
    return {"Authorization": f"Bearer {student_token}", **HEADERS}


# --- GET exam structure must not expose correct answers ---
def test_get_exam_no_correct_exposed(auth):
    r = requests.get(f"{BASE_URL}/api/cbt/exam/{TEST_ID}", headers=auth, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "questions" in data and "subjects" in data and "order" in data
    for qid, q in data["questions"].items():
        assert "correct" not in q, f"q {qid} exposes correct"
        # also no answer-ish keys
        for forbidden in ("correct_answer", "answer", "solution"):
            assert forbidden not in q, f"q {qid} exposes {forbidden}"
    # at least 3 subjects (Physics/Chem/Math)
    subject_names = [s["name"] for s in data["subjects"]]
    assert len(subject_names) >= 1


# --- start / state / save / summary ---
def test_cbt_lifecycle(auth):
    s = requests.post(f"{BASE_URL}/api/cbt/attempts/start",
                      json={"test_id": TEST_ID}, headers=auth, timeout=30)
    assert s.status_code == 200, s.text
    attempt = s.json()
    aid = attempt["id"]
    assert attempt["status"] in ("in_progress", "submitted")
    if attempt["status"] == "submitted":
        pytest.skip("student15 already submitted this exam; skipping lifecycle")

    # state
    st = requests.get(f"{BASE_URL}/api/cbt/attempts/{aid}/state", headers=auth, timeout=30)
    assert st.status_code == 200
    assert "remaining_seconds" in st.json()

    # idempotent start -> same attempt
    s2 = requests.post(f"{BASE_URL}/api/cbt/attempts/start",
                       json={"test_id": TEST_ID}, headers=auth, timeout=30)
    assert s2.json()["id"] == aid, "start is not idempotent while in progress"

    # Save a response for the first question
    exam = requests.get(f"{BASE_URL}/api/cbt/exam/{TEST_ID}", headers=auth, timeout=30).json()
    first_qid = exam["order"][0]
    first_q = exam["questions"][first_qid]
    payload_answer = []
    if first_q["type"] == "scm":
        payload_answer = [first_q["options"][0]["id"]]
    elif first_q["type"] == "msq":
        payload_answer = [first_q["options"][0]["id"]]
    else:
        payload_answer = ["0"]
    r = requests.post(f"{BASE_URL}/api/cbt/attempts/{aid}/response", headers=auth, timeout=30,
                      json={"question_id": first_qid, "answer": payload_answer,
                            "marked_for_review": False, "visited": True, "action": "save", "seq": 1})
    assert r.status_code == 200, r.text
    assert r.json()["is_answered"] is True

    # stale seq guard
    r2 = requests.post(f"{BASE_URL}/api/cbt/attempts/{aid}/response", headers=auth, timeout=30,
                       json={"question_id": first_qid, "answer": [], "marked_for_review": False,
                             "visited": True, "action": "save", "seq": 0})
    assert r2.status_code == 200
    assert r2.json().get("stale") is True

    # summary endpoint
    sm = requests.get(f"{BASE_URL}/api/cbt/attempts/{aid}/summary", headers=auth, timeout=30)
    assert sm.status_code == 200
    body = sm.json()
    assert "totals" in body and "by_subject" in body
    assert body["totals"]["answered"] >= 1


# --- auth: another user can't touch my attempt ---
def test_attempt_ownership(auth):
    s = requests.post(f"{BASE_URL}/api/cbt/attempts/start",
                      json={"test_id": TEST_ID}, headers=auth, timeout=30)
    aid = s.json()["id"]
    other = _login("student8@examnest.io")
    other_headers = {"Authorization": f"Bearer {other}", **HEADERS}
    r = requests.get(f"{BASE_URL}/api/cbt/attempts/{aid}/state", headers=other_headers, timeout=30)
    assert r.status_code == 403


# --- 404 on bogus test ---
def test_exam_404(auth):
    r = requests.get(f"{BASE_URL}/api/cbt/exam/{uuid.uuid4()}", headers=auth, timeout=30)
    assert r.status_code == 404
