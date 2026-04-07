import pytest
from core.exceptions import ApplicationError


@pytest.mark.unit
class TestUserModel:
    """Unit tests for User model properties — no DB needed."""

    def test_full_name(self):
        from users.models import User

        user = User(first_name="John", last_name="Doe")
        assert user.full_name == "John Doe"

    def test_full_name_empty(self):
        from users.models import User

        user = User(first_name="", last_name="")
        assert user.full_name == ""

    def test_full_name_first_only(self):
        from users.models import User

        user = User(first_name="John", last_name="")
        assert user.full_name == "John"

    def test_full_name_last_only(self):
        from users.models import User

        user = User(first_name="", last_name="Doe")
        assert user.full_name == "Doe"

    def test_str_returns_email(self):
        from users.models import User

        user = User(email="test@example.com")
        assert str(user) == "test@example.com"


@pytest.mark.unit
class TestApplicationError:
    """Unit tests for ApplicationError — no DB needed."""

    def test_default_extra(self):
        err = ApplicationError("Something failed")
        assert err.message == "Something failed"
        assert err.extra == {}

    def test_custom_extra(self):
        err = ApplicationError("Bad input", extra={"field": "email"})
        assert err.message == "Bad input"
        assert err.extra == {"field": "email"}

    def test_is_exception(self):
        err = ApplicationError("fail")
        assert isinstance(err, Exception)
