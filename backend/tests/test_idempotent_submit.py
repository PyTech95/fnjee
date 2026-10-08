"""Idempotent double-submit + persistence test."""
import os
import time
import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")).rstrip("/")
API = f"{BASE_URL}/api"

STUDENT = {"email": "student3@examnest.io", "password": "Student@123", "role": "student"}


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def student_token():
    r = requests.post(f"{API}/auth/login", json=STUDENT, timeout=30)
    if r.status_code != 200:
        # fallback to student1
        r = requests.post(f"{API}/auth/login",
                          json={"email": "student1@examnest.io", "password": "Student@123", "role": "student"},
                          timeout=30)
    assert r.status_code == 200, r.text[:200]
    return r.json()["token"]


def test_health():
    r = requests.get(f"{API}/health", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "healthy"


def test_idempotent_submit_and_persistence(student_token):
    # find a test
    r = requests.get(f"{API}/tests", headers=_h(student_token), timeout=30)
    assert r.status_code == 200
    tests = [t for t in r.json() if t.get("question_ids")]
    assert tests, "No test with questions available"
    tid = tests[0]["id"]

    # start
    r = requests.post(f"{API}/attempts/start", headers=_h(student_token),
                      json={"test_id": tid}, timeout=30)
    assert r.status_code == 200, r.text[:300]
    aid = r.json()["id"]

    # get questions (student view)
    r = requests.get(f"{API}/tests/{tid}?include_questions=true",
                     headers=_h(student_token), timeout=30)
    qs = r.json()["questions"]
    answers = []
    for q in qs[:3]:
        if q.get("options"):
            answers.append({"question_id": q["id"], "answer": [q["options"][0]]})

    # first submit
    r1 = requests.post(f"{API}/attempts/submit", headers=_h(student_token),
                       json={"attempt_id": aid, "answers": answers}, timeout=60)
    assert r1.status_code == 200, r1.text[:300]
    first = r1.json()
    assert first["status"] == "submitted"

    # second submit with different answers - must be idempotent
    time.sleep(1)
    alt_answers = []
    for q in qs[:3]:
        if q.get("options") and len(q["options"]) > 1:
            alt_answers.append({"question_id": q["id"], "answer": [q["options"][1]]})
    r2 = requests.post(f"{API}/attempts/submit", headers=_h(student_token),
                       json={"attempt_id": aid, "answers": alt_answers}, timeout=60)
    assert r2.status_code == 200, r2.text[:300]
    second = r2.json()
    # Score must be identical (idempotent)
    assert second["score"] == first["score"], f"Score changed on resubmit: {first['score']} -> {second['score']}"
    assert second["correct"] == first["correct"]
    assert second["wrong"] == first["wrong"]

    # persistence check
    r = requests.get(f"{API}/attempts", headers=_h(student_token), timeout=30)
    assert r.status_code == 200
    ids = [a["id"] for a in r.json()]
    assert aid in ids, "Submitted attempt not found in GET /api/attempts"
