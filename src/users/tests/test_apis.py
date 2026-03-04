from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from users.factories import UserFactory


@pytest.mark.django_db
class TestUserListApi:
    def test_requires_auth(self):
        client = APIClient()
        response = client.get("/api/users/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_lists_users(self, authenticated_client):
        UserFactory.create_batch(3)
        response = authenticated_client.get("/api/users/")

        assert response.status_code == status.HTTP_200_OK
        # LimitOffset pagination wraps results
        assert "results" in response.data
        assert len(response.data["results"]) >= 3


@pytest.mark.django_db
class TestUserDetailApi:
    def test_returns_user(self, authenticated_client):
        user = UserFactory()
        response = authenticated_client.get(f"/api/users/{user.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_returns_404_for_missing_user(self, authenticated_client):
        response = authenticated_client.get("/api/users/99999/")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUserCreateApi:
    @patch("users.services.task_on_commit")
    def test_creates_user(self, mock_task, authenticated_client):
        data = {
            "email": "new@example.com",
            "password": "securepass123",
            "first_name": "New",
            "last_name": "User",
        }
        response = authenticated_client.post("/api/users/create/", data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "new@example.com"

    def test_validates_input(self, authenticated_client):
        data = {"email": "invalid", "password": "short"}
        response = authenticated_client.post("/api/users/create/", data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserUpdateApi:
    def test_updates_user(self, authenticated_client):
        user = UserFactory()
        data = {"first_name": "Updated"}
        response = authenticated_client.patch(f"/api/users/{user.id}/update/", data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"


@pytest.mark.django_db
class TestUserDeactivateApi:
    def test_deactivates_user(self, authenticated_client):
        user = UserFactory(is_active=True)
        response = authenticated_client.post(f"/api/users/{user.id}/deactivate/")

        assert response.status_code == status.HTTP_200_OK

    def test_raises_for_already_deactivated(self, authenticated_client):
        user = UserFactory(is_active=False)
        response = authenticated_client.post(f"/api/users/{user.id}/deactivate/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
