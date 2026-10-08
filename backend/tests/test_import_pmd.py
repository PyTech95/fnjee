"""Targeted tests for the PageMaker (.pmd) import bug fix + light import regression.

Covers:
- Real .pmd (60 MB OLE compound doc at /tmp/chembond.pmd) -> count > 0, used_ai=true
- Tiny random-bytes .pmd stub -> count == 0 AND non-empty errors[]
- Excel with 2 rows -> count == 2, used_ai=false
- Missing file/drive_url -> 400
- /api/import/commit still persists a subset
"""
import io
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback: read frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

ADMIN_EMAIL = "admin@examnest.io"
ADMIN_PASSWORD = "Admin@123"
PMD_PATH = "/tmp/chembond.pmd"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "role": "admin"},
                      timeout=30)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------- PageMaker real file ----------

def test_pmd_real_file_extracts_questions(auth_headers):
    assert os.path.exists(PMD_PATH), f"Missing {PMD_PATH}"
    with open(PMD_PATH, "rb") as f:
        files = {"file": ("3. Chemical Bonding.pmd", f, "application/octet-stream")}
        data = {"subject_default": "Chemistry"}
        t0 = time.time()
        r = requests.post(f"{BASE_URL}/api/import/parse",
                          headers=auth_headers, files=files, data=data,
                          timeout=180)
        elapsed = time.time() - t0
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:500]}"
    body = r.json()
    print(f"PMD parse elapsed={elapsed:.1f}s count={body.get('count')} used_ai={body.get('used_ai')} errors={body.get('errors')}")
    assert body["file_type"] == "pmd"
    assert body["used_ai"] is True
    assert body["count"] > 0, f"Expected count>0 but got {body['count']}; errors={body.get('errors')}"
    # sanity check structure
    q = body["questions"][0]
    assert "text" in q and q["text"]
    # performance sanity - allow up to 120s
    assert elapsed < 120, f"Parse took too long: {elapsed:.1f}s"


# ---------- PageMaker stub with random bytes ----------

def test_pmd_stub_gives_actionable_error(auth_headers):
    import random
    random.seed(1)
    stub = bytes(random.getrandbits(8) for _ in range(2048))
    files = {"file": ("tiny.pmd", io.BytesIO(stub), "application/octet-stream")}
    data = {"subject_default": "Physics"}
    r = requests.post(f"{BASE_URL}/api/import/parse",
                      headers=auth_headers, files=files, data=data, timeout=90)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:500]}"
    body = r.json()
    assert body["count"] == 0
    assert body["errors"], "Expected non-empty errors array"
    assert any(len(e) > 20 for e in body["errors"]), f"Expected actionable message, got {body['errors']}"


# ---------- Excel happy path ----------

def _make_xlsx_bytes():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Question Text", "Option A", "Option B", "Option C", "Option D", "Correct Answer", "Subject"])
    ws.append(["TEST_PMD What is 2+2?", "3", "4", "5", "6", "B", "Mathematics"])
    ws.append(["TEST_PMD Capital of France?", "London", "Paris", "Rome", "Berlin", "B", "GK"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_excel_two_rows_no_ai(auth_headers):
    xlsx = _make_xlsx_bytes()
    files = {"file": ("test.xlsx", io.BytesIO(xlsx),
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = requests.post(f"{BASE_URL}/api/import/parse",
                      headers=auth_headers, files=files, data={"subject_default": "Physics"},
                      timeout=60)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:500]}"
    body = r.json()
    assert body["count"] == 2, f"Expected 2 got {body['count']}, errors={body.get('errors')}"
    assert body["used_ai"] is False
    assert body["file_type"] == "xlsx"


# ---------- Missing file/drive ----------

def test_parse_requires_file_or_drive(auth_headers):
    r = requests.post(f"{BASE_URL}/api/import/parse", headers=auth_headers, data={}, timeout=30)
    assert r.status_code == 400, f"Expected 400 got {r.status_code}: {r.text[:200]}"


# ---------- Commit persists ----------

def test_commit_persists_subset(auth_headers):
    xlsx = _make_xlsx_bytes()
    files = {"file": ("test.xlsx", io.BytesIO(xlsx),
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    parse_r = requests.post(f"{BASE_URL}/api/import/parse",
                            headers=auth_headers, files=files, data={"subject_default": "Physics"},
                            timeout=60)
    assert parse_r.status_code == 200
    questions = parse_r.json()["questions"]
    # commit just first one
    commit_r = requests.post(f"{BASE_URL}/api/import/commit",
                             headers={**auth_headers, "Content-Type": "application/json"},
                             json={"questions": questions[:1]}, timeout=30)
    assert commit_r.status_code == 200
    assert commit_r.json()["inserted"] == 1
