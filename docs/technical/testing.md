# Testing

## Setup

Tests use **pytest** with **pytest-django**, **pytest-xdist** (parallel), and **factory_boy**. Configuration lives in `pyproject.toml`.

## Running Tests

```bash
make testing                # all: unit+integration parallel, then e2e sequential
make testing-unit           # unit only (no DB, no Redis) — parallel
make testing-integration    # integration only (with DB + Redis) — parallel
make testing-e2e            # e2e only — sequential (shared fixtures)
make testing-cov            # all tests with coverage report
```

Or directly inside the container:

```bash
pytest                                  # all tests
pytest src/users/tests/                 # single app
pytest -k test_creates_user             # by name
pytest -m unit -n auto                  # unit, parallel
pytest -m integration -n auto           # integration, parallel
pytest -m e2e                           # e2e, sequential
pytest --cov --cov-report=term          # with coverage
```

## Markers

Defined in `pyproject.toml`. Use `--strict-markers` to fail on unknown markers.

| Marker | Purpose | DB | Parallel |
|---|---|---|---|
| `@pytest.mark.unit` | No DB, no Redis — fast | No | Yes (`-n auto`) |
| `@pytest.mark.integration` | Requires DB + Redis | `@pytest.mark.django_db` | Yes (`-n auto`) |
| `@pytest.mark.e2e` | Full request/response cycle | `@pytest.mark.django_db` | No (sequential) |

```python
@pytest.mark.unit
def test_email_format():
    ...

@pytest.mark.integration
@pytest.mark.django_db
def test_user_create():
    ...

@pytest.mark.e2e
@pytest.mark.django_db
class TestUserCreateApi:
    ...
```

## Spec-Driven Testing

Business rules live in `docs/specs/<app>.md`. Each rule has a **Rule ID** and a reference to the test that enforces it. The workflow:

1. **Document the rule** in `docs/specs/` with stakeholders or from client requirements.
2. **Write the test** that enforces the rule (reference the Rule ID in a comment if helpful).
3. **Implement the code** to make the test pass.

Example from `docs/specs/users.md`:

| Rule ID | Rule | Tested in |
|---------|------|-----------|
| USR-DEACT-02 | Deactivating an already-deactivated user raises `ApplicationError` | `test_services::test_raises_if_already_deactivated` |

This ensures every business requirement is traceable from spec to test to implementation.

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

## xdist Worker Isolation

When running tests in parallel with `-n auto`, each xdist worker gets its own Redis database to prevent key collisions. This is handled automatically by the root `conftest.py`.

## Patterns by Layer

### Unit Tests — No DB, No Network

```python
@pytest.mark.unit
class TestUserFullName:
    def test_full_name(self):
        user = User(first_name="John", last_name="Doe")
        assert user.full_name == "John Doe"
```

### Integration Tests — Require DB

```python
@pytest.mark.integration
@pytest.mark.django_db
class TestUserCreate:
    def test_creates_user(self):
        with patch("users.services.enqueue_on_commit"):
            user = user_create(email="new@example.com", password="testpass123")
        assert user.email == "new@example.com"
```

### E2E Tests — Full Request/Response Cycle

```python
@pytest.mark.e2e
@pytest.mark.django_db
class TestUserCreateApi:
    @patch("users.services.enqueue_on_commit")
    def test_creates_user(self, mock_task, authenticated_client):
        data = {"email": "new@example.com", "password": "securepass123"}
        response = authenticated_client.post("/api/users/create/", data)
        assert response.status_code == status.HTTP_201_CREATED
```

### Testing Tasks

Call the task function directly — don't go through the broker:

```python
@pytest.mark.integration
@pytest.mark.django_db
def test_send_welcome_email():
    user = UserFactory()
    send_welcome_email(user_id=user.id)
```

When testing services that dispatch tasks, mock `enqueue_on_commit`:

```python
with patch("users.services.enqueue_on_commit"):
    user = user_create(email="test@example.com", password="testpass123")
```

## Factories

Factories use [factory_boy](https://factoryboy.readthedocs.io/):

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
