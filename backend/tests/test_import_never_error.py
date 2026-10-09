"""Never-error guarantee for /api/import/start + /api/import/jobs/{id}.

Rule under test: ANY file (valid, exotic, garbage, oversized) must:
  * get HTTP 200 on POST /api/import/start with {job_id,status:'processing'}
  * eventually reach status='done' on GET /api/import/jobs/{id} (NEVER 'error')
AI calls are legitimately slow (45-130s) so we poll up to 3 min per job.

Run with:  pytest -n 0 /app/backend/tests/test_import_never_error.py -v
"""
import os, time, pytest, requests
from pathlib import Path

def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v: return v.rstrip("/")
    env = Path("/app/frontend/.env")
    for line in env.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not set")

BASE_URL = _load_backend_url()
ADMIN = {"email": "admin@examnest.io", "password": "Admin@123", "role": "admin"}

SAMPLES = Path("/app/tests/sample_imports")
TXT  = SAMPLES / "plain_questions.txt"
PPTX = SAMPLES / "slides_questions.pptx"
PNG  = SAMPLES / "scan_questions.png"
DOCX = SAMPLES / "Hydrocarbons_Questions.docx"
PDF  = SAMPLES / "Hydrocarbons_Solutions.pdf"


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok
    return {"Authorization": f"Bearer {tok}"}


def _start(headers, filename, content, content_type="application/octet-stream", **extra):
    files = {"file": (filename, content, content_type)}
    data = {"subject_default": "Chemistry", "use_ai": "true", "import_mode": "extract"}
    data.update(extra)
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/api/import/start", headers=headers,
                      files=files, data=data, timeout=60)
    return r, time.time() - t0


def _poll(headers, job_id, timeout_s=200, interval=5):
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = requests.get(f"{BASE_URL}/api/import/jobs/{job_id}",
                         headers=headers, timeout=30)
        assert r.status_code == 200, r.text
        last = r.json()
        if last.get("status") in ("done", "error"):
            return last
        time.sleep(interval)
    return last


def _run_file(headers, path: Path, content_type="application/octet-stream",
              timeout_s=200, **extra):
    assert path.exists(), f"missing sample {path}"
    with open(path, "rb") as f:
        r, elapsed = _start(headers, path.name, f, content_type, **extra)
    assert r.status_code == 200, f"start returned {r.status_code}: {r.text[:300]}"
    body = r.json()
    assert body.get("status") == "processing"
    assert body.get("job_id")
    assert elapsed < 10, f"start was slow: {elapsed:.1f}s"
    final = _poll(headers, body["job_id"], timeout_s=timeout_s)
    assert final is not None, "job disappeared"
    assert final.get("status") == "done", \
        f"job must NEVER end in 'error', got {final.get('status')}: err={final.get('error')}"
    return final


# ------------- Never-error for each file type -------------

class TestNeverError:
    def test_txt_code_first_regex(self, auth_headers):
        final = _run_file(auth_headers, TXT, "text/plain", timeout_s=120)
        res = final.get("result") or {}
        assert res.get("count", 0) >= 2, f"TXT count<2: {res}"
        assert res.get("used_regex") is True, f"TXT should use regex path: {res}"

    def test_pptx_code_plus_ai(self, auth_headers):
        final = _run_file(
            auth_headers, PPTX,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            timeout_s=200,
        )
        res = final.get("result") or {}
        assert res.get("count", 0) >= 2, f"PPTX count<2: {res}"

    def test_image_ai_vision(self, auth_headers):
        final = _run_file(auth_headers, PNG, "image/png", timeout_s=200)
        res = final.get("result") or {}
        assert res.get("count", 0) >= 1, f"PNG count<1: {res}"
        assert res.get("used_ai") is True, f"PNG must use AI: {res}"
        assert res.get("used_regex") is False, f"PNG must not use regex: {res}"

    def test_docx_regex_thin_then_ai(self, auth_headers):
        final = _run_file(
            auth_headers, DOCX,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            timeout_s=240,
        )
        res = final.get("result") or {}
        assert res.get("count", 0) >= 60, f"DOCX count<60: {res.get('count')}"

    def test_solutions_pdf_adapt(self, auth_headers):
        final = _run_file(auth_headers, PDF, "application/pdf", timeout_s=240)
        res = final.get("result") or {}
        assert res.get("count", 0) > 0, f"Solutions PDF count=0: {res}"

    def test_garbage_binary_graceful(self, auth_headers):
        """Random bytes with .xyz extension — must NOT error."""
        garbage = os.urandom(2048)
        r, _ = _start(auth_headers, "weird.xyz", garbage, "application/octet-stream")
        assert r.status_code == 200, f"start on garbage returned {r.status_code}: {r.text[:300]}"
        job_id = r.json()["job_id"]
        final = _poll(auth_headers, job_id, timeout_s=180)
        assert final.get("status") == "done", f"garbage job must be 'done', got {final}"
        assert final.get("error") in (None, ""), f"job.error must be null, got {final.get('error')!r}"
        res = final.get("result") or {}
        assert res.get("count", 0) == 0
        errs = res.get("errors") or []
        joined = " ".join(errs).lower()
        # friendly message, no stack trace / 500
        assert errs, "expected at least one friendly note in result.errors"
        assert "traceback" not in joined
        assert "500" not in joined

    def test_large_file_not_413(self, auth_headers):
        """20MB file beginning with PDF header must return 200 (not 413/400)."""
        big = b"%PDF-1.4\n" + os.urandom(20 * 1024 * 1024)
        files = {"file": ("big_dummy.pdf", big, "application/pdf")}
        data = {"subject_default": "Chemistry", "use_ai": "false", "import_mode": "extract"}
        r = requests.post(f"{BASE_URL}/api/import/start",
                          headers=auth_headers, files=files, data=data, timeout=120)
        assert r.status_code == 200, f"20MB upload returned {r.status_code}: {r.text[:200]}"
        assert r.json().get("job_id")

    def test_admin_login_requires_role(self):
        """Login must require email+password+role (regression)."""
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": ADMIN["email"], "password": ADMIN["password"]},
                          timeout=15)
        assert r.status_code in (400, 401, 403, 422), \
            f"login without role should fail, got {r.status_code}"
        r2 = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=15)
        assert r2.status_code == 200
        assert r2.json().get("token") or r2.json().get("access_token")
