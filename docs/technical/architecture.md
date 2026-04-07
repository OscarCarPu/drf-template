# Architecture

This project follows the [HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide), which enforces a clear separation between data, business logic, read operations, and API interfaces.

## Spec-Driven Development

Business rules are documented in `docs/specs/<app>.md` before implementation. Each rule gets a **Rule ID** and must be enforced by at least one test. The workflow:

1. **Spec** — Document the rule with stakeholders (e.g. `USR-DEACT-02`).
2. **Test** — Write a failing test that enforces the rule.
3. **Code** — Implement until the test passes.

This ensures every business requirement is traceable: spec → test → implementation.

## Layer Responsibilities

### Models — Data Only

Models define fields, constraints, and database-level behaviour. They must **not** contain business logic.

- Extend `BaseModel` (from `core/models.py`) to get `created_at` and `updated_at` timestamps.
- Keep custom managers for generic queryset helpers (e.g. `ActiveManager`).
- Use `full_clean()` in the manager's `create_*` methods so validation always runs.

```python
# src/core/models.py
class BaseModel(models.Model):
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

### Services — Write Operations

Every state-changing operation lives in a service function: `<entity>_<action>()`.

Rules:

1. Wrap the function with `@transaction.atomic`.
2. Call `full_clean()` before saving (the `model_update` utility does this automatically).
3. Accept keyword-only arguments — never pass a request object.
4. Dispatch async work through `enqueue_on_commit()` (django.tasks) or `task_on_commit()` (Celery).

```python
# src/users/services.py
@transaction.atomic
def user_create(*, email: str, password: str, ...) -> User:
    user = User.objects.create_user(email=email, password=password, ...)
    enqueue_on_commit(send_welcome_email, user_id=user.id)
    return user
```

### Selectors — Read Operations

Selectors return `QuerySet` or `Optional[Model]`. They are the only place where database reads are composed.

- Use `django-filter` `FilterSet` classes to encapsulate filtering logic.
- Return querysets (not lists) so pagination can be applied lazily in the API layer.

```python
# src/users/selectors.py
def user_list(*, filters: dict | None = None) -> QuerySet[User]:
    filters = filters or {}
    qs = User.objects.all()
    return UserFilter(filters, qs).qs

def user_get(*, user_id: int) -> User | None:
    return User.objects.filter(id=user_id).first()
```

### APIs — One View per Operation

Each API endpoint is a single `APIView` class. Input validation uses a nested `InputSerializer`; output shaping uses a nested `OutputSerializer`. The view delegates to services/selectors — it never touches the ORM directly.

```python
# src/users/apis.py (simplified)
class UserCreateApi(ApiAuthMixin, APIView):
    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField(min_length=8)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ("id", "email", "first_name", "last_name", "is_active", "created_at")

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = user_create(**serializer.validated_data)
        return Response(self.OutputSerializer(user).data, status=201)
```

## Background Tasks

Two systems with clear separation:

| System | Use for |
|---|---|
| **django.tasks** | Lightweight async: emails, notifications, webhooks |
| **Celery** | Heavy computation, periodic/cron, complex retry |

See [Background Tasks](celery-tasks.md) for details.

## Error Flow

All exceptions are normalized to a single JSON shape by `custom_exception_handler`:

```
raise ApplicationError("User is already deactivated.")
        │
        ▼
custom_exception_handler(exc, ctx)
        │
        ▼
Response({"message": "User is already deactivated.", "extra": {}}, status=400)
```

| Source | Conversion |
|---|---|
| `ApplicationError(message, extra)` | `400` with `{message, extra}` |
| Django `ValidationError` | Converted to DRF `ValidationError`, then normalized |
| Any DRF exception | Field errors → `{message: "Validation error.", extra: {fields: {...}}}` |

## App Boundaries

- Apps communicate **only** through each other's services and selectors — never import another app's models directly for writes.
- Each app owns its own `services.py`, `selectors.py`, `apis.py`, `urls.py`, `filters.py`, `factories.py`, and `tests/` directory.
- Shared infrastructure lives in `core/` (base classes, exceptions) and `utils/` (reusable helpers).

## Directory Map

```
src/
├── core/       # BaseModel, ApplicationError
├── api/        # Exception handler, auth mixin, pagination, inline_serializer
├── utils/      # model_update, DynamicModelSerializer, ActiveManager, cache, tasks
├── users/      # Reference implementation of all patterns
└── main/       # Django project config, settings, celery, urls

docs/
├── specs/      # Business rules (source of truth, tested against)
├── technical/  # Architecture, API, deployment, testing docs
└── README.md   # Documentation index
```
