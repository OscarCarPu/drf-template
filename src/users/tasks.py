import logging

from celery import shared_task

from utils.tasks import ResilientTask

logger = logging.getLogger(__name__)


@shared_task(base=ResilientTask, bind=True, max_retries=3)
def send_welcome_email(self, *, user_id: int):
    from django.conf import settings
    from django.core.mail import send_mail

    from users.models import User

    user = User.objects.get(id=user_id)

    send_mail(
        subject="Welcome!",
        message=f"Hi {user.first_name or user.email}, welcome to our platform!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

    logger.info("Welcome email sent to %s", user.email)
