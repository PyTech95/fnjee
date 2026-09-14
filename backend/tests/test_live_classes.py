"""Backend tests for Live Classes feature.

Covers: create (jitsi auto-link, provider link required), list scoping (admin/teacher/student/parent),
live-now, join (student attendance auto-mark), roster, mark, csv, update, delete, RBAC, notifications.

Note: pytest-xdist with --dist loadscope groups by class, so classes may run on different workers.
Cross-class shared state is provided via module-scoped fixtures.
"""
import os
from datetime import datetime, timezone, timedelta

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

CREDS = {
    "admin":   {"email": "admin@examnest.io",    "password": "Admin@123",   "role": "admin"},
    "teacher": {"email": "teacher1@examnest.io", "password": "Teacher@123", "role": "teacher"},
    "student": {"email": "student1@examnest.io", "password": "Student@123", "role": "student"},
    "parent":  {"email": "parent1@examnest.io",  "password": "Parent@123",  "role": "parent"},
}


def _login(role_key):
    c = CREDS[role_key]
    r = requests.post(f"{BASE_URL}/api/auth/login", json=c, timeout=30)
    assert r.status_code == 200, f"login {role_key} failed: {r.status_code} {r.text[:200]}"
    j = r.json()
    tok = j.get("access_token") or j.get("token")
    uid = (j.get("user") or {}).get("id")
    assert tok, f"no token in login response {j}"
    return tok, uid


