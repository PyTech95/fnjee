"""Iteration 11 tests:
- PATCH /api/questions/{qid} (admin partial update, validation)
- PUT /api/questions/{qid} regression
- Cron endpoints auth: /api/cron/weekly-digest, /api/cron/study-reminder
- Managed Resend proxy send_email() to delivered@resend.dev
- /api/ready health
"""
import os
import asyncio
import pytest
import requests
from dotenv import dotenv_values

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://fnjee-deploy.preview.emergentagent.com").rstrip("/")
ENV = dotenv_values("/app/backend/.env")
CRON_SECRET = ENV.get("WEBHOOK_CRON_SECRET", "").strip('"').strip("'")

ADMIN = {"email": "admin@examnest.io", "password": "Admin@123", "role": "admin"}
STUDENT = {"email": "student1@examnest.io", "password": "Student@123", "role": "student"}


def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT)


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def student_headers(student_token):
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture(scope="module")
def seed_question(admin_headers):
    payload = {
        "text": "TEST_PATCH What is 2+2?",
        "options": ["3", "4", "5", "6"],
        "correct": ["B"],
        "subject": "Physics",
        "chapter": "Arithmetic",
        "difficulty": "easy",
        "marks": 4,
        "negative": 1,
    }
    r = requests.post(f"{BASE_URL}/api/questions", json=payload, headers=admin_headers, timeout=20)
    assert r.status_code == 200, r.text
    q = r.json()
    yield q
    # cleanup
    requests.delete(f"{BASE_URL}/api/questions/{q['id']}", headers=admin_headers, timeout=20)


def test_ready_health():
    r = requests.get(f"{BASE_URL}/api/ready", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ok") is True or data.get("status") in ("ok", "healthy", "ready") or "db" in data


def test_patch_partial_difficulty(admin_headers, seed_question):
    q = seed_question
    r = requests.patch(
        f"{BASE_URL}/api/questions/{q['id']}",
        json={"difficulty": "hard"},
        headers=admin_headers,
        timeout=20,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["difficulty"] == "hard"
    assert data["text"] == q["text"]
    assert data["options"] == q["options"]
    assert data["correct"] == q["correct"]
    # restore
    r2 = requests.patch(
        f"{BASE_URL}/api/questions/{q['id']}",
        json={"difficulty": "easy"},
        headers=admin_headers,
        timeout=20,
    )
    assert r2.status_code == 200
    assert r2.json()["difficulty"] == "easy"


def test_patch_invalid_enum(admin_headers, seed_question):
    r = requests.patch(
        f"{BASE_URL}/api/questions/{seed_question['id']}",
        json={"difficulty": "ultra"},
        headers=admin_headers,
        timeout=20,
    )
    assert r.status_code == 422, f"got {r.status_code}: {r.text}"


def test_patch_unknown_field(admin_headers, seed_question):
    r = requests.patch(
        f"{BASE_URL}/api/questions/{seed_question['id']}",
        json={"foo_bar": "baz"},
        headers=admin_headers,
        timeout=20,
    )
    assert r.status_code == 400, f"got {r.status_code}: {r.text}"


def test_patch_nonexistent(admin_headers):
    r = requests.patch(
        f"{BASE_URL}/api/questions/nonexistent-qid-xyz",
        json={"difficulty": "hard"},
        headers=admin_headers,
        timeout=20,
    )
    assert r.status_code == 404


def test_patch_student_forbidden(student_headers, seed_question):
    r = requests.patch(
        f"{BASE_URL}/api/questions/{seed_question['id']}",
        json={"difficulty": "hard"},
        headers=student_headers,
        timeout=20,
    )
    assert r.status_code == 403


def test_put_full_regression(admin_headers, seed_question):
    q = seed_question
    full = {
        "text": q["text"],
        "options": q["options"],
        "correct": q["correct"],
        "subject": q["subject"],
        "chapter": q.get("chapter", "Arithmetic"),
        "difficulty": "medium",
        "marks": 4,
        "negative": 1,
    }
    r = requests.put(f"{BASE_URL}/api/questions/{q['id']}", json=full, headers=admin_headers, timeout=20)
    assert r.status_code == 200, r.text
    assert r.json()["difficulty"] == "medium"


def test_cron_weekly_digest_unauthorized():
    r = requests.post(f"{BASE_URL}/api/cron/weekly-digest", timeout=20)
    assert r.status_code == 401


def test_cron_weekly_digest_authorized():
    assert CRON_SECRET, "WEBHOOK_CRON_SECRET missing from backend/.env"
    r = requests.post(
        f"{BASE_URL}/api/cron/weekly-digest",
        headers={"Authorization": f"Bearer {CRON_SECRET}"},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ok") is True
    assert data.get("status") == "accepted"


def test_cron_study_reminder_unauthorized():
    r = requests.post(f"{BASE_URL}/api/cron/study-reminder", timeout=20)
    assert r.status_code == 401


def test_cron_study_reminder_authorized():
    r = requests.post(
        f"{BASE_URL}/api/cron/study-reminder",
        headers={"Authorization": f"Bearer {CRON_SECRET}"},
        timeout=20,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("status") == "accepted"


def test_managed_resend_send_email():
    """Call email_utils.send_email() directly to delivered@resend.dev; expect a non-null id."""
    import sys
    sys.path.insert(0, "/app/backend")
    # Ensure env from backend/.env is loaded (test cwd may differ)
    from dotenv import load_dotenv
    load_dotenv("/app/backend/.env", override=False)
    os.environ["EMERGENT_EMAIL_KEY"] = ENV.get("EMERGENT_EMAIL_KEY", "").strip('"').strip("'")
    import importlib
    import email_utils
    importlib.reload(email_utils)

    async def _go():
        return await email_utils.send_email(
            to="delivered@resend.dev",
            subject="FNJEE automated test ping",
            html="<p>Automated test email from iteration 11. Please ignore.</p>",
        )

    msg_id = asyncio.run(_go())
    assert msg_id, f"expected non-null id from managed Resend proxy, got {msg_id!r}"
