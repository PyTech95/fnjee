"""Tests for the 4 new features + regression:
  1. Live leaderboard (overall + per-test)
  2. Question difficulty heatmap (admin only)
  3. Admin error tracking (list/clear + admin-only)
  4. Distributed MongoDB-backed rate limiting (login 10/min per IP)
  5. Regression: submit still works and answer key still hidden pre-submit
"""
import os, time, uuid
import pytest, requests

_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not _URL:
    # fall back to frontend .env
    try:
        with open("/app/frontend/.env") as _f:
            for _l in _f:
                if _l.startswith("REACT_APP_BACKEND_URL="):
                    _URL = _l.split("=", 1)[1].strip()
                    break
    except Exception:
        pass
BASE = _URL.rstrip("/") + "/api"


def _login(email, password, role):
    r = requests.post(f"{BASE}/auth/login",
                      json={"email": email, "password": password, "role": role})
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login("admin@examnest.io", "Admin@123", "admin")


@pytest.fixture(scope="module")
def student_token():
    return _login("student1@examnest.io", "Student@123", "student")


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------- Live leaderboard ----------
class TestLeaderboard:
    def test_overall_leaderboard(self, student_token):
        r = requests.get(f"{BASE}/leaderboard/live", headers=_h(student_token))
        assert r.status_code == 200
        data = r.json()
        assert data["kind"] == "coins"
        assert "updated_at" in data and "you" in data
        assert isinstance(data["rows"], list)
        if data["rows"]:
            row = data["rows"][0]
            assert row["rank"] == 1
            assert "user" in row and "score" in row
            # rows sorted by score desc
            scores = [r_["score"] for r_ in data["rows"]]
            assert scores == sorted(scores, reverse=True)

    def test_per_test_leaderboard(self, student_token):
        # find any test id
        tests = requests.get(f"{BASE}/tests", headers=_h(student_token)).json()
        assert isinstance(tests, list) and tests
        tid = tests[0]["id"]
        r = requests.get(f"{BASE}/leaderboard/live", params={"test_id": tid},
                         headers=_h(student_token))
        assert r.status_code == 200
        d = r.json()
        assert d["kind"] == "test"
        assert isinstance(d["rows"], list)

    def test_requires_auth(self):
        r = requests.get(f"{BASE}/leaderboard/live")
        assert r.status_code == 401


# ---------- Question heatmap ----------
class TestHeatmap:
    def test_heatmap_admin(self, admin_token):
        r = requests.get(f"{BASE}/analytics/question-heatmap", headers=_h(admin_token))
        assert r.status_code == 200
        d = r.json()
        assert set(["subjects", "cells", "total_questions"]).issubset(d.keys())
        assert d["total_questions"] == len(d["cells"])
        if d["cells"]:
            c = d["cells"][0]
            for k in ["question_id", "accuracy", "seen", "correct", "wrong",
                      "observed_difficulty", "tagged_difficulty", "subject"]:
                assert k in c, f"missing {k} in cell"
            assert 0 <= c["accuracy"] <= 100
            assert c["observed_difficulty"] in {"easy", "medium", "hard", "unknown"}

    def test_heatmap_forbidden_for_student(self, student_token):
        r = requests.get(f"{BASE}/analytics/question-heatmap", headers=_h(student_token))
        assert r.status_code == 403

    def test_heatmap_subject_filter(self, admin_token):
        d = requests.get(f"{BASE}/analytics/question-heatmap",
                         headers=_h(admin_token)).json()
        if not d["subjects"]:
            pytest.skip("no data yet")
        subj = d["subjects"][0]
        r = requests.get(f"{BASE}/analytics/question-heatmap",
                         params={"subject": subj}, headers=_h(admin_token))
        assert r.status_code == 200
        for c in r.json()["cells"]:
            assert c["subject"] == subj


# ---------- Error tracking ----------
class TestErrorTracking:
    def test_list_admin_only(self, admin_token, student_token):
        r = requests.get(f"{BASE}/admin/errors", headers=_h(admin_token))
        assert r.status_code == 200
        d = r.json()
        for k in ["total", "last_24h", "errors"]:
            assert k in d
        assert isinstance(d["errors"], list)

        r2 = requests.get(f"{BASE}/admin/errors", headers=_h(student_token))
        assert r2.status_code == 403

    def test_clear_errors(self, admin_token):
        r = requests.post(f"{BASE}/admin/errors/clear", headers=_h(admin_token))
        assert r.status_code == 200
        assert "cleared" in r.json()
        # verify empty after clear
        d = requests.get(f"{BASE}/admin/errors", headers=_h(admin_token)).json()
        assert d["total"] == 0


# ---------- Rate limiting ----------
class TestRateLimit:
    def test_login_rate_limit_429(self):
        """11+ rapid logins/min per IP should get 429."""
        got_429 = False
        # send 15 rapid bad-password attempts (bad password still counts against limit)
        for i in range(15):
            r = requests.post(f"{BASE}/auth/login",
                              json={"email": f"nobody{i}@x.com",
                                    "password": "x", "role": "student"})
            if r.status_code == 429:
                got_429 = True
                break
        assert got_429, "expected HTTP 429 after >10 rapid logins/min"
        # wait to reset window for other tests
        time.sleep(2)


# ---------- Regression ----------
class TestRegression:
    def test_answer_key_hidden_pre_submit(self, student_token):
        tests = requests.get(f"{BASE}/tests", headers=_h(student_token)).json()
        tid = tests[0]["id"]
        r = requests.get(f"{BASE}/tests/{tid}", params={"include_questions": "true"},
                         headers=_h(student_token))
        assert r.status_code == 200
        for q in r.json().get("questions", []):
            assert "correct" not in q, "answer key leaked pre-submit!"

    def test_submit_flow(self, student_token):
        tests = requests.get(f"{BASE}/tests", headers=_h(student_token)).json()
        tid = tests[0]["id"]
        start = requests.post(f"{BASE}/attempts/start", json={"test_id": tid},
                              headers=_h(student_token))
        assert start.status_code == 200, start.text
        aid = start.json()["id"]
        # answer nothing / defaults, just submit
        sub = requests.post(f"{BASE}/attempts/submit",
                            json={"attempt_id": aid, "answers": []},
                            headers=_h(student_token))
        assert sub.status_code == 200, sub.text
        body = sub.json()
        assert "score" in body
