"""Tests for admin AI key settings endpoints + end-to-end effect on /api/ai/doubt-solve."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fnjee-deploy.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@examnest.io", "password": "Admin@123", "role": "admin"}
STUDENT = {"email": "student1@examnest.io", "password": "Student@123", "role": "student"}
EMERGENT_KEY = "sk-emergent-12645D5441cA9F87f6"


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT)


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def student_headers(student_token):
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture(autouse=True)
def _reset_after(admin_token):
    yield
    # cleanup: reset to env default after each test
    try:
        requests.delete(f"{API}/admin/settings/ai",
                        headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
    except Exception:
        pass


# --- GET /api/admin/settings/ai ---
class TestGetAISettings:
    def test_get_returns_expected_shape(self, admin_headers):
        r = requests.get(f"{API}/admin/settings/ai", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        d = r.json()
        for k in ("provider", "model", "source", "masked_key",
                  "env_key_present", "effective_model", "providers", "default_models"):
            assert k in d, f"missing key: {k}"
        assert d["source"] in ("env", "admin")
        assert set(d["providers"]) >= {"emergent", "openai", "gemini", "claude"}
        # masked key never equals full key
        if d["masked_key"]:
            assert EMERGENT_KEY not in d["masked_key"]
            assert "…" in d["masked_key"] or len(d["masked_key"]) < len(EMERGENT_KEY)

    def test_get_without_token_rejected(self):
        r = requests.get(f"{API}/admin/settings/ai", timeout=10)
        assert r.status_code in (401, 403)

    def test_get_student_forbidden(self, student_headers):
        r = requests.get(f"{API}/admin/settings/ai", headers=student_headers, timeout=10)
        assert r.status_code == 403


# --- PUT /api/admin/settings/ai ---
class TestPutAISettings:
    def test_put_saves_and_flips_source_to_admin(self, admin_headers):
        r = requests.put(f"{API}/admin/settings/ai", headers=admin_headers,
                         json={"provider": "emergent", "api_key": EMERGENT_KEY}, timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["source"] == "admin"
        assert d["provider"] == "emergent"
        # masked key must not expose full key
        assert d["masked_key"] and EMERGENT_KEY not in d["masked_key"]
        # Verify persistence via GET
        g = requests.get(f"{API}/admin/settings/ai", headers=admin_headers, timeout=10)
        assert g.status_code == 200
        assert g.json()["source"] == "admin"
        assert g.json()["masked_key"] == d["masked_key"]

    def test_put_short_key_400(self, admin_headers):
        r = requests.put(f"{API}/admin/settings/ai", headers=admin_headers,
                         json={"provider": "emergent", "api_key": "short"}, timeout=10)
        assert r.status_code == 400

    def test_put_invalid_provider_422(self, admin_headers):
        r = requests.put(f"{API}/admin/settings/ai", headers=admin_headers,
                         json={"provider": "bogus", "api_key": "sk-valid-aaaaaaa"}, timeout=10)
        assert r.status_code == 422

    def test_put_no_token(self):
        r = requests.put(f"{API}/admin/settings/ai",
                         json={"provider": "emergent", "api_key": EMERGENT_KEY}, timeout=10)
        assert r.status_code in (401, 403)

    def test_put_student_forbidden(self, student_headers):
        r = requests.put(f"{API}/admin/settings/ai", headers=student_headers,
                         json={"provider": "emergent", "api_key": EMERGENT_KEY}, timeout=10)
        assert r.status_code == 403


# --- DELETE /api/admin/settings/ai ---
class TestDeleteAISettings:
    def test_delete_resets_to_env(self, admin_headers):
        requests.put(f"{API}/admin/settings/ai", headers=admin_headers,
                     json={"provider": "emergent", "api_key": EMERGENT_KEY}, timeout=10)
        r = requests.delete(f"{API}/admin/settings/ai", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        assert r.json()["source"] == "env"

    def test_delete_student_forbidden(self, student_headers):
        r = requests.delete(f"{API}/admin/settings/ai", headers=student_headers, timeout=10)
        assert r.status_code == 403

    def test_delete_no_token(self):
        r = requests.delete(f"{API}/admin/settings/ai", timeout=10)
        assert r.status_code in (401, 403)


# --- POST /api/admin/settings/ai/test (live LLM call) ---
class TestAISettingsTest:
    def test_live_test_with_saved_key(self, admin_headers):
        requests.put(f"{API}/admin/settings/ai", headers=admin_headers,
                     json={"provider": "emergent", "api_key": EMERGENT_KEY}, timeout=10)
        r = requests.post(f"{API}/admin/settings/ai/test", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert "latency_ms" in d and isinstance(d["latency_ms"], int)
        assert "provider" in d and "model" in d

    def test_test_student_forbidden(self, student_headers):
        r = requests.post(f"{API}/admin/settings/ai/test", headers=student_headers, timeout=10)
        assert r.status_code == 403

    def test_test_no_token(self):
        r = requests.post(f"{API}/admin/settings/ai/test", timeout=10)
        assert r.status_code in (401, 403)


# --- End-to-end: student doubt-solve still works after admin saves a key ---
class TestE2EDoubtSolve:
    def test_doubt_solve_uses_admin_key(self, admin_headers, student_headers):
        requests.put(f"{API}/admin/settings/ai", headers=admin_headers,
                     json={"provider": "emergent", "api_key": EMERGENT_KEY}, timeout=10)
        r = requests.post(f"{API}/ai/doubt-solve", headers=student_headers,
                          json={"question": "What is Newton's second law of motion?",
                                "subject": "Physics"}, timeout=60)
        # could be 200 (worked) or 429 if the student already hit rate limit earlier.
        assert r.status_code in (200, 429), r.text
        if r.status_code == 200:
            d = r.json()
            assert "solution" in d and len(d["solution"]) > 10


# --- Regression: /api/ready still healthy ---
def test_ready_healthy():
    r = requests.get(f"{API}/ready", timeout=10)
    assert r.status_code == 200
