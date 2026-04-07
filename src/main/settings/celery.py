# ---------------------------------------------------------------------------
# Celery (heavy tasks, periodic/cron, complex retry logic)
# ---------------------------------------------------------------------------
# For lightweight async work (emails, notifications), use django.tasks instead.
# Celery is reserved for:
#   - Long-running / CPU-intensive tasks
#   - Periodic tasks via django-celery-beat (cron schedules)
#   - Tasks requiring complex retry strategies (ResilientTask)

from main.settings.config import env

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
