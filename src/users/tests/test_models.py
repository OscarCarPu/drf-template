import pytest

from users.models import User


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")

        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password("testpass123")

    def test_create_superuser(self):
        user = User.objects.create_superuser(email="admin@example.com", password="adminpass123")

        assert user.is_staff is True
        assert user.is_superuser is True

    def test_create_user_without_email_raises(self):
        with pytest.raises(ValueError, match="The Email field must be set"):
            User.objects.create_user(email="", password="testpass123")

    def test_str_returns_email(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        assert str(user) == "test@example.com"

    def test_full_name(self):
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", first_name="John", last_name="Doe"
        )
        assert user.full_name == "John Doe"

    def test_full_name_empty(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        assert user.full_name == ""

    def test_has_timestamps(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        assert user.created_at is not None
        assert user.updated_at is not None
