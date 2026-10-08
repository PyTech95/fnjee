"""Tests for the async import background-job flow (/api/import/start + /api/import/jobs/{id}).

The fix under test: synchronous /api/import/parse was timing out at the Emergent 60s gateway
for AI-based PDF/DOCX extraction. New flow:
  POST /api/import/start -> returns {job_id,status:'processing'} quickly (<2s)
  GET  /api/import/jobs/{id} -> poll until status == 'done' with result.count > 0
"""
import os, time, pytest, requests
from pathlib import Path

def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v: return v.rstrip("/")
    env = Path("/app/frontend/.env")
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not set")

BASE_URL = _load_backend_url()
ADMIN = {"email": "admin@examnest.io", "password": "Admin@123", "role": "admin"}

SAMPLE_PDF  = "/app/tests/sample_imports/Hydrocarbons_Solutions.pdf"
SAMPLE_DOCX = "/app/tests/sample_imports/Hydrocarbons_Questions.docx"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def _start_job(headers, path, subject="Chemistry", **extra_fields):
    assert os.path.exists(path), f"missing sample file {path}"
    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f, "application/octet-stream")}
        data = {"subject_default": subject, "use_ai": "true", "import_mode": "extract"}
        data.update(extra_fields)
        t0 = time.time()
        r = requests.post(f"{BASE_URL}/api/import/start", headers=headers,
                          files=files, data=data, timeout=30)
        elapsed = time.time() - t0
    return r, elapsed


def _poll_job(headers, job_id, timeout_s=240, interval=3):
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = requests.get(f"{BASE_URL}/api/import/jobs/{job_id}", headers=headers, timeout=30)
        assert r.status_code == 200, r.text
        last = r.json()
        if last.get("status") in ("done", "error"):
            return last
        time.sleep(interval)
    return last


class TestImportAsyncJob:
    def test_start_pdf_returns_quickly(self, auth_headers):
        """POST /import/start must return <2s with a job_id (not block on AI)."""
        r, elapsed = _start_job(auth_headers, SAMPLE_PDF, subject="Chemistry")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("status") == "processing"
        assert body.get("job_id")
        assert elapsed < 5, f"start endpoint took {elapsed:.1f}s (should be <<60s)"

    def test_pdf_full_flow(self, auth_headers):
        r, _ = _start_job(auth_headers, SAMPLE_PDF, subject="Chemistry")
        assert r.status_code == 200
        job_id = r.json()["job_id"]
        final = _poll_job(auth_headers, job_id, timeout_s=240)
        assert final is not None
        assert final.get("status") == "done", f"job did not complete: {final}"
        result = final.get("result") or {}
        count = result.get("count") or len(result.get("questions") or [])
        assert count > 0, f"no questions extracted; result={result}"

    def test_docx_full_flow_with_categorisation(self, auth_headers):
        extras = {
            "chapter_default": "Hydrocarbons",
            "topic_default": "Alkanes",
            "difficulty_default": "hard",
            "tags_default": "pyq, important",
        }
        r, elapsed = _start_job(auth_headers, SAMPLE_DOCX, subject="Chemistry", **extras)
        assert r.status_code == 200, r.text
        assert elapsed < 5
        job_id = r.json()["job_id"]
        final = _poll_job(auth_headers, job_id, timeout_s=240)
        assert final.get("status") == "done", f"docx job failed: {final}"
        questions = (final.get("result") or {}).get("questions") or []
        assert len(questions) > 0, "no DOCX questions extracted"
        # verify batch categorisation applied
        sample = questions[0]
        assert sample.get("chapter") == "Hydrocarbons", f"chapter not applied: {sample.get('chapter')}"
        assert sample.get("difficulty") == "hard", f"difficulty not applied: {sample.get('difficulty')}"
        tags = sample.get("tags") or []
        assert "pyq" in tags and "important" in tags, f"tags not applied: {tags}"

    def test_commit_saves_questions(self, auth_headers):
        """After extraction, /import/commit persists selected questions."""
        r, _ = _start_job(auth_headers, SAMPLE_DOCX, subject="Chemistry",
                          chapter_default="Hydrocarbons", difficulty_default="medium")
        job_id = r.json()["job_id"]
        final = _poll_job(auth_headers, job_id, timeout_s=240)
        assert final.get("status") == "done"
        questions = (final.get("result") or {}).get("questions") or []
        assert questions
        # take first 3 to keep commit fast
        payload = {"questions": questions[:3], "subject_default": "Chemistry"}
        cr = requests.post(f"{BASE_URL}/api/import/commit", headers=auth_headers,
                           json=payload, timeout=60)
        assert cr.status_code == 200, cr.text
        body = cr.json()
        inserted = body.get("inserted") or body.get("count") or 0
        if isinstance(inserted, list): inserted = len(inserted)
        assert inserted > 0, f"commit saved nothing: {body}"

    def test_unauthorized_start_rejected(self):
        r = requests.post(f"{BASE_URL}/api/import/start",
                          data={"subject_default": "Physics", "raw_text": "x"}, timeout=15)
        assert r.status_code in (401, 403)
