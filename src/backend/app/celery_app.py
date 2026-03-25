from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "matrix",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_retry_delay=10,
    task_max_retries=3,
    beat_schedule={
        "daily-pg-backup": {
            "task": "app.tasks.backup.daily_pg_backup",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
