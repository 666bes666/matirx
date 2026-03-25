import logging
import subprocess
from datetime import UTC, datetime

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def daily_pg_backup(self):
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"/tmp/matrix_backup_{timestamp}.sql"

    try:
        subprocess.run(
            [
                "pg_dump",
                "-h",
                "db",
                "-U",
                "matrix",
                "-d",
                "matrix",
                "-f",
                filename,
            ],
            env={"PGPASSWORD": "matrix_dev"},
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("Backup created: %s", filename)
        return {"status": "ok", "file": filename}
    except subprocess.CalledProcessError as exc:
        logger.error("Backup failed: %s", exc.stderr)
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc
