"""Iteration 3 tests:
  (1) App-side 413 verification — /api/import/start accepts 1/5/12/25 MB uploads
  (2) Regression — DOCX & solutions-PDF import via async job
  (3) Live progress object on GET /api/import/jobs/{id}
  (4) /api/questions/bulk-update
  (5) /api/questions/bulk-delete
"""
import os, time, pytest, requests
from pathlib import Path


def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    env = Path("/app/frontend/.env")
    for line in env.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not set")


BASE_URL = _load_backend_url()
ADMIN = {"email": "admin@examnest.io", "password": "Admin@123", "role": "admin"}
SAMPLE_PDF = "/app/tests/sample_imports/Hydrocarbons_Solutions.pdf"
SAMPLE_DOCX = "/app/tests/sample_imports/Hydrocarbons_Questions.docx"


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok
    return {"Authorization": f"Bearer {tok}"}


def _make_fake_pdf(size_bytes: int) -> bytes:
    """Minimal valid PDF header + zero-padding to desired size. The parser may fail to
    extract anything from this content, but POST /import/start should still return 200
    quickly because it only queues a background job. This test is strictly about proving
    the app imposes no small upload cap."""
    header = (b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
              b"1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n")
    pad = size_bytes - len(header)
    return header + (b"\x00" * max(pad, 0))


# ---------- (1) 413 verification ----------
@pytest.mark.parametrize("mb", [1, 5, 12, 25])
def test_import_start_accepts_large_upload(auth_headers, mb):
    size = mb * 1024 * 1024
    payload = _make_fake_pdf(size)
    files = {"file": (f"dummy_{mb}mb.pdf", payload, "application/pdf")}
    data = {"subject_default": "Physics", "use_ai": "false", "import_mode": "extract"}
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/api/import/start",
                      headers=auth_headers, files=files, data=data, timeout=120)
    elapsed = time.time() - t0
    assert r.status_code == 200, (
        f"{mb}MB upload returned {r.status_code} (expected 200). "
        f"Body: {r.text[:300]}  elapsed={elapsed:.1f}s"
    )
    body = r.json()
    assert body.get("status") == "processing", body
    assert body.get("job_id"), body
    print(f"[413-test] {mb}MB uploaded in {elapsed:.1f}s -> job {body['job_id']}")


# ---------- Shared helpers ----------
def _start_real(headers, path, subject="Chemistry", **extra):
    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f, "application/octet-stream")}
        data = {"subject_default": subject, "use_ai": "true", "import_mode": "extract"}
        data.update(extra)
        return requests.post(f"{BASE_URL}/api/import/start", headers=headers,
                             files=files, data=data, timeout=30)


def _poll(headers, job_id, timeout_s=200, interval=5, collect_progress=False):
    deadline = time.time() + timeout_s
    last = None
    prog_history = []
    while time.time() < deadline:
        r = requests.get(f"{BASE_URL}/api/import/jobs/{job_id}", headers=headers, timeout=30)
        assert r.status_code == 200, r.text
        last = r.json()
        if collect_progress:
            prog_history.append(last.get("progress") or {})
        if last.get("status") in ("done", "error"):
            break
        time.sleep(interval)
    return (last, prog_history) if collect_progress else last


# ---------- (2) DOCX regression ----------
def test_docx_import_end_to_end(auth_headers):
    r = _start_real(auth_headers, SAMPLE_DOCX, subject="Chemistry")
    assert r.status_code == 200, r.text
    job_id = r.json()["job_id"]
    final = _poll(auth_headers, job_id, timeout_s=200)
    assert final and final.get("status") == "done", f"DOCX job did not finish: {final}"
    result = final.get("result") or {}
    questions = result.get("questions") or []
    count = result.get("count") or len(questions)
    assert count >= 60, f"expected >=60 Qs, got {count}"
    # structural sanity on a sample
    sample = questions[0]
    assert sample.get("options"), "sample has no options"
    assert sample.get("correct"), "sample has no correct answer"


# ---------- (3) Solutions-PDF regression ----------
def test_solutions_pdf_import(auth_headers):
    r = _start_real(auth_headers, SAMPLE_PDF, subject="Chemistry")
    assert r.status_code == 200, r.text
    job_id = r.json()["job_id"]
    final = _poll(auth_headers, job_id, timeout_s=200)
    assert final and final.get("status") == "done", f"PDF job did not finish: {final}"
    result = final.get("result") or {}
    count = result.get("count") or len(result.get("questions") or [])
    assert count > 0, f"solutions PDF produced 0 questions: {result}"
    assert result.get("error") in (None, "", []), f"unexpected error: {result.get('error')}"