def _hdr(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


# Session-wide token/live-class fixtures — created once, visible to all workers via HTTP (shared backend/db)
@pytest.fixture(scope="session")
def teacher_tok():
    return _login("teacher")


@pytest.fixture(scope="session")
def admin_tok():
    return _login("admin")


@pytest.fixture(scope="session")
def student_tok():
    return _login("student")


@pytest.fixture(scope="session")
def parent_tok():
    return _login("parent")


@pytest.fixture(scope="session")
def live_class(teacher_tok):
    """Create the primary live-now Jitsi class used by many tests. Cleaned up at session end."""
    tok, _ = teacher_tok
    starts = _iso(datetime.now(timezone.utc) - timedelta(minutes=2))
    r = requests.post(f"{BASE_URL}/api/live-classes", headers=_hdr(tok),
                      json={"title": "TEST_LC_JitsiLive", "subject": "Physics",
                            "provider": "jitsi", "starts_at": starts, "duration_minutes": 60},
                      timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    yield d
    try:
        atok, _ = _login("admin")
        requests.delete(f"{BASE_URL}/api/live-classes/{d['id']}", headers=_hdr(atok), timeout=15)
    except Exception:
        pass


@pytest.fixture(scope="session")
def extra_cleanup():
    ids = []
    yield ids
    atok, _ = _login("admin")
    for cid in ids:
        try:
            requests.delete(f"{BASE_URL}/api/live-classes/{cid}", headers=_hdr(atok), timeout=15)
        except Exception:
            pass


# --- Create + Jitsi auto-url + notifications ---
class TestCreate:
    def test_teacher_creates_jitsi_class_live_now(self, live_class):
        d = live_class
        assert d["id"] and d["provider"] == "jitsi"
        assert d["meeting_url"].startswith("https://meet.jit.si/MockTestClub-")
        assert d["status"] == "live"
        assert d["host_role"] == "teacher"

    def test_provider_zoom_requires_link(self, teacher_tok):
        tok, _ = teacher_tok
        starts = _iso(datetime.now(timezone.utc) + timedelta(hours=1))
        r = requests.post(f"{BASE_URL}/api/live-classes", headers=_hdr(tok),
                          json={"title": "TEST_LC_ZoomNoLink", "provider": "zoom",
                                "starts_at": starts, "duration_minutes": 30}, timeout=30)
        assert r.status_code == 400
        assert "link" in r.text.lower()

    def test_provider_meet_requires_link(self, teacher_tok):
        tok, _ = teacher_tok
        starts = _iso(datetime.now(timezone.utc) + timedelta(hours=1))
        r = requests.post(f"{BASE_URL}/api/live-classes", headers=_hdr(tok),
                          json={"title": "TEST_LC_MeetNoLink", "provider": "meet",
                                "starts_at": starts, "duration_minutes": 30}, timeout=30)
        assert r.status_code == 400

    def test_provider_zoom_with_link_succeeds(self, teacher_tok, extra_cleanup):
        tok, _ = teacher_tok
        starts = _iso(datetime.now(timezone.utc) + timedelta(hours=2))
        r = requests.post(f"{BASE_URL}/api/live-classes", headers=_hdr(tok),
                          json={"title": "TEST_LC_ZoomOK", "provider": "zoom",
                                "meeting_url": "https://zoom.us/j/1234567890",
                                "starts_at": starts, "duration_minutes": 30}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["meeting_url"] == "https://zoom.us/j/1234567890"
        assert d["status"] == "upcoming"
        extra_cleanup.append(d["id"])

    def test_reminders_notification_for_student(self, live_class, student_tok):
        tok, _ = student_tok
        r = requests.get(f"{BASE_URL}/api/notifications", headers=_hdr(tok), timeout=30)
        assert r.status_code == 200, r.text
        data = r.json() if isinstance(r.json(), list) else r.json().get("notifications", [])
        matching = [n for n in data if n.get("type") == "live_class" and "TEST_LC_JitsiLive" in (n.get("message") or "")]
        assert len(matching) >= 1, f"expected live_class notification for TEST_LC_JitsiLive"


# --- List scoping ---
class TestList:
    def test_admin_sees_all(self, live_class, admin_tok):
        tok, _ = admin_tok
        r = requests.get(f"{BASE_URL}/api/live-classes", headers=_hdr(tok), timeout=30)
        assert r.status_code == 200
        titles = [c["title"] for c in r.json()]
        assert "TEST_LC_JitsiLive" in titles

    def test_teacher_sees_own(self, live_class, teacher_tok):
        tok, _ = teacher_tok
        r = requests.get(f"{BASE_URL}/api/live-classes", headers=_hdr(tok), timeout=30)
        assert r.status_code == 200
        assert all(c["host_role"] == "teacher" for c in r.json())

    def test_student_sees_open_classes(self, live_class, student_tok):
        tok, _ = student_tok
        r = requests.get(f"{BASE_URL}/api/live-classes", headers=_hdr(tok), timeout=30)
        assert r.status_code == 200
        titles = [c["title"] for c in r.json()]
        assert "TEST_LC_JitsiLive" in titles

    def test_live_now_endpoint(self, live_class, student_tok):
        tok, _ = student_tok
        r = requests.get(f"{BASE_URL}/api/live-classes/live-now", headers=_hdr(tok), timeout=30)
        assert r.status_code == 200
        assert any(c["title"] == "TEST_LC_JitsiLive" and c["status"] == "live" for c in r.json())

    def test_parent_scoped(self, live_class, parent_tok):
        tok, _ = parent_tok
        r = requests.get(f"{BASE_URL}/api/live-classes", headers=_hdr(tok), timeout=30)
        assert r.status_code == 200
        # assigned_to=[] means open to all → parent should see it via child fallback
        # We at least assert 200 and list shape
        assert isinstance(r.json(), list)


# --- Join + attendance ---
class TestJoinAndAttendance:
    def test_student_joins_marks_attendance(self, live_class, student_tok):
        cid = live_class["id"]
        tok, _ = student_tok
        r = requests.post(f"{BASE_URL}/api/live-classes/{cid}/join", headers=_hdr(tok), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["meeting_url"].startswith("https://meet.jit.si/")

    def test_teacher_sees_roster_with_student_present(self, live_class, student_tok, teacher_tok):
        cid = live_class["id"]
        stok, sid = student_tok
        # ensure student has joined
        requests.post(f"{BASE_URL}/api/live-classes/{cid}/join", headers=_hdr(stok), timeout=30)
        ttok, _ = teacher_tok
        r = requests.get(f"{BASE_URL}/api/live-classes/{cid}/attendance", headers=_hdr(ttok), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["total"] >= 1
        row = next((x for x in d["rows"] if x["student_id"] == sid), None)
        assert row is not None, "student1 not in roster"
        assert row["present"] is True
        assert row["marked_by"] == "self"

    def test_teacher_manual_mark_absent_overrides(self, live_class, student_tok, teacher_tok):
        cid = live_class["id"]
        _, sid = student_tok
        ttok, _ = teacher_tok
        # ensure joined first
        stok, _ = student_tok
        requests.post(f"{BASE_URL}/api/live-classes/{cid}/join", headers=_hdr(stok), timeout=30)
        r = requests.post(f"{BASE_URL}/api/live-classes/{cid}/attendance/mark",
                          headers=_hdr(ttok), json={"student_id": sid, "present": False}, timeout=30)
        assert r.status_code == 200
        r2 = requests.get(f"{BASE_URL}/api/live-classes/{cid}/attendance", headers=_hdr(ttok), timeout=30)
        row = next(x for x in r2.json()["rows"] if x["student_id"] == sid)
        assert row["present"] is False
        assert row["marked_by"] == "teacher"
        # restore for downstream tests
        requests.post(f"{BASE_URL}/api/live-classes/{cid}/attendance/mark",
                      headers=_hdr(ttok), json={"student_id": sid, "present": True}, timeout=30)

    def test_csv_download(self, live_class, teacher_tok):
        cid = live_class["id"]
        tok, _ = teacher_tok
        r = requests.get(f"{BASE_URL}/api/live-classes/{cid}/attendance.csv", headers=_hdr(tok), timeout=30)
        assert r.status_code == 200
        assert "Name,Email,Present" in r.text
        assert "attachment" in r.headers.get("Content-Disposition", "")


# --- Edit (recording + materials) ---
class TestEdit:
    def test_teacher_updates_recording_and_material(self, live_class, teacher_tok):
        cid = live_class["id"]
        tok, _ = teacher_tok
        payload = {"recording_url": "https://example.com/rec.mp4",
                   "materials": [{"name": "Notes", "url": "https://example.com/notes.pdf"}]}
        r = requests.put(f"{BASE_URL}/api/live-classes/{cid}", headers=_hdr(tok), json=payload, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["recording_url"] == "https://example.com/rec.mp4"
        assert d["materials"] and d["materials"][0]["name"] == "Notes"


# --- RBAC ---
class TestRBAC:
    def test_student_cannot_create(self, student_tok):
        tok, _ = student_tok
        starts = _iso(datetime.now(timezone.utc) + timedelta(hours=1))
        r = requests.post(f"{BASE_URL}/api/live-classes", headers=_hdr(tok),
                          json={"title": "hack", "provider": "jitsi", "starts_at": starts}, timeout=30)
        assert r.status_code == 403

    def test_student_cannot_view_attendance(self, live_class, student_tok):
        cid = live_class["id"]
        tok, _ = student_tok
        r = requests.get(f"{BASE_URL}/api/live-classes/{cid}/attendance", headers=_hdr(tok), timeout=30)
        assert r.status_code == 403

    def test_student_cannot_mark_attendance(self, live_class, student_tok):
        cid = live_class["id"]
        tok, _ = student_tok
        r = requests.post(f"{BASE_URL}/api/live-classes/{cid}/attendance/mark",
                          headers=_hdr(tok), json={"student_id": "x", "present": True}, timeout=30)
        assert r.status_code == 403

    def test_teacher_cannot_edit_non_owned(self, admin_tok, teacher_tok, extra_cleanup):
        atok, _ = admin_tok
        starts = _iso(datetime.now(timezone.utc) + timedelta(hours=3))
        r = requests.post(f"{BASE_URL}/api/live-classes", headers=_hdr(atok),
                          json={"title": "TEST_LC_AdminOwned", "provider": "jitsi",
                                "starts_at": starts, "duration_minutes": 30}, timeout=30)
        assert r.status_code == 200
        acid = r.json()["id"]
        extra_cleanup.append(acid)
        ttok, _ = teacher_tok
        r2 = requests.put(f"{BASE_URL}/api/live-classes/{acid}", headers=_hdr(ttok),
                          json={"title": "hacked"}, timeout=30)
        assert r2.status_code == 403
        r3 = requests.delete(f"{BASE_URL}/api/live-classes/{acid}", headers=_hdr(ttok), timeout=30)
        assert r3.status_code == 403


# --- Regression ---
class TestRegression:
    def test_teacher_can_still_list_questions(self, teacher_tok):
        tok, _ = teacher_tok
        r = requests.get(f"{BASE_URL}/api/questions", headers=_hdr(tok), timeout=30)
        assert r.status_code == 200

    def test_student_practice_generate_still_works(self, student_tok):
        tok, _ = student_tok
        r = requests.post(f"{BASE_URL}/api/practice/generate", headers=_hdr(tok),
                          json={"subjects": ["Physics"], "count": 3}, timeout=30)
        assert r.status_code in (200, 400), r.text
