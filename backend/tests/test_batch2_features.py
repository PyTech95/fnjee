"""BATCH 2 tests: SEO/PWA static assets + Coach + Revision + Adaptive + Battles APIs."""
import os
import re
import time
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://hardened-quiz-app.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="session")
def student_token():
    # small delay to avoid login rate limit
    time.sleep(1)
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": "student2@examnest.io", "password": "Student@123", "role": "student"
    }, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture
def sauth(student_token):
    return {"Authorization": f"Bearer {student_token}"}


# ---- SEO / PWA static ----
class TestSEOPWA:
    def test_robots_txt(self):
        r = requests.get(f"{BASE}/robots.txt", timeout=15)
        assert r.status_code == 200
        assert "Sitemap" in r.text

    def test_sitemap_xml(self):
        r = requests.get(f"{BASE}/sitemap.xml", timeout=15)
        assert r.status_code == 200
        assert "<urlset" in r.text and "</urlset>" in r.text

    def test_manifest_json(self):
        r = requests.get(f"{BASE}/manifest.json", timeout=15)
        assert r.status_code == 200
        j = r.json()
        icons = j.get("icons", [])
        assert isinstance(icons, list) and len(icons) > 0
        srcs = [i.get("src", "") for i in icons]
        assert any("/icon-192.png" in s for s in srcs)
        purposes = " ".join(i.get("purpose", "") for i in icons)
        assert "maskable" in purposes
        assert isinstance(j.get("shortcuts", []), list) and len(j["shortcuts"]) > 0

    def test_icon_192(self):
        r = requests.get(f"{BASE}/icon-192.png", timeout=15)
        assert r.status_code == 200
        assert len(r.content) > 100

    def test_og_image(self):
        r = requests.get(f"{BASE}/og-image.jpg", timeout=15)
        assert r.status_code == 200
        assert len(r.content) > 100


# ---- Coach ----
class TestCoach:
    def test_coach_plan(self, sauth):
        r = requests.get(f"{BASE}/api/coach/plan", headers=sauth, timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        # should contain either weak items or empty flag
        assert isinstance(j, dict)


# ---- Reviews ----
class TestReviews:
    def test_reviews_stats(self, sauth):
        r = requests.get(f"{BASE}/api/reviews/stats", headers=sauth, timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        for k in ["due", "learning", "mastered", "total"]:
            assert k in j, f"missing key {k}"

    def test_reviews_due(self, sauth):
        r = requests.get(f"{BASE}/api/reviews/due", headers=sauth, timeout=30)
        assert r.status_code == 200
        # returns a list-like structure
        j = r.json()
        assert isinstance(j, (list, dict))


# ---- Adaptive ----
class TestAdaptive:
    def test_adaptive_full_loop(self, sauth):
        r = requests.post(f"{BASE}/api/adaptive/start", headers=sauth,
                          json={"subject": "Physics"}, timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        assert "session_id" in j
        sid = j["session_id"]
        q = j.get("question")
        assert q and "id" in q and "options" in q
        # answer up to 20 questions
        for _ in range(25):
            payload = {"session_id": sid, "question_id": q["id"], "answer": "A"}
            ar = requests.post(f"{BASE}/api/adaptive/answer", headers=sauth,
                               json=payload, timeout=30)
            assert ar.status_code == 200, ar.text
            aj = ar.json()
            if aj.get("done") or aj.get("summary"):
                assert "ability" in (aj.get("summary") or {}) or "ability" in aj
                return
            q = aj.get("next_question") or aj.get("question")
            assert q, f"no next question: {aj}"
        pytest.fail("Adaptive session did not terminate in 25 answers")


# ---- Battles ----
class TestBattles:
    def test_battle_flow(self, sauth):
        # create
        r = requests.post(f"{BASE}/api/battles/create", headers=sauth,
                          json={"subject": "Physics", "num_questions": 3}, timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        assert "id" in j
        bid = j["id"]
        code = j.get("code") or j.get("room_code")
        assert code and len(code) == 5

        # get state
        r = requests.get(f"{BASE}/api/battles/{bid}", headers=sauth, timeout=15)
        assert r.status_code == 200

        # start
        r = requests.post(f"{BASE}/api/battles/{bid}/start", headers=sauth, timeout=15)
        assert r.status_code == 200, r.text

        # poll state
        r = requests.get(f"{BASE}/api/battles/{bid}", headers=sauth, timeout=15)
        assert r.status_code == 200
        state = r.json()
        assert state.get("status") in ("active", "running", "in_progress", "started")

        # answer first question if available
        q = (state.get("current_question") or state.get("question")
             or (state.get("questions") or [{}])[0])
        if q and q.get("id"):
            ar = requests.post(f"{BASE}/api/battles/{bid}/answer", headers=sauth,
                               json={"question_id": q["id"], "answer": "A", "index": 0}, timeout=15)
            assert ar.status_code in (200, 400, 409), ar.text  # ok or timing

    def test_battle_join_invalid_code(self, sauth):
        r = requests.post(f"{BASE}/api/battles/join", headers=sauth,
                          json={"code": "ZZZZZ"}, timeout=15)
        assert r.status_code in (400, 404), r.text
