import logging

from django.tasks import task

logger = logging.getLogger(__name__)


@task()
def send_welcome_email(*, user_id: int):
    """Send a welcome email to a newly created user (via django.tasks)."""
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
