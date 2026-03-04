from unittest.mock import patch

import pytest

from core.exceptions import ApplicationError
from users.factories import UserFactory
from users.services import user_create, user_deactivate, user_update


@pytest.mark.django_db
class TestUserCreate:
    def test_creates_user(self):
        with patch("users.services.task_on_commit"):
            user = user_create(email="new@example.com", password="testpass123")

        assert user.email == "new@example.com"
        assert user.is_active is True
        assert user.check_password("testpass123")

    def test_creates_user_with_name(self):
        with patch("users.services.task_on_commit"):
            user = user_create(
                email="new@example.com",
                password="testpass123",
                first_name="Jane",
                last_name="Doe",
            )

        assert user.first_name == "Jane"
        assert user.last_name == "Doe"


@pytest.mark.django_db
class TestUserUpdate:
    def test_updates_first_name(self):
        user = UserFactory()
        updated_user = user_update(user=user, data={"first_name": "Updated"})

        assert updated_user.first_name == "Updated"

    def test_updates_multiple_fields(self):
        user = UserFactory()
        updated_user = user_update(user=user, data={"first_name": "New", "last_name": "Name"})

        assert updated_user.first_name == "New"
        assert updated_user.last_name == "Name"

    def test_ignores_non_allowed_fields(self):
        user = UserFactory()
        original_email = user.email
        updated_user = user_update(user=user, data={"email": "hacked@example.com"})

        assert updated_user.email == original_email


@pytest.mark.django_db
class TestUserDeactivate:
    def test_deactivates_user(self):
        user = UserFactory(is_active=True)
        deactivated = user_deactivate(user=user)

        assert deactivated.is_active is False

    def test_raises_if_already_deactivated(self):
        user = UserFactory(is_active=False)

        with pytest.raises(ApplicationError, match="already deactivated"):
            user_deactivate(user=user)
