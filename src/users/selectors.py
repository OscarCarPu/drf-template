from django.db.models import QuerySet

from users.filters import UserFilter
from users.models import User


def user_list(*, filters: dict | None = None) -> QuerySet[User]:
    filters = filters or {}
    qs = User.objects.all()
    return UserFilter(filters, qs).qs


def user_get(*, user_id: int) -> User | None:
    return User.objects.filter(id=user_id).first()
