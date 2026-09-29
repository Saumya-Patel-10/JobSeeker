"""
Celery application configuration.
Two queues:
  - ai_queue   → resume tailoring, cover letter, interview prep (AI Workers)
  - bot_queue  → Playwright browser automation (Bot Workers)
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "jobaigent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks",
        "app.workers.scheduled",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,      # important for long-running bot tasks

    # Route tasks to correct queues
    task_routes={
        "app.workers.tasks.process_application":      {"queue": "ai_queue"},
        "app.workers.tasks.run_bot_application":      {"queue": "bot_queue"},
        "app.workers.tasks.run_job_discovery":        {"queue": "ai_queue"},
        "app.workers.scheduled.reset_daily_credits":  {"queue": "ai_queue"},
    },

    # Celery Beat schedule
    beat_schedule={
        # Job discovery every 30 minutes
        "discover-jobs-every-30-min": {
            "task": "app.workers.tasks.run_job_discovery",
            "schedule": crontab(minute="*/30"),
        },
        # Reset daily credits at midnight UTC
        "reset-daily-credits-midnight": {
            "task": "app.workers.scheduled.reset_daily_credits",
            "schedule": crontab(hour=0, minute=0),
        },
    },
)
