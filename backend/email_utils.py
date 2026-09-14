"""Emergent-managed Resend email helper + result scorecard sender.

Guardrail gate copied verbatim from the Resend playbook — do not weaken it.
Emails are built from server-side templates only (never caller input).
"""
import os
import re
import ipaddress
import logging
import httpx
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Emergent managed email proxy. CONSTANT — never read from os.environ.
EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ.get("EMERGENT_EMAIL_KEY", "")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Abhyash Mantra")
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")

_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = ("reply with your password", "reply with the code", "send your password", "cvv",
             "send us your password", "enter your password below", "confirm your card number",
             "your full card number", "seed phrase", "recovery phrase", "verify your card",
             "social security number", "confirm your bank details")
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == s or host.endswith("." + s) for s in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.urls, self.anchors = set(), [], []
        self._href, self._text = None, []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [v for k, v in attrs if k.lower() in ("href", "src") and v]
        if tag.lower() == "a":
            self._href = dict((k.lower(), v) for k, v in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan(); scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email (G2)")
    body = f"{subject}\n{html}".lower()
    for p in _CRED_ASK:
        if p in body:
            raise ValueError(f"Email asks the recipient for credentials: {p!r} (G2)")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError(f"Email links/assets must be absolute https: {url!r} (G3)")
        host = urlparse(low).hostname or ""
        if not _host_ok(host) or urlparse(low).username is not None:
            raise ValueError(f"Shortened, numeric-host or credential-bearing URL: {url!r} (G3)")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for m in _HOSTISH.finditer(text):
            if not _same_site(m.group(1).lower(), real):
                raise ValueError(f"Anchor text {m.group(1)!r} != real link host {real!r} (G3)")


async def send_email(*, to: str, subject: str, html: str, reply_to: str | None = None) -> str | None:
    _assert_safe_email(subject, html)
    if not EMAIL_KEY:
        logger.warning("EMERGENT_EMAIL_KEY not set — skipping email send")
        return None
    payload = {"to": [to], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if reply_to or EMAIL_REPLY_TO:
        payload["contact_email"] = reply_to or EMAIL_REPLY_TO
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{EMAIL_BASE_URL}/api/v1/email/send",
            headers={"X-Email-Key": EMAIL_KEY},
            json=payload,
        )
    resp.raise_for_status()
    return resp.json().get("id")


def _result_html(user: dict, test: dict, attempt: dict, qmap: dict, rank: dict | None = None, topper: dict | None = None, retake_url: str | None = None, coach: dict | None = None) -> str:
    name = escape(str(user.get("name", "Student")))
    title = escape(str(test.get("title", "Test")))
    score = attempt.get("score", 0)
    total = attempt.get("total_marks", 0) or 0
    pct = round((score / total) * 100) if total else 0
    correct = attempt.get("correct", 0)
    wrong = attempt.get("wrong", 0)
    unatt = attempt.get("unattempted", 0)

    rank_html = ""
    if rank and rank.get("total"):
        rank_html = (
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:18px">'
            f'<tr><td style="background:#eef4fb;border:1px solid #d6e6f7;border-radius:12px;padding:14px 16px">'
            f'<div style="font-size:14px;color:#0f172a">🏆 You beat '
            f'<strong style="color:#0A66C2">{rank["percentile"]}%</strong> of aspirants — predicted percentile '
            f'<strong style="color:#0A66C2">{rank["percentile"]}</strong> '
            f'({rank.get("beat", 0)} of {rank["total"]} peers).</div></td></tr></table>'
        )

    topper_html = ""
    if topper and topper.get("top_score") is not None:
        top = topper["top_score"]; mine = attempt.get("score", 0)
        if mine >= top:
            line = "🥇 You are the <strong>class topper</strong> on this test!"
        else:
            diff = round(top - mine, 2)
            line = (f'Class topper scored <strong>{top}/{topper.get("total", 0)}</strong> — '
                    f'you are <strong>{diff}</strong> marks behind.')
        topper_html = (
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:18px">'
            f'<tr><td style="background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:14px 16px">'
            f'<div style="font-size:14px;color:#0f172a">🏫 {line}</div></td></tr></table>'
        )

    cta_html = ""
    if retake_url:
        cta_html = (
            f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:20px 0 4px"><tr>'
            f'<td style="border-radius:9999px;background:#0A66C2">'
            f'<a href="{retake_url}" style="display:inline-block;padding:12px 28px;color:#ffffff;'
            f'font-size:14px;font-weight:700;text-decoration:none">Retake &amp; beat the topper →</a>'
            f'</td></tr></table>'
        )

    coach_html = ""
    if coach:
        gaps = "".join(f'<li>{escape(str(g.get("topic","")))}: {escape(str(g.get("note","")))}</li>' for g in (coach.get("conceptual_gaps") or [])[:4])
        actions = "".join(f'<li>{escape(str(a))}</li>' for a in (coach.get("action_plan") or [])[:4])
        coach_html = (
            f'<div style="background:#f5f3ff;border:1px solid #ddd6fe;border-radius:12px;padding:16px;margin-bottom:18px">'
            f'<div style="font-size:14px;font-weight:800;color:#4338CA;margin-bottom:6px">🤖 AI Performance Coach</div>'
            f'<div style="font-size:14px;color:#0f172a;margin-bottom:10px">{escape(str(coach.get("overview","")))}</div>'
            + (f'<div style="font-size:12px;font-weight:700;color:#0f172a">Focus topics</div>'
               f'<ul style="font-size:13px;color:#475569;margin:4px 0 10px;padding-left:18px">{gaps}</ul>' if gaps else '')
            + (f'<div style="font-size:12px;font-weight:700;color:#0f172a">Do next</div>'
               f'<ul style="font-size:13px;color:#475569;margin:4px 0 0;padding-left:18px">{actions}</ul>' if actions else '')
            + '</div>'
        )

    rows = ""
    for i, d in enumerate(attempt.get("detailed", []), start=1):
        q = qmap.get(d.get("question_id"), {})
        qtext = escape(str(q.get("text", ""))[:140])
        res = d.get("result", "")
        color = {"correct": "#16a34a", "wrong": "#dc2626"}.get(res, "#64748b")
        ua = escape(", ".join([str(x) for x in (d.get("user_answer") or [])]) or "—")
        ca = escape(", ".join([str(x) for x in (d.get("correct") or [])]) or "—")
        marks = d.get("marks_awarded", 0)
        rows += (
            f'<tr>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;font-size:13px;vertical-align:top">Q{i}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;font-size:13px;vertical-align:top">{qtext}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;font-size:13px;vertical-align:top">{ua}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;font-size:13px;vertical-align:top">{ca}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;font-size:13px;font-weight:700;color:{color};vertical-align:top">'
            f'{"+" if marks > 0 else ""}{marks}</td>'
            f'</tr>'
        )

    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:#f4f6fb;padding:24px 0;font-family:Arial,Helvetica,sans-serif"><tr><td align="center">'
        f'<table role="presentation" width="640" cellpadding="0" cellspacing="0" '
        f'style="background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e5e9f2">'
        f'<tr><td style="background:#0A66C2;padding:24px 28px">'
        f'<div style="color:#ffffff;font-size:20px;font-weight:800">{escape(EMAIL_FROM_NAME)}</div>'
        f'<div style="color:#cfe0f5;font-size:13px;margin-top:2px">Your test result is ready</div></td></tr>'
        f'<tr><td style="padding:28px">'
        f'<p style="font-size:15px;color:#0f172a;margin:0 0 6px">Hi {name},</p>'
        f'<p style="font-size:14px;color:#475569;margin:0 0 18px">Here is your scorecard for '
        f'<strong>{title}</strong>.</p>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px">'
        f'<tr><td align="center" style="background:#0A66C2;border-radius:12px;padding:20px">'
        f'<div style="color:#ffffff;font-size:40px;font-weight:800;line-height:1">{score}<span style="font-size:18px;color:#cfe0f5"> / {total}</span></div>'
        f'<div style="color:#cfe0f5;font-size:13px;margin-top:4px">{pct}% overall</div></td></tr></table>'
        f'{rank_html}'
        f'{topper_html}'
        f'{coach_html}'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:22px"><tr>'
        f'<td align="center" style="padding:10px;background:#f0fdf4;border-radius:10px"><div style="font-size:20px;font-weight:800;color:#16a34a">{correct}</div><div style="font-size:12px;color:#64748b">Correct</div></td>'
        f'<td width="10"></td>'
        f'<td align="center" style="padding:10px;background:#fef2f2;border-radius:10px"><div style="font-size:20px;font-weight:800;color:#dc2626">{wrong}</div><div style="font-size:12px;color:#64748b">Wrong</div></td>'
        f'<td width="10"></td>'
        f'<td align="center" style="padding:10px;background:#f8fafc;border-radius:10px"><div style="font-size:20px;font-weight:800;color:#64748b">{unatt}</div><div style="font-size:12px;color:#64748b">Skipped</div></td>'
        f'</tr></table>'
        f'<div style="font-size:14px;font-weight:700;color:#0f172a;margin-bottom:8px">Question breakdown</div>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #eee;border-radius:8px">'
        f'<tr style="background:#f8fafc">'
        f'<td style="padding:8px;font-size:12px;font-weight:700;color:#64748b">#</td>'
        f'<td style="padding:8px;font-size:12px;font-weight:700;color:#64748b">Question</td>'
        f'<td style="padding:8px;font-size:12px;font-weight:700;color:#64748b">Your ans</td>'
        f'<td style="padding:8px;font-size:12px;font-weight:700;color:#64748b">Correct</td>'
        f'<td style="padding:8px;font-size:12px;font-weight:700;color:#64748b">Marks</td></tr>'
        f'{rows}</table>'
        f'{cta_html}'
        f'<p style="font-size:13px;color:#475569;margin:20px 0 0">Log in to your dashboard to review full '
        f'explanations and retake the test.</p>'
        f'<p style="font-size:12px;color:#94a3b8;margin:22px 0 0">Sent by {escape(EMAIL_FROM_NAME)}. '
        f'We never ask for your password or payment details by email.</p>'
        f'</td></tr></table></td></tr></table>'
    )


