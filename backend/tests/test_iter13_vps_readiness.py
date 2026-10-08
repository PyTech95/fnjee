"""Iteration 13 — VPS readiness regression + unit tests.

Covers:
  * Platform regression on /api/ready, admin integrations, cron auth
  * AI regression on /api/import/parse after emergentintegrations removal from ai_parser
  * email_utils.email_mode precedence + Resend/SMTP transport mocks + safety gate
  * scheduler.start job registration behind ENABLE_INTERNAL_SCHEDULER
  * Static VPS file sanity (docker-compose, Dockerfiles, Caddyfile, deploy/*.sh, requirements.vps.txt)
"""
import os
import sys
import re
import io
import asyncio
import pathlib
import subprocess
import pytest
import requests
import yaml

# Ensure /app/backend is importable for unit tests on email_utils / scheduler
sys.path.insert(0, "/app/backend")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or "https://fnjee-deploy.preview.emergentagent.com"
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@examnest.io", "password": "Admin@123", "role": "admin"}
STUDENT = {"email": "student1@examnest.io", "password": "Student@123", "role": "student"}


# ---------------- fixtures ----------------
def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT)


@pytest.fixture(scope="module")
def cron_secret():
    # read from backend .env
    for line in pathlib.Path("/app/backend/.env").read_text().splitlines():
        if line.startswith("WEBHOOK_CRON_SECRET"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


# ---------------- Platform regression ----------------
class TestPlatformRegression:
    def test_ready(self):
        r = requests.get(f"{API}/ready", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") == "ready"
        assert d.get("db") == "up"

    def test_admin_integrations(self, admin_token):
        r = requests.get(f"{API}/admin/system/integrations",
                         headers={"Authorization": f"Bearer {admin_token}"}, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ai"]["mode"] == "emergent", d
        assert d["email"]["mode"] == "emergent", d
        # Scheduler must be OFF on platform (no ENABLE_INTERNAL_SCHEDULER)
        assert d["scheduler"]["internal"] is False, d

    def test_student_integrations_forbidden(self, student_token):
        r = requests.get(f"{API}/admin/system/integrations",
                         headers={"Authorization": f"Bearer {student_token}"}, timeout=15)
        assert r.status_code == 403, r.text

    def test_cron_without_secret_401(self):
        r = requests.post(f"{API}/cron/weekly-digest", timeout=15)
        assert r.status_code == 401
        r = requests.post(f"{API}/cron/study-reminder", timeout=15)
        assert r.status_code == 401

    def test_cron_with_secret_accepted(self, cron_secret):
        assert cron_secret
        h = {"Authorization": f"Bearer {cron_secret}"}
        r = requests.post(f"{API}/cron/weekly-digest", headers=h, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("ok") is True
        r = requests.post(f"{API}/cron/study-reminder", headers=h, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("ok") is True


# ---------------- AI regression on /api/import/parse ----------------
class TestAIImportParse:
    def test_import_parse_two_mcqs(self, admin_token):
        raw = ("1. What is 2+2? (A) 3 (B) 4 (C) 5 (D) 6\n"
               "2. Capital of India? (A) Delhi (B) Mumbai (C) Pune (D) Goa")
        r = requests.post(
            f"{API}/import/parse",
            data={"raw_text": raw, "use_ai": "true", "subject_default": "Physics", "import_mode": "extract"},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        parsed = d.get("parsed") or d.get("questions") or []
        assert isinstance(parsed, list) and len(parsed) >= 1, f"no questions returned: {d}"

    def test_student_doubt_solve(self, student_token):
        r = requests.post(
            f"{API}/ai/doubt-solve",
            json={"question": "What is 2+2?"},
            headers={"Authorization": f"Bearer {student_token}"},
            timeout=90,
        )
        # endpoint may be /api/ai/doubt or /api/doubt-solve — try alternates if 404
        if r.status_code == 404:
            r = requests.post(
                f"{API}/doubt-solve",
                json={"question": "What is 2+2?"},
                headers={"Authorization": f"Bearer {student_token}"},
                timeout=90,
            )
        assert r.status_code == 200, r.text
        body = r.json()
        txt = (body.get("answer") or body.get("solution") or body.get("text") or str(body)).strip()
        assert len(txt) > 2


# ---------------- email_utils unit tests ----------------
class TestEmailUtils:
    def test_email_mode_precedence(self, monkeypatch):
        import email_utils as eu
        # resend wins
        monkeypatch.setenv("RESEND_API_KEY", "re_x")
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setattr(eu, "EMAIL_KEY", "ek")
        assert eu.email_mode() == "resend"
        # smtp next
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        assert eu.email_mode() == "smtp"
        # emergent next
        monkeypatch.delenv("SMTP_HOST", raising=False)
        assert eu.email_mode() == "emergent"
        # disabled
        monkeypatch.setattr(eu, "EMAIL_KEY", "")
        assert eu.email_mode() == "disabled"

    def test_resend_path_posts_correct_payload(self, monkeypatch):
        import email_utils as eu
        import httpx

        monkeypatch.setenv("RESEND_API_KEY", "re_test_abc")
        monkeypatch.setenv("EMAIL_FROM_ADDRESS", "noreply@fnjee.com")
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.setattr(eu, "EMAIL_KEY", "")  # ensure precedence picks resend

        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["auth"] = request.headers.get("authorization")
            import json
            captured["body"] = json.loads(request.content.decode())
            return httpx.Response(200, json={"id": "em_123"})

        transport = httpx.MockTransport(handler)
        orig = httpx.AsyncClient

        def fake_client(*args, **kwargs):
            kwargs["transport"] = transport
            return orig(*args, **kwargs)

        monkeypatch.setattr(eu.httpx, "AsyncClient", fake_client)

        rid = asyncio.get_event_loop().run_until_complete(
            eu.send_email(to="user@real.com", subject="Hi", html="<p>Hello</p>")
        )
        assert rid == "em_123"
        assert captured["url"] == "https://api.resend.com/emails"
        assert captured["auth"] == "Bearer re_test_abc"
        assert captured["body"]["from"] == "FNJEE.com <noreply@fnjee.com>"
        assert captured["body"]["to"] == ["user@real.com"]
        assert captured["body"]["subject"] == "Hi"

    def test_smtp_path_builds_message(self, monkeypatch):
        import email_utils as eu
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("EMAIL_FROM_ADDRESS", "noreply@fnjee.com")
        monkeypatch.setattr(eu, "EMAIL_KEY", "")

        captured = {}

        async def fake_send(msg, **kwargs):
            captured["from"] = msg["From"]
            captured["to"] = msg["To"]
            captured["subject"] = msg["Subject"]
            captured["hostname"] = kwargs.get("hostname")
            captured["port"] = kwargs.get("port")
            return None

        import aiosmtplib
        monkeypatch.setattr(aiosmtplib, "send", fake_send)
        asyncio.get_event_loop().run_until_complete(
            eu.send_email(to="user@real.com", subject="Hello", html="<p>hi</p>")
        )
        assert "FNJEE.com" in captured["from"]
        assert "noreply@fnjee.com" in captured["from"]
        assert captured["to"] == "user@real.com"
        assert captured["subject"] == "Hello"
        assert captured["hostname"] == "smtp.example.com"
        assert captured["port"] == 587

    def test_examnest_recipient_skipped(self, monkeypatch):
        import email_utils as eu
        monkeypatch.setenv("RESEND_API_KEY", "re_x")
        monkeypatch.setenv("EMAIL_FROM_ADDRESS", "x@fnjee.com")
        called = {"n": 0}

        async def fake_resend(*a, **kw):
            called["n"] += 1
            return "nope"

        monkeypatch.setattr(eu, "_send_resend", fake_resend)
        eu._SENDERS["resend"] = fake_resend
        res = asyncio.get_event_loop().run_until_complete(
            eu.send_email(to="demo@examnest.io", subject="x", html="<p>x</p>")
        )
        assert res is None
        assert called["n"] == 0

    def test_assert_safe_email_rejects_form(self):
        import email_utils as eu
        with pytest.raises(ValueError):
            eu._assert_safe_email("Subj", "<form><input name='x'></form>")


# ---------------- scheduler unit tests ----------------
class TestScheduler:
    def test_disabled_by_default(self, monkeypatch):
        import scheduler
        monkeypatch.delenv("ENABLE_INTERNAL_SCHEDULER", raising=False)

        async def noop():
            pass

        assert scheduler.start(noop, noop) is False

    @pytest.mark.asyncio
    async def test_registers_jobs_when_enabled(self, monkeypatch):
        import importlib, scheduler
        importlib.reload(scheduler)
        monkeypatch.setenv("ENABLE_INTERNAL_SCHEDULER", "true")

        async def noop():
            pass

        try:
            ok = scheduler.start(noop, noop)
            assert ok is True
            ids = {j["id"] for j in scheduler.jobs()}
            assert "weekly-digest" in ids
            assert "study-reminder" in ids
            from apscheduler.triggers.cron import CronTrigger
            jobs = {j.id: j for j in scheduler._sched.get_jobs()}
            wd = jobs["weekly-digest"]
            assert isinstance(wd.trigger, CronTrigger)
            fields = {f.name: str(f) for f in wd.trigger.fields}
            assert fields.get("day_of_week") in ("mon", "0")
            assert fields.get("hour") == "8"
            assert fields.get("minute") == "0"
            sr = jobs["study-reminder"]
            fields2 = {f.name: str(f) for f in sr.trigger.fields}
            assert fields2.get("minute") == "30"
        finally:
            scheduler.stop()


# ---------------- Static VPS file sanity ----------------
class TestVPSFiles:
    def test_docker_compose(self):
        data = yaml.safe_load(pathlib.Path("/app/docker-compose.yml").read_text())
        services = data.get("services") or {}
        for s in ("mongo", "backend", "web", "backup"):
            assert s in services, f"missing service {s}"
        assert "ports" not in services["mongo"], "mongo must not expose ports"
        env = services["backend"].get("environment") or {}
        val = env.get("ENABLE_INTERNAL_SCHEDULER")
        assert str(val).lower() in ("true", "1", "yes"), f"ENABLE_INTERNAL_SCHEDULER={val}"

    def test_backend_dockerfile(self):
        txt = pathlib.Path("/app/backend/Dockerfile").read_text()
        assert "requirements.vps.txt" in txt

    def test_requirements_vps_clean(self):
        txt = pathlib.Path("/app/backend/requirements.vps.txt").read_text().lower()
        assert "emergentintegrations" not in txt
        assert "litellm" not in txt

    def test_ai_parser_no_emergentintegrations(self):
        txt = pathlib.Path("/app/backend/ai_parser.py").read_text()
        assert "emergentintegrations" not in txt
        assert "litellm" not in txt

    def test_frontend_dockerfile_requires_site_url(self):
        txt = pathlib.Path("/app/frontend/Dockerfile").read_text()
        assert "SITE_URL" in txt
        assert re.search(r'test -n\s+"\$SITE_URL"', txt)

    def test_caddyfile_proxies_api(self):
        txt = pathlib.Path("/app/frontend/Caddyfile").read_text()
        assert "handle /api/*" in txt
        assert "reverse_proxy backend:8001" in txt

    def test_deploy_shell_scripts_syntax(self):
        for p in pathlib.Path("/app/deploy").glob("*.sh"):
            rc = subprocess.run(["sh", "-n", str(p)]).returncode
            assert rc == 0, f"sh -n failed on {p}"
