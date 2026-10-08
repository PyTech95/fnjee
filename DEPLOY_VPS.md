# FNJEE — VPS Self-Hosting Guide

Stack on the VPS: **Caddy** (auto HTTPS + static React) → **FastAPI** → **MongoDB (auth on, not exposed)** + daily backups. Everything runs with Docker Compose.

## 1. Server prerequisites
- Ubuntu 22.04+ VPS, 2 GB RAM minimum (4 GB recommended for the React build)
- Domain `A` record → VPS IP (e.g. `fnjee.com`)
- Ports 80 and 443 open
- Docker: `curl -fsSL https://get.docker.com | sh`

## 2. Get the code and configure
```bash
git clone <your-repo> fnjee && cd fnjee
cp deploy/compose.env.example .env            # DOMAIN, ACME_EMAIL, Mongo root user/pass
cp deploy/backend.env.example backend/.env    # JWT_SECRET, CORS_ORIGINS, email
nano .env backend/.env
```
Rules (the backend refuses to start otherwise):
- `JWT_SECRET` ≥ 32 chars
- `CORS_ORIGINS` = `https://<your domain>` — never `*`

## 3. Launch
```bash
docker compose up -d --build
docker compose ps                      # all services healthy
curl https://fnjee.com/api/ready       # {"status":"ready","db":"up",...}
```
First start seeds demo data. **Immediately change the demo passwords** (admin@examnest.io / Admin@123 etc.) or delete those users.

## 4. Turn on AI (OpenAI / Gemini / Claude)
Login as admin → **AI Settings** → choose provider → paste your key → **Save** → **Test key**.
Calls go directly to the provider's official API. No restart needed.

## 5. Email
Set ONE of these in `backend/.env`, then `docker compose up -d backend`:
- **Resend**: `RESEND_API_KEY` + `EMAIL_FROM_ADDRESS` on a domain verified in Resend
- **SMTP**: `SMTP_HOST`, `SMTP_PORT` (587 STARTTLS / 465 SSL), `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM_ADDRESS`

Check: Admin → `GET /api/admin/system/integrations` shows `email.mode` = `resend` or `smtp`.

## 6. Scheduled jobs
Built in (`ENABLE_INTERNAL_SCHEDULER=true` is set by docker-compose):
- weekly parent digest — Monday 08:00 IST
- study streak reminder — hourly at :30

Keep backend at **1 worker** (already set) so jobs don't run twice.

## 7. Backups & restore
- `backup` service writes `backups/fnjee-<timestamp>.archive.gz` daily, keeps 14 days.
- Restore: `./deploy/restore.sh backups/fnjee-YYYYMMDD-HHMMSS.archive.gz`
- Copy `backups/` off-server regularly (e.g. `rclone` to S3/Drive) — a backup on the same disk is not a backup.
- **Test a restore once** before real users arrive.

## 8. Updates & one-step rollback
```bash
git pull && docker compose up -d --build            # deploy
git checkout <previous-tag> && docker compose up -d --build   # rollback
```
Tag every release (`git tag v1.3 && git push --tags`) so rollback is one command.
Take a manual backup before a risky update: `docker compose exec backup sh -c 'mongodump --uri="$MONGO_URI" --archive=/backups/pre-update.archive.gz --gzip'`

## 9. Logs
`docker compose logs -f backend` · `docker compose logs -f web`

## What differs from the Emergent-hosted version
| Feature | Emergent | VPS |
|---|---|---|
| AI | Emergent universal key | your own key in Admin → AI Settings |
| Email | Emergent proxy | your Resend / SMTP |
| Cron | platform `.emergent/crons.yml` | built-in scheduler |
| HTTPS | platform | Caddy (Let's Encrypt, automatic) |
| DB | platform Mongo | Mongo container with auth + daily backups |