async def send_result_email(user: dict, test: dict, attempt: dict, qmap: dict, rank: dict | None = None, topper: dict | None = None, retake_url: str | None = None, coach: dict | None = None) -> None:
    """Safe fire-and-forget: emails the candidate their scorecard. Never raises."""
    try:
        to = user.get("email")
        if not to:
            return
        subject = f"Your {escape(str(test.get('title', 'test')))} result — {attempt.get('score', 0)}/{attempt.get('total_marks', 0)}"
        html = _result_html(user, test, attempt, qmap, rank, topper, retake_url, coach)
        await send_email(to=to, subject=subject, html=html)
        logger.info("Result email sent to %s for attempt %s", to, attempt.get("id"))
    except Exception as e:
        logger.warning("send_result_email failed: %s", e)


def _digest_html(d: dict) -> str:
    cname = escape(str(d.get("child", {}).get("name", "your child")))
    trend = d.get("delta_pct", 0) or 0
    tcolor = "#16a34a" if trend > 0 else "#dc2626" if trend < 0 else "#64748b"
    tarrow = "▲" if trend > 0 else "▼" if trend < 0 else "�—"
    weak = d.get("weak_subject")
    weak_line = (f'<strong>{escape(str(weak))}</strong> at {round(d.get("weak_accuracy") or 0)}% accuracy'
                 if weak else "Balanced across subjects")
    drops = d.get("drops") or []
    drops_html = ""
    if drops:
        items = "".join(
            f'<li style="margin-bottom:4px">{escape(str(x.get("title", "Test")))}: '
            f'<strong style="color:#dc2626">−{x.get("drop", 0)} pp</strong> (to {x.get("pct", 0)}%)</li>'
            for x in drops)
        drops_html = (
            f'<div style="font-size:14px;font-weight:700;color:#0f172a;margin:18px 0 6px">⚠️ Biggest score drops this week</div>'
            f'<ul style="font-size:13px;color:#475569;margin:0 0 8px;padding-left:18px">{items}</ul>')
    rows = ""
    for r in (d.get("recent") or []):
        rows += (
            f'<tr>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;font-size:13px">{escape(str(r.get("title", "Test")))}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;font-size:13px">{escape(str(r.get("date", "")))}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #eee;font-size:13px;font-weight:700">{r.get("score", 0)} / {r.get("total", 0)}</td>'
            f'</tr>'
        )
    if not rows:
        rows = '<tr><td colspan="3" style="padding:12px;font-size:13px;color:#94a3b8">No mocks attempted this week.</td></tr>'
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:#f4f6fb;padding:24px 0;font-family:Arial,Helvetica,sans-serif"><tr><td align="center">'
        f'<table role="presentation" width="640" cellpadding="0" cellspacing="0" '
        f'style="background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e5e9f2">'
        f'<tr><td style="background:#0A66C2;padding:24px 28px">'
        f'<div style="color:#ffffff;font-size:20px;font-weight:800">{escape(EMAIL_FROM_NAME)}</div>'
        f'<div style="color:#cfe0f5;font-size:13px;margin-top:2px">{cname}\'s weekly progress</div></td></tr>'
        f'<tr><td style="padding:28px">'
        f'<p style="font-size:14px;color:#475569;margin:0 0 18px">Here is how {cname} did over the last 7 days.</p>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px"><tr>'
        f'<td align="center" style="padding:14px;background:#f8fafc;border-radius:10px"><div style="font-size:22px;font-weight:800;color:#0A66C2">{d.get("week_attempts", 0)}</div><div style="font-size:12px;color:#64748b">Mocks this week</div></td>'
        f'<td width="10"></td>'
        f'<td align="center" style="padding:14px;background:#f8fafc;border-radius:10px"><div style="font-size:22px;font-weight:800;color:#0f172a">{d.get("week_avg_pct", 0)}%</div><div style="font-size:12px;color:#64748b">Avg score</div></td>'
        f'<td width="10"></td>'
        f'<td align="center" style="padding:14px;background:#f8fafc;border-radius:10px"><div style="font-size:22px;font-weight:800;color:{tcolor}">{tarrow} {abs(trend)}pp</div><div style="font-size:12px;color:#64748b">vs prior</div></td>'
        f'<td width="10"></td>'
        f'<td align="center" style="padding:14px;background:#f8fafc;border-radius:10px"><div style="font-size:22px;font-weight:800;color:#f97316">{d.get("streak_days", 0)}</div><div style="font-size:12px;color:#64748b">Day streak</div></td>'
        f'</tr></table>'
        f'<p style="font-size:14px;color:#0f172a;margin:0 0 16px">Focus area: {weak_line}.</p>'
        f'{drops_html}'
        f'<div style="font-size:14px;font-weight:700;color:#0f172a;margin-bottom:8px">Recent mocks</div>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #eee;border-radius:8px">'
        f'<tr style="background:#f8fafc"><td style="padding:8px;font-size:12px;font-weight:700;color:#64748b">Test</td>'
        f'<td style="padding:8px;font-size:12px;font-weight:700;color:#64748b">Date</td>'
        f'<td style="padding:8px;font-size:12px;font-weight:700;color:#64748b">Score</td></tr>{rows}</table>'
        f'<p style="font-size:12px;color:#94a3b8;margin:22px 0 0">Sent by {escape(EMAIL_FROM_NAME)}. '
        f'You receive this because you are a registered parent. We never ask for your password by email.</p>'
        f'</td></tr></table></td></tr></table>'
    )


