# FNJEE.com — Hardened Deployment (ExamNest quiz & mock-test platform)

## Original Problem Statement
"FNJEE — Hardened Deployment Plan": take the uploaded project (FNJEE-main.zip) live safely with rollback + guardrails. Phases: 0 verify stack/env/build, 1 backend health/ready + locked CORS + env config, 2 Mongo auth/TLS/backups/indexes, 3 React prod build + env API URL, 4 HTTPS, rate limiting, secrets store, one-step rollback, smoke test. User: "deploy here".

## Architecture
React 18 (CRA+craco, Tailwind, shadcn) → FastAPI (`server.py` + `cbt.py`) → MongoDB (Motor). JWT+bcrypt auth (4 roles). AI import via emergentintegrations (EMERGENT_LLM_KEY). Crons in `.emergent/crons.yml` (weekly-digest, study-reminder; auth via WEBHOOK_CRON_SECRET).

## Done (2026-06)
- Phase 0: zip extracted & ported into /app (platform .env keys preserved); stack confirmed; deps installed (+6 missing pdf/docx libs), requirements pinned via pip freeze; `yarn build` passes.
- Fail-fast: `JWT_SECRET` and `CORS_ORIGINS` now required (no defaults); ENV=production refuses start if JWT_SECRET < 32 chars or CORS contains '*'.
- Added `/api/live` (liveness) and `/api/ready` (DB ping → 503 if unreachable); `/api/health` kept.
- CORS locked to frontend origin; prod is same-origin via /api ingress.
- Existing: rate limits (login 10/min, submit 20/min), server-side scoring, answer-key stripping, idempotent submit, indexes, error capture to `error_logs`.
- .gitignore no longer excludes .env (deploy blocker).
- Testing iteration_7: backend 14/14, frontend 100%.

## Feature Audit (2026-06, iteration_9 + 10)
- Full audit: backend 49/49 pytest green; frontend 34/34 routes (after fix).
- Fixed: /admin/grading route was missing in App.js (ManualGrader never wired) — now renders in admin layout, verified.
- Working: auth 4 roles, student test flow (timer, server scoring, idempotent submit, no key leak), CBT demo exam, doubt-solve (live LLM), podcasts, flashcards/mindmaps/PYQ/store/referrals APIs, admin question CRUD, analytics, proctoring, system health, AI settings, teacher + parent portals.
- Pending (not bugs): email/weekly-digest needs EMERGENT_EMAIL_KEY (not configured); PUT /api/questions requires full payload (no partial PATCH); production deploy awaiting user's 50 ECU confirm.

## Pending Work Completed (2026-06, iteration_11)
- Email live: EMERGENT_EMAIL_KEY + EMAIL_FROM_NAME="FNJEE.com" in backend/.env; verified real send via managed Resend proxy (delivered@resend.dev). Demo @examnest.io addresses skipped in send_email (fake domain → avoid bounces). Weekly digest + study reminder crons auth-protected (401 without WEBHOOK_CRON_SECRET), ack 200 + background run. Result scorecard emails fire on submit.
- PATCH /api/questions/{qid}: partial update, merged + validated against QuestionIn (422 bad enum, 400 unknown field, 404 missing). Frontend `questionsApi.patch`.
- Readiness: all checks pass except scanner's CORS-wildcard suggestion — intentionally kept locked (user's plan: no '*' in prod; prod is same-origin).
- Testing iteration_11: 12/12 backend, frontend 100%.

## Backlog

## VPS-ready AI layer (2026-06, iteration_12)
- `backend/ai_chat.py::ai_complete(system, text, file_paths, max_tokens)` — single entry for ALL 13 LLM call sites. Emergent key (admin provider 'emergent' or env) → emergentintegrations LlmChat; own OpenAI/Gemini/Claude key → direct REST to official provider APIs (httpx, no Emergent dependency — works on VPS).
- Own-key default models are real provider models (gpt-4.1-mini / gemini-2.5-flash / claude-haiku-4-5-20251001); stale Emergent-catalog names auto-remapped. PDF file inputs supported on all 3 direct providers (base64).
- Key-test endpoint reports mode: emergent|direct. Testing: 17/17 (live emergent regression + mocked direct paths + PDF wiring).

### VPS porting checklist (for user's self-host)
- DONE (iteration_13, 21/21): see /app/DEPLOY_VPS.md.
- Email: email_utils.email_mode() precedence RESEND_API_KEY > SMTP_HOST > EMERGENT_EMAIL_KEY > disabled; guardrail gate on all paths; demo @examnest.io skipped.
- Cron: backend/scheduler.py (APScheduler) when ENABLE_INTERNAL_SCHEDULER=true (set by docker-compose, OFF on Emergent → no double sends). Single worker.
- Infra: docker-compose.yml (mongo:7 auth, no exposed port; backend; Caddy web with auto-HTTPS, /api proxy, cache headers; daily mongodump backup service + deploy/restore.sh). backend/requirements.vps.txt excludes emergentintegrations/litellm (they conflict on public PyPI). frontend Dockerfile rewrites hardcoded preview URLs in index.html/sitemap/robots with SITE_URL.
- Removed leftover emergentintegrations import guards in ai_parser.py (would have broken import on VPS).
- GET /api/admin/system/integrations shows ai/email/scheduler modes.
- Verified by real VPS simulation: clean venv without emergentintegrations boots, scheduler on, SMTP send via local server, own OpenAI key reaches real API.
- Not verified here: docker image builds (no docker in pod), Caddy TLS issuance.
- AI: admin AI Settings → paste own key (done, works). Email: needs own SMTP/Resend (currently Emergent proxy). Crons: need own scheduler (currently platform crons.yml). Mongo: own instance, set MONGO_URL/DB_NAME. Env: JWT_SECRET, CORS_ORIGINS=<own domain>.

## Demo test new tab (2026-06)
- Marketing header "Demo Test" (desktop + mobile) now opens /demo in a new browser tab (`target="_blank" rel="noopener noreferrer"`); landing page tab stays put. Verified via browser automation. Signup CTAs ("Start free mock") unchanged.
- P1: add custom domain to CORS_ORIGINS/APP_BASE_URL when linked; EMERGENT_EMAIL_KEY for digest emails
- P2: split server.py into routers; structured auth logs; staging env; uptime alerts

## Feature: Admin-managed AI key (2026-06)
- `backend/ai_key.py`: admin DB key (`db.settings` id='ai') > `EMERGENT_LLM_KEY` env fallback; provider map (emergent/openai/gemini/claude) → LlmChat provider + default model; module-level cache refreshed on startup + save/reset.
- Endpoints (admin-only): GET/PUT/DELETE `/api/admin/settings/ai`, POST `/api/admin/settings/ai/test` (live probe call, 5/min rate limit). Key stored in Mongo, returned only masked.
- All 13 LLM call sites (server.py ×5, ai_parser ×3, faithful_import, visual_pdf + helpers) now resolve via `ai_key.resolve()` — admin key applies instantly, no restart. Works on VPS with any own key.
- UI: `/admin/settings` (AdminSettings.jsx) — status card (source badge, masked key, model), provider select, password key input, optional model override, Test key, Reset-to-env.
- Testing iteration_8: backend 16/16, frontend save→test→reset flow 100%.