# ---------- (4) Live progress ----------
def test_live_progress_increases(auth_headers):
    r = _start_real(auth_headers, SAMPLE_DOCX, subject="Chemistry")
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    final, history = _poll(auth_headers, job_id, timeout_s=200, interval=4,
                           collect_progress=True)
    assert final and final.get("status") == "done", f"job failed: {final}"
    # distinct pct snapshots observed over time
    pcts = [int(p.get("pct") or 0) for p in history if isinstance(p, dict)]
    assert pcts, "no progress snapshots captured"
    assert max(pcts) == 100, f"final pct never reached 100: {pcts}"
    distinct = sorted(set(pcts))
    assert len(distinct) >= 2, f"pct did not advance over time: {pcts}"
    # messages are human-readable strings
    assert any(isinstance(p.get("msg"), str) and p.get("msg") for p in history), history
    print(f"[progress] observed pct values: {distinct}")


# ---------- (5) Bulk update ----------
def _create_question(headers, text_suffix: str) -> str:
    body = {
        "type": "mcq_single", "subject": "Chemistry", "chapter": "TMP",
        "difficulty": "easy", "marks": 4, "negative_marks": 1,
        "text": f"TEST_bulk Q {text_suffix}",
        "options": ["A", "B", "C", "D"], "correct": ["A"],
        "status": "approved",
    }
    r = requests.post(f"{BASE_URL}/api/questions", headers=headers, json=body, timeout=30)
    assert r.status_code in (200, 201), r.text
    q = r.json()
    qid = q.get("id") or q.get("_id") or q.get("question_id")
    assert qid, f"no id in create response: {q}"
    return qid


def test_bulk_update_questions(auth_headers):
    ids = [_create_question(auth_headers, f"upd-{i}") for i in range(2)]
    patch = {
        "ids": ids,
        "patch": {"chapter": "TEST_CHAP", "difficulty": "hard"},
        "add_tags": ["bulktest"],
    }
    r = requests.post(f"{BASE_URL}/api/questions/bulk-update",
                      headers=auth_headers, json=patch, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True, body
    assert (body.get("modified") or 0) >= 1, body

    # verify persistence via list endpoint (no GET /questions/{id} route)
    g = requests.get(f"{BASE_URL}/api/questions",
                     headers=auth_headers,
                     params={"chapter": "TEST_CHAP", "limit": 50}, timeout=20)
    assert g.status_code == 200, g.text
    docs = g.json()
    found = {d.get("id"): d for d in docs}
    for qid in ids:
        q = found.get(qid)
        assert q, f"updated question {qid} not found in list: ids={list(found)[:5]}"
        assert q.get("chapter") == "TEST_CHAP", q
        assert q.get("difficulty") == "hard", q
        assert "bulktest" in (q.get("tags") or []), q
    # cleanup
    requests.post(f"{BASE_URL}/api/questions/bulk-delete",
                  headers=auth_headers, json={"ids": ids}, timeout=20)


# ---------- (6) Bulk delete ----------
def test_bulk_delete_questions(auth_headers):
    ids = [_create_question(auth_headers, f"del-{i}") for i in range(2)]
    r = requests.post(f"{BASE_URL}/api/questions/bulk-delete",
                      headers=auth_headers, json={"ids": ids}, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True, body
    assert body.get("deleted") == 2, body
    # verify gone via list endpoint
    g = requests.get(f"{BASE_URL}/api/questions",
                     headers=auth_headers, params={"limit": 200}, timeout=20)
    assert g.status_code == 200
    remaining = {d.get("id") for d in g.json()}
    for qid in ids:
        assert qid not in remaining, f"question {qid} still present after bulk-delete"


# ---------- (7) Admin login requires role ----------
def test_admin_login_requires_role():
    bad = {"email": ADMIN["email"], "password": ADMIN["password"]}
    r = requests.post(f"{BASE_URL}/api/auth/login", json=bad, timeout=20)
    assert r.status_code in (400, 401, 403, 422), f"expected 4xx without role, got {r.status_code}: {r.text}"
    r2 = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=20)
    assert r2.status_code == 200, r2.text