async def send_parent_digest_email(parent: dict, digest: dict) -> None:
    """Safe fire-and-forget: emails a parent their child's weekly digest. Never raises."""
    try:
        to = parent.get("email")
        if not to or not digest:
            return
        cname = escape(str(digest.get("child", {}).get("name", "your child")))
        subject = f"{cname}'s weekly progress — {EMAIL_FROM_NAME}"
        html = _digest_html(digest)
        await send_email(to=to, subject=subject, html=html)
        logger.info("Digest email sent to parent %s", to)
    except Exception as e:
        logger.warning("send_parent_digest_email failed: %s", e)


def _reminder_html(user: dict) -> str:
    name = escape(str(user.get("name", "there")))
    streak = int(user.get("streak_days", 0) or 0)
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:#f4f6fb;padding:24px 0;font-family:Arial,Helvetica,sans-serif"><tr><td align="center">'
        f'<table role="presentation" width="560" cellpadding="0" cellspacing="0" '
        f'style="background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e5e9f2">'
        f'<tr><td style="background:#0A66C2;padding:22px 26px">'
        f'<div style="color:#ffffff;font-size:20px;font-weight:800">{escape(EMAIL_FROM_NAME)}</div>'
        f'<div style="color:#cfe0f5;font-size:13px;margin-top:2px">Keep your streak alive 🔥</div></td></tr>'
        f'<tr><td style="padding:26px" align="center">'
        f'<div style="font-size:44px;font-weight:800;color:#f97316;line-height:1">{streak}🔥</div>'
        f'<div style="font-size:13px;color:#64748b;margin-top:4px">day streak</div>'
        f'<p style="font-size:16px;color:#0f172a;margin:18px 0 6px">Hi {name}, you haven\'t practised today.</p>'
        f'<p style="font-size:14px;color:#475569;margin:0 0 4px;max-width:400px">'
        f'One quick mock or DPP keeps your <strong>{streak}-day</strong> streak going. '
        f'Just a few minutes is enough — log in and knock out a set before midnight.</p>'
        f'<p style="font-size:12px;color:#94a3b8;margin:24px 0 0">Sent by {escape(EMAIL_FROM_NAME)}. '
        f'You can turn these off anytime in your profile settings.</p>'
        f'</td></tr></table></td></tr></table>'
    )


