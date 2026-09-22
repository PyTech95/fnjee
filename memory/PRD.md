# FNJEE.com — Quiz & Mock-Test Platform

## Original Problem Statement
User uploaded an existing React + FastAPI + MongoDB quiz application (Quiz-test-17aug-main.zip) and asked to "deploy this" under a hardened deployment plan (audit → harden → containerize → DB → build → go-live), with explicit security concerns: server-side scoring, no answer-key leakage, dedupe/one-attempt lock, server-side timer, concurrent load.

Latest request: "Sir table and picture nhin h kisi bhi question me Only text h esme proper tabel aana chahiye - ai se enhance karke website me daliye"; confirmed "yes please with image the question". User supplied DPP 9 and DPP 10 solutions PDFs and approved using the existing AI configuration with sensible defaults.

## Stack / Architecture
- Frontend: React 18 (CRA + craco), Tailwind, shadcn/ui, react-router 7. API via `REACT_APP_BACKEND_URL` + `/api`.
- Backend: FastAPI (single `server.py` monolith, `/api` router), JWT + bcrypt auth, Motor/MongoDB.
- DB: MongoDB via `MONGO_URL`/`DB_NAME`. Indexes on users.email (unique), users.referral_code, questions.subject.
- AI features (question import parsing, difficulty prediction, podcast scripts) via emergentintegrations + `EMERGENT_LLM_KEY`.
- Roles: admin, teacher, parent, student. Marketing/landing pages included.

## What Was Done (2026-06, current)
- **Smart drill link + time chart** (latest):
  - Result page "Drill your weakest" button now computes the lowest-accuracy difficulty and dominant subject, deep-links to `/student/practice?subject=..&difficulty=..`. `Practice.jsx` reads those query params (`useSearchParams`) to preselect subject + difficulty.
  - New "Where your time went" card on the result page: recharts horizontal bar chart of the 10 slowest questions, colored by result (green correct / red wrong), using persisted `time_taken`.
- **Difficulty tags + timed analytics**:
  - All 75 bio questions tagged easy/medium/hard (`DIFFICULTY` map in `seed_bio_paper.py`; 17/31/27). Practice page already filters Subject+Difficulty → students can drill "Biology / Hard".
  - Per-question time now persisted server-side: added `time_taken` to `AttemptAnswerIn`, stored `time_taken`+`difficulty` in each `detailed` entry (`server.py` submit); `LiveExam.jsx` sends it.
  - `Result.jsx`: new "Accuracy & time by difficulty" card (accuracy %, correct/wrong, avg time per level) + a "Drill your weak level" link to Practice; per-question review shows difficulty badge + time (server value with sessionStorage fallback).
