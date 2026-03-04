import logging

from celery import Task
from django.conf import settings
from django.core.mail import mail_admins
from django.db import transaction

logger = logging.getLogger(__name__)


class ResilientTask(Task):
    """
    Base Celery task with automatic retry, exponential backoff,
    and admin email notification on final failure.

    Usage:
        @shared_task(base=ResilientTask, bind=True, max_retries=3)
        def my_task(self, arg):
            ...
    """

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        subject = f"[Celery] Task {self.name} failed"
        message = (
            f"Task ID: {task_id}\n"
            f"Args: {args}\n"
            f"Kwargs: {kwargs}\n"
            f"Exception: {exc}\n"
            f"Traceback:\n{einfo}"
        )
        logger.error(message)

        if not settings.DEBUG:
            mail_admins(subject, message)

        super().on_failure(exc, task_id, args, kwargs, einfo)


def task_on_commit(task, *args, **kwargs):
    """
    Schedule a Celery task to run after the current DB transaction commits.

    Usage:
        task_on_commit(send_welcome_email, user_id=user.id)
    """
    transaction.on_commit(lambda: task.delay(*args, **kwargs))
