from django.db import transaction

from core.exceptions import ApplicationError
from users.models import User
from utils.services import model_update
from utils.tasks import task_on_commit


@transaction.atomic
def user_create(*, email: str, password: str, first_name: str = "", last_name: str = "") -> User:
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    from users.tasks import send_welcome_email

    task_on_commit(send_welcome_email, user_id=user.id)

    return user


@transaction.atomic
def user_update(*, user: User, data: dict) -> User:
    fields = ["first_name", "last_name"]
    user, _has_updated = model_update(instance=user, fields=fields, data=data)
    return user


@transaction.atomic
def user_deactivate(*, user: User) -> User:
    if not user.is_active:
        raise ApplicationError("User is already deactivated.")

    user.is_active = False
    user.full_clean()
    user.save(update_fields=["is_active", "updated_at"])
    return user
