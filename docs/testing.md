# Testing

## Setup

Tests use **pytest** with **pytest-django** and **factory_boy**. Configuration is split across two files:

- `pyproject.toml` — pytest options, markers, coverage settings
- `src/pytest.ini` — duplicate config for IDE compatibility (same values)

## Running Tests

```bash
make test            # run all tests
make test-cov        # run tests with coverage report

# Or directly inside the container:
pytest                              # all tests
pytest src/users/tests/             # single app
pytest -k test_creates_user         # by name
pytest -m unit                      # by marker
pytest -m "not slow"                # exclude slow tests
pytest --cov --cov-report=term      # with coverage
```

## Markers

Defined in `pyproject.toml`:

| Marker | Purpose |
|---|---|
| `@pytest.mark.unit` | Fast, no DB or network |
| `@pytest.mark.integration` | Requires DB (use with `@pytest.mark.django_db`) |
| `@pytest.mark.e2e` | Full request/response cycle |
| `@pytest.mark.slow` | Long-running tests |

```python
@pytest.mark.unit
def test_email_format():
    ...

@pytest.mark.integration
@pytest.mark.django_db
def test_user_create():
    ...
```

## Shared Fixtures

Defined in `src/conftest.py`, available to all test files:

```python
@pytest.fixture
def api_client():
    """Unauthenticated DRF test client."""
    return APIClient()

@pytest.fixture
def user_factory():
    """Returns the UserFactory class for creating users in tests."""
    return UserFactory

@pytest.fixture
def authenticated_client():
    """DRF test client with a pre-authenticated user."""
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return client
```

<!-- TODO: Add project-specific fixtures (e.g. authenticated_admin_client, sample data fixtures). -->

## Patterns by Layer

### Unit Tests — No DB, No Network

Unit tests mock all external dependencies and run entirely in memory. Mark them with `@pytest.mark.unit`.

**Testing model properties and logic (no DB needed):**

```python
@pytest.mark.unit
class TestUserFullName:
    def test_full_name(self):
        user = User(first_name="John", last_name="Doe")
        assert user.full_name == "John Doe"

    def test_full_name_empty(self):
        user = User()
        assert user.full_name == ""
```

**Testing services with mocked ORM:**

```python
@pytest.mark.unit
class TestUserDeactivateLogic:
    def test_raises_if_already_deactivated(self):
        user = User(is_active=False)
        with pytest.raises(ApplicationError, match="already deactivated"):
            user_deactivate(user=user)
```

**Testing utility functions:**

```python
@pytest.mark.unit
class TestTaskOnCommit:
    def test_schedules_task_after_commit(self):
        mock_task = Mock()
        with patch("utils.tasks.transaction") as mock_tx:
            task_on_commit(mock_task, user_id=1)
            mock_tx.on_commit.assert_called_once()
```

### Integration Tests — Require DB

Integration tests hit the real database. Mark them with `@pytest.mark.integration` and `@pytest.mark.django_db`.

**Testing models (creation, constraints, persistence):**

```python
@pytest.mark.integration
@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        assert user.email == "test@example.com"
        assert user.is_active is True

    def test_str_returns_email(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        assert str(user) == "test@example.com"

    def test_has_timestamps(self):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        assert user.created_at is not None
        assert user.updated_at is not None
```

**Testing services (real DB writes):**

```python
@pytest.mark.integration
@pytest.mark.django_db
class TestUserCreate:
    def test_creates_user(self):
        with patch("users.services.task_on_commit"):
            user = user_create(email="new@example.com", password="testpass123")

        assert user.email == "new@example.com"
        assert user.is_active is True
        assert User.objects.filter(email="new@example.com").exists()
```

**Testing selectors (filtering, queries):**

```python
@pytest.mark.integration
@pytest.mark.django_db
class TestUserList:
    def test_filters_by_is_active(self):
        UserFactory.create_batch(2, is_active=True)
        UserFactory.create_batch(1, is_active=False)

        active = user_list(filters={"is_active": True})
        assert active.count() == 2

class TestUserGet:
    def test_returns_none_for_missing_user(self):
        result = user_get(user_id=99999)
        assert result is None
```

### E2E Tests — Full Request/Response Cycle

E2E tests exercise the full stack: URL routing, authentication, serialization, services, and DB. Mark them with `@pytest.mark.e2e` and `@pytest.mark.django_db`.

```python
@pytest.mark.e2e
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
        assert "results" in response.data

@pytest.mark.e2e
@pytest.mark.django_db
class TestUserCreateApi:
    @patch("users.services.task_on_commit")
    def test_creates_user(self, mock_task, authenticated_client):
        data = {"email": "new@example.com", "password": "securepass123"}
        response = authenticated_client.post("/api/users/create/", data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "new@example.com"

    def test_validates_input(self, authenticated_client):
        response = authenticated_client.post("/api/users/create/", {"email": "invalid", "password": "short"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "message" in response.data
```

### Testing Celery Tasks

Call the task function directly (don't go through the broker):

```python
@pytest.mark.integration
@pytest.mark.django_db
def test_send_welcome_email():
    user = UserFactory()
    # Call the underlying function, not .delay()
    send_welcome_email(user_id=user.id)
```

When testing services that dispatch tasks, mock `task_on_commit`:

```python
with patch("users.services.task_on_commit"):
    user = user_create(email="test@example.com", password="testpass123")
```

## Factories

Factories use [factory_boy](https://factoryboy.readthedocs.io/). Key features:

```python
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")   # unique per test
    first_name = factory.Faker("first_name")                      # random realistic data
    password = factory.django.Password("testpass123")              # hashed password
    is_active = True

    class Params:
        admin = factory.Trait(          # UserFactory(admin=True) for superusers
            is_staff=True,
            is_superuser=True,
        )
```

Common patterns:

```python
user = UserFactory()                          # single instance
users = UserFactory.create_batch(5)           # multiple instances
admin = UserFactory(admin=True)               # using a Trait
data = UserFactory.build()                    # in-memory only (no DB)
```

## Coverage

Configuration in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
omit = ["*/migrations/*", "*/tests/*", "*/conftest.py", "manage.py"]

[tool.coverage.report]
show_missing = true
skip_covered = true
fail_under = 80
```

The coverage threshold is **80%**. CI will fail if coverage drops below this.

<!-- TODO: Adjust fail_under threshold if your project requires higher coverage. -->