async def send_streak_reminder_email(user: dict) -> None:
    """Safe fire-and-forget: nudges a student whose streak is about to break. Never raises."""
    try:
        to = user.get("email")
        if not to:
            return
        streak = int(user.get("streak_days", 0) or 0)
        subject = f"🔥 Keep your {streak}-day streak alive — {EMAIL_FROM_NAME}"
        html = _reminder_html(user)
        await send_email(to=to, subject=subject, html=html)
        logger.info("Streak reminder sent to %s", to)
    except Exception as e:
        logger.warning("send_streak_reminder_email failed: %s", e)


def _alert_html(child_name: str, test_title: str, this_pct: int, prior_avg: int) -> str:
    cname = escape(str(child_name))
    ttitle = escape(str(test_title))
    drop = max(prior_avg - this_pct, 0)
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:#f4f6fb;padding:24px 0;font-family:Arial,Helvetica,sans-serif"><tr><td align="center">'
        f'<table role="presentation" width="600" cellpadding="0" cellspacing="0" '
        f'style="background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e5e9f2">'
        f'<tr><td style="background:#0A66C2;padding:22px 26px">'
        f'<div style="color:#ffffff;font-size:20px;font-weight:800">{escape(EMAIL_FROM_NAME)}</div>'
        f'<div style="color:#cfe0f5;font-size:13px;margin-top:2px">Progress alert</div></td></tr>'
        f'<tr><td style="padding:26px">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:18px">'
        f'<tr><td style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:16px">'
        f'<div style="font-size:15px;color:#0f172a">⚠️ <strong>{cname}</strong> scored '
        f'<strong style="color:#dc2626">{this_pct}%</strong> on <strong>{ttitle}</strong> — down '
        f'<strong>{drop} pp</strong> from a recent average of <strong>{prior_avg}%</strong>.</div></td></tr></table>'
        f'<p style="font-size:14px;color:#475569;margin:0">A dip on a single mock is normal, but it can be a good '
        f'moment to check in. Log in to your parent dashboard to see {cname}\'s weak topics and recent attempts.</p>'
        f'<p style="font-size:12px;color:#94a3b8;margin:22px 0 0">Sent by {escape(EMAIL_FROM_NAME)} because you are a '
        f'registered parent. We never ask for your password by email.</p>'
        f'</td></tr></table></td></tr></table>'
    )


async def send_parent_alert_email(parent: dict, child: dict, test: dict, this_pct: int, prior_avg: int) -> None:
    """Safe fire-and-forget: alerts a parent to a sharp score drop. Never raises."""
    try:
        to = parent.get("email")
        if not to:
            return
        cname = escape(str(child.get("name", "your child")))
        subject = f"{cname}'s score dropped on a recent mock — {EMAIL_FROM_NAME}"
        html = _alert_html(child.get("name", "your child"), test.get("title", "a mock"), this_pct, prior_avg)
        await send_email(to=to, subject=subject, html=html)
        logger.info("Parent alert sent to %s", to)
    except Exception as e:
        logger.warning("send_parent_alert_email failed: %s", e)
