"""Backend tests for Peer Duel, Wrong-only Retest, Podcasts, Parent Digest."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://exam-builder-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


def _login(email, password, role):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password, "role": role}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def student1_token():
    return _login("student1@examnest.io", "Student@123", "student")


@pytest.fixture(scope="module")
def student2_token():
    return _login("student2@examnest.io", "Student@123", "student")


@pytest.fixture(scope="module")
def parent1_token():
    return _login("parent1@examnest.io", "Parent@123", "parent")


@pytest.fixture(scope="module")
def student1_attempt(student1_token):
    """A submitted attempt with at least one wrong answer."""
    h = {"Authorization": f"Bearer {student1_token}"}
    r = requests.get(f"{API}/attempts", headers=h, timeout=30)
    assert r.status_code == 200
    submitted = [a for a in r.json() if a.get("status") == "submitted"]
    assert submitted, "no submitted attempts for student1"
    # prefer one with wrong answers
    for a in submitted:
        detail = a.get("detailed") or []
        if any(d.get("result") == "wrong" for d in detail):
            return a
    return submitted[0]


# ---------------- Podcasts ----------------
class TestPodcasts:
    def test_chapters_list(self, student1_token):
        h = {"Authorization": f"Bearer {student1_token}"}
        r = requests.get(f"{API}/podcasts/chapters", headers=h, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0
        first = data[0]
        assert "subject" in first and "chapter" in first and "questions" in first

    def test_podcast_script(self, student1_token):
        h = {"Authorization": f"Bearer {student1_token}"}
        r = requests.post(f"{API}/podcasts/script", headers=h,
                          json={"subject": "Physics", "chapter": "Kinematics"}, timeout=60)
        assert r.status_code == 200
        data = r.json()
        assert "script" in data and isinstance(data["script"], str) and len(data["script"]) > 50
        assert "used_ai" in data


# ---------------- Wrong Retest ----------------
class TestWrongRetest:
    def test_creates_wrong_only_test(self, student1_token, student1_attempt):
        h = {"Authorization": f"Bearer {student1_token}"}
        aid = student1_attempt["id"]
        r = requests.post(f"{API}/attempts/{aid}/wrong-retest", headers=h, timeout=30)
        # Could be 400 if attempt has no wrong. Assert either.
        if r.status_code == 400:
            pytest.skip("selected attempt has no wrong answers")
        assert r.status_code == 200, r.text
        t = r.json()
        assert "id" in t
        assert t["title"].startswith("Wrong-only drill ·")
        assert t.get("exam_type") == "wrong_retest"
        assert isinstance(t.get("question_ids"), list) and len(t["question_ids"]) > 0

        # Verify persistence via /tests/{id}
        g = requests.get(f"{API}/tests/{t['id']}", headers=h, timeout=30)
        assert g.status_code == 200
        assert g.json()["title"] == t["title"]


# ---------------- Peer Duel ----------------
class TestPeerDuel:
    def test_create_and_fetch(self, student1_token, student1_attempt):
        h = {"Authorization": f"Bearer {student1_token}"}
        r = requests.post(f"{API}/duels", headers=h,
                          json={"test_id": student1_attempt["test_id"], "attempt_id": student1_attempt["id"]},
                          timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert len(d["code"]) == 6
        assert d["challenger_name"]
        assert "challenger_score" in d

        # public fetch (no auth)
        g = requests.get(f"{API}/duels/{d['code']}", timeout=30)
        assert g.status_code == 200
        assert g.json()["code"] == d["code"]
        # save for downstream
        TestPeerDuel._code = d["code"]

    def test_get_unknown_code_404(self):
        r = requests.get(f"{API}/duels/ZZZZZZ", timeout=30)
        assert r.status_code == 404


# ---------------- Parent Digest ----------------
class TestParentDigest:
    def test_digest_for_own_child(self, parent1_token):
        h = {"Authorization": f"Bearer {parent1_token}"}
        # get child id via parent profile
        me = requests.get(f"{API}/auth/me", headers=h, timeout=30)
        assert me.status_code == 200
        child_ids = me.json().get("child_ids") or []
        assert child_ids, "parent1 has no linked children"
        cid = child_ids[0]
        r = requests.get(f"{API}/parent/digest/{cid}", headers=h, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["child"]["id"] == cid
        assert "week_attempts" in d
        assert "week_avg_pct" in d
        assert "delta_pct" in d
        assert "message" in d and isinstance(d["message"], str)

    def test_digest_forbidden_for_other_child(self, parent1_token):
        h = {"Authorization": f"Bearer {parent1_token}"}
        r = requests.get(f"{API}/parent/digest/not-my-child-id", headers=h, timeout=30)
        assert r.status_code in (403, 404)
