"""In-process cron for self-hosted (VPS) runs. Mirrors .emergent/crons.yml.

Enable with ENABLE_INTERNAL_SCHEDULER=true. Keep it OFF on the Emergent platform
(the platform scheduler already calls /api/cron/*) to avoid double sends.
Requires a single backend worker (uvicorn --workers 1).
"""
import logging
import os

log = logging.getLogger("scheduler")
_sched = None


def start(weekly_digest, study_reminder):
    global _sched
    if os.environ.get("ENABLE_INTERNAL_SCHEDULER", "").lower() != "true":
        return False
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    _sched = AsyncIOScheduler()
    _sched.add_job(weekly_digest, CronTrigger(day_of_week="mon", hour=8, minute=0, timezone="Asia/Kolkata"),
                   id="weekly-digest", max_instances=1, coalesce=True)
    _sched.add_job(study_reminder, CronTrigger(minute=30, timezone="UTC"),
                   id="study-reminder", max_instances=1, coalesce=True)
    _sched.start()
    log.info("Internal scheduler started: %s", [j.id for j in _sched.get_jobs()])
    return True


def jobs():
    if not _sched:
        return []
    return [{"id": j.id, "next_run": j.next_run_time.isoformat() if j.next_run_time else None}
            for j in _sched.get_jobs()]


def stop():
    if _sched:
        _sched.shutdown(wait=False)