- **CBSE Biology paper** — 75-question test with 17 diagram images.
  - NEET-style scoring turned on for this paper: +4 correct / −1 wrong, total 300. Validated (all-correct 300, one-wrong 295).
  - Result page (`Result.jsx`) question review enriched: shows diagram image, your answer + correct answer as full option TEXT (e.g. "C. …"), and the worked explanation (revealed only post-submit; `correct` still stripped from the student test payload).
  - Answer key re-reviewed; standing by all 75 (agent-derived, teacher can flip any Q# on request).
- **CBSE Biology paper (initial)**: Recreated the user's uploaded 75-question CBSE Class 12 Biology worksheet.
  - Extracted 17 figure-based diagrams from the PDF via high-DPI page clips (captures raster + vector labels A/B/C, P/Q/R/S, I–VI, numbers, a–d), stored as base64 data URLs in `/app/backend/bio_images.json` (self-contained, no external hosting).
  - `/app/backend/seed_bio_paper.py` (`run_bio_seed`, idempotent via deterministic uuid5 ids) seeds 75 MCQs (1 mark each, no negative) + one test, wired into server startup. Test id `d57fa55c-...`.
  - Derived the full 75-answer key from NEET/NCERT biology. Validated: student view shows 75 Qs with 17 images and NO answer leak; all-correct submission scores 75/75.
  - ⚠️ Answer key is agent-derived (the PDF had no key) — a handful of ambiguous items (Q11, Q12, Q18, Q21, Q24, Q44, Q58, Q60, Q72) should be teacher-verified.

## Re-port & Deploy Session (2026-06)
- Received `Mock-Test-Club2-main.zip`; extracted and ported full app into `/app` (preserved platform `.env` keys).
- Backend `.env` hardened: strong env-driven `JWT_SECRET`, `ENV=production`, `EMERGENT_LLM_KEY`, `APP_BASE_URL`, and `CORS_ORIGINS` LOCKED to the deployed frontend origin (NOT wildcard — per hardening plan item #2).
- Installed backend deps (litellm/emergentintegrations already in base image), `yarn install` frontend. Both services healthy via supervisor.
- Demo data auto-seeds on startup (idempotent). `/api/health` returns `{status:healthy, db:up, env:production}`.
- Deployment-readiness scan: PASS (1 WARN — CORS not wildcard, intentional/by-design).
- Testing (iteration_1): no critical/blocking bugs. Verified: all 4 role logins + wrong-role/password 401, server-side scoring, answer-key hidden pre & post submit, idempotent double-submit, server-side timer, RBAC, rate-limit 429 on login(10/min)/submit(20/min), health endpoint, student take-test E2E. backend 94% (one stale-data pytest, not a prod bug), frontend 100%.
- At real deploy: set `CORS_ORIGINS` (+ `APP_BASE_URL`, `REACT_APP_BACKEND_URL`) to the production origin; point `MONGO_URL` to managed Atlas with backups.

## What Was Done (prior deploy session)
- Phase 1 audit: no hardcoded secrets/DB strings; env-based config already present; no committed .env.
- Installed app into /app; installed backend deps + emergentintegrations; yarn install frontend.
- Configured backend/.env: strong `JWT_SECRET`, `ENV=production`, `EMERGENT_LLM_KEY`, locked `CORS_ORIGINS` to preview + production domains (no wildcard).
- Added `/api/health` endpoint (db ping).
- Added in-memory rate limiting: 10 logins/min per IP, 20 submits/min per student → HTTP 429.
- Fixed deployment blockers found by scan: removed destructive `db.courses.delete_many({})` startup migration; fixed N+1 query in `/api/leaderboard` referral branch (batch fetch).
- Verified existing hardening: server-side scoring, answer-key stripped for students pre-submit, idempotent double-submit, server-side timer (`ends_at`).
- Testing: 19/19 backend pytest green; frontend E2E (4 role logins + full take-test→submit→result flow). Deployment readiness scan: PASS.

## Security-Critical Behaviors (verified)
- Answer key never sent to students before submission; explanations only after submit when allowed.
- Scoring recomputed server-side on submit.
- One in-progress attempt lock; re-submit returns existing result (no score doubling).
- Timer authoritative server-side with 120s network grace.

## Test Credentials
See /app/memory/test_credentials.md (admin/student/teacher/parent, all `@examnest.io`). Login requires email+password+role.

## Advanced Feature Roadmap (building "one by one")
Market-researched roadmap of 18 features. Building in batches.
- ✅ Batch 0: live leaderboard, difficulty heatmap, error tracking, distributed (MongoDB) rate limiting.
- ✅ Landing page redesign — "Neo-Athletic Academic" (Clash Display + Satoshi, cream + electric-red, brutalist offset shadows, dark stat/footer, heavy framer-motion). Scoped under `.mkt`.
- ✅ Batch 1 (AI): #1 AI Doubt-Solver + #2 Notes→Quiz. Tested (iteration_3).
- ✅ SEO + PWA + Mobile-ready (Android/TWA foundation): manifest w/ maskable icons + shortcuts, service worker (SWR caching), robots.txt, sitemap.xml, full OG/Twitter/Apple meta, JSON-LD (Organization/WebSite/FAQPage), generated app icon + OG image. AppShell mobile bottom-tab bar + slide-in drawer + safe-area insets. Tested (iteration_4).
- ✅ Batch 2 (4 features): #4 AI Weakness Coach (`/api/coach/plan`,`/coach/drill`, page /student/coach), #5 Smart Revision / spaced repetition SM-2-lite (`/api/reviews/stats|due|grade`, hooked into submit_attempt, page /student/revision), #3 Adaptive CAT (`/api/adaptive/start|answer`, difficulty stepping, page /student/adaptive), #9 Quiz Battles real-time multiplayer poll-based shared-clock (`/api/battles/create|join|{id}/start|{id}|{id}/answer`, page /student/battles). Tested 100% (iteration_4). Battle join rate-limited.
- ⬜ Batch 3: #6 PYQ archive, #7 full-length timed mock series.
- ⬜ Batch 4: #10 badges/levels/goals, #11 study groups/cohorts.
- ⬜ Batch 5: #12 lockdown/tab-switch integrity, #15 item analysis (difficulty+discrimination index).
- ⬜ Batch 6: #16 predicted rank + time analytics, #17 PDF/Excel report export.
- ⬜ Batch 7: #13 AI webcam proctoring.
- ⬜ Batch 8: #18 subscription tiers + payments.

## Backlog / Remaining (not blocking)
- P2: `server.py` monolith could be split into routers (maintainability only).
- P1: real error tracking/logging integration (Sentry) if desired for production observability.

---
## Deployment Restore — June 2026
- Restored `mock-test22` (Abhyash Mantra / ExamNest — NEET/JEE exam prep) from uploaded zip into /app.
- Backend deps installed (emergentintegrations + requirements), frontend deps via yarn.
- Env configured: EMERGENT_LLM_KEY, JWT_SECRET, ENV added to backend/.env (MONGO_URL, DB_NAME, REACT_APP_BACKEND_URL preserved).
- Verified: /api/health healthy, demo data seeded, auth login working (login requires role field), landing page renders.
- deployment_agent: PASS — no blockers.

## Rebrand to FNJEE.com — June 2026
- Replaced brand name "Abhyash Mantra" → "FNJEE.com" across 28 files (75 occurrences): frontend pages, marketing copy, emails, index.html meta, manifest, print templates.
- Added uploaded logo: cropped/transparent /frontend/public/fnjee-logo.png (header lockup) + regenerated favicon-32, icon-192/512, apple-touch, maskable from the logo mark.
- Swapped placeholder "M" logo boxes for real logo in MarketingLayout (header+footer), AppShell (sidebar+mobile), Login, Signup.
- Kept examnest.io seed emails/credentials unchanged (not user-facing brand).
- Verified: landing, title, and login render new branding.

## Visual Questions & PDF Import — 2026-09-22
### Source limitations and content decisions
- Both uploaded PDFs contain **solutions only**, 20 numbered explanations each; original question stems/options and referenced diagrams are absent. DPP 10 contains a comparison table in solution 20. Files preserved at `backend/source_documents/dpp-9-solutions.pdf` and `dpp-10-solutions.pdf`.
- User was informed that new papers are **AI-adapted practice**, not reconstructed originals. Gemini 3 Flash genuinely generated 40 questions; no API mocks.
- Added two publicly assigned Biology tests (20 questions, 30 minutes, 80 marks, +4/−1), visibly labelled AI-adapted:
  - DPP 9: `0e87d454-f910-5e29-824f-6f37a26a14ff` — 7 image questions, 4 question tables.
  - DPP 10: `93498a34-4acf-5660-b70e-ebdefcb810f7` — 6 image questions, 5 question tables; Q20 has a restored solution comparison table plus exact source-table image.
- AI raw output saved in `backend/dpp_9_content.json`, `dpp_10_content.json`. **Publish via `reviewed_dpp.py` / `seed_dpp_papers.py`, not raw JSON**: editorial corrections address pulmonary-vein valves, platelet/coagulation wording, ABO red-cell compatibility scope, and textbook Rh frequency. Accessible diagram descriptions contain only visible information, not hidden label identities.
- Six deterministic scientific schematic types (blood route, vessel cross-sections, conduction, blood fractions, portal route, haemoglobin) generated using Pillow in `biology_visuals.py`; bundled licensed font in `backend/assets`. Self-contained PNG data URLs persisted in Mongo; no external image host dependency.
- DPP seed uses deterministic uuid5 IDs and `$setOnInsert`; does not overwrite subsequent edits. It is called from server startup. Re-running does not duplicate questions/tests.

### Existing content repaired
- Restored actual two-column matching tables for CBSE Biology Q31–38 through `biology_tables.py` and the existing seed.
- Preserved all 75 original questions, option order, answer keys and 17 original diagram images.

### Shared rendering & importer
- `MathText.jsx` now renders GFM tables safely with `react-markdown`/`remark-gfm`; `InlineFormula.jsx` handles LaTeX separately. This avoids the development visual-editor Babel recursion encountered with self-referencing JSX. No raw HTML rendering.
- `QuestionContent.jsx` / `QuestionImage` provide responsive un-cropped images, accessible labels, zoom dialog, invalid-URL filtering and image-load errors. Shared across exams, results, adaptive, revision, battles, admin/teacher question-bank previews and import review.
- `printPaper.js` prints tables, formulas and diagrams; solutions/solution images only appear with answer-key mode. Unique print test IDs and safe escaping retained.
- PDF import now uses Gemini vision with the original PDF attachment via `visual_pdf.py`; tables remain Markdown, diagrams are bounded high-resolution PyMuPDF crops preserving labels. Limits: 25 MB / 30 pages per import; 240s AI timeout; temporary PDF deleted afterward.
- Explicit import modes: extract originals (solutions-only PDF yields zero questions plus warning) or create adapted practice from solutions. Review UI shows question/solution media separately; supports removing a bad image and editing text/options. Final UI save approves reviewed selections.
- New QuestionIn fields: `image_alt`, `explanation_image_url`, `content_origin`, `source_number`. Existing `image_url` remains compatible. All Mongo returns exclude `_id` or use existing clean/model paths.
- Student test payload retains question images but hides answer keys, hints, explanations **and explanation images** until submission; solution reveal also respects `show_solutions_after`. `_strip_q` now carries question image fields for adaptive/revision/battles.
- Wrapped narrow-screen exam controls, added min-width constraints, and resolved dashboard/result Recharts initial negative-dimension warnings without suppressing console output.

### Verification
- Testing agent report: `/app/test_reports/iteration_2.json`; 9/9 backend tests passed, main browser exam/import flows passed. Agent omitted strict print workflow and used a generated solutions fixture due to a wrong file path; both gaps subsequently covered by main agent.
- Corrected regression test path to the actual uploaded DPP 10 file and tightened diagram/table/key assertions and fixture cleanup. Rerun: **9/9 passed**, `/app/test_reports/dpp-retest.log`.
- Real original-question PDF fixture extraction retained its table, cropped image and answer mapping; commit preserved media metadata. Exact DPP 10 PDF in extract mode correctly returned solutions-only warning, zero questions.
- Browser verified admin previews, student image enlargement, exam submission/result reveal; print student copy has table/image/LaTeX and zero answers, teacher copy includes solution table and source image.
- Responsive browsing contexts at 320/768/1024/1440px: image and table questions fit without page overflow. Dashboard charts render without negative-dimension warnings.
- Production build passed (`test_reports/final-build.log`) with pre-existing hook-dependency/bundle-size warnings, no compiler errors. Python compilation passed. Health API healthy; final DB 135 questions, 6 tests; no disposable question or print fixtures remaining.
- Testing-created account recorded in `memory/test_credentials.md`. Student3 submitted both DPPs. Dedicated autotest account has an unsubmitted DPP9 attempt from responsive checks; Student1/Student2 remain available for new sets.

### Prioritized next actions
- P0: No known blocking issues in the implemented table/image flows.
- P1: User/teacher review of the adapted DPPs; retain clear AI-adapted labels. Original question PDFs are required only if exact original-paper reproduction is later requested.
- P1 deferred: `fnjee.com` domain connection remains outside this task.
- P2: Diagram-only practice filter; teacher approval indicators for AI-generated content; broader old roadmap unchanged.
- P2 technical backlog: existing monolithic server and pre-existing hook warnings. Existing JWT-secret fallback was noted by testing but auth was not changed in this task; protected environment secret is configured.
