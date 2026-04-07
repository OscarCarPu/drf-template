import pytest

from users.factories import UserFactory
from users.selectors import user_get, user_list


@pytest.mark.integration
@pytest.mark.django_db
class TestUserList:
    def test_returns_all_users(self):
        UserFactory.create_batch(3)
        result = user_list()

        assert result.count() == 3

    def test_filters_by_is_active(self):
        UserFactory.create_batch(2, is_active=True)
        UserFactory.create_batch(1, is_active=False)

        active = user_list(filters={"is_active": True})
        assert active.count() == 2

    def test_filters_by_email(self):
        UserFactory(email="findme@example.com")
        UserFactory(email="other@example.com")

        result = user_list(filters={"email": "findme"})
        assert result.count() == 1


@pytest.mark.integration
@pytest.mark.django_db
class TestUserGet:
    def test_returns_user(self):
        user = UserFactory()
        result = user_get(user_id=user.id)

        assert result == user

    def test_returns_none_for_missing_user(self):
        result = user_get(user_id=99999)
        assert result is None
