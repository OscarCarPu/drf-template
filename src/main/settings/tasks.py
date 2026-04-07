# ---------------------------------------------------------------------------
# Django Background Tasks (django.tasks)
# ---------------------------------------------------------------------------
# Used for lightweight async work: emails, notifications, simple processing.
# For heavy computation, periodic/cron, or complex retry logic, use Celery.

TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
    }
}
