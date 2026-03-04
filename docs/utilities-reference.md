# Utilities Reference

Quick reference for all built-in utilities. Each entry includes the source file, purpose, and usage example.

## Core (`src/core/`)

### BaseModel

**Source:** `src/core/models.py`

Abstract model providing `created_at` and `updated_at` timestamps. All app models should extend this.

```python
from core.models import BaseModel

class Order(BaseModel):
    total = models.DecimalField(max_digits=10, decimal_places=2)
    # Inherits: created_at (DateTimeField, db_index=True, default=timezone.now)
    #           updated_at (DateTimeField, auto_now=True)
```

### ApplicationError

**Source:** `src/core/exceptions.py`

Custom exception for business logic errors. Caught by the custom exception handler and returned as `{"message": "...", "extra": {...}}` with status 400.

```python
from core.exceptions import ApplicationError

raise ApplicationError("User is already deactivated.")
raise ApplicationError("Insufficient balance.", extra={"balance": "10.00", "required": "25.00"})
```

## API (`src/api/`)

### ApiAuthMixin

**Source:** `src/api/mixins.py`

Mixin for API views that require authentication. Provides Session + Token auth.

```python
from api.mixins import ApiAuthMixin

class MyApi(ApiAuthMixin, APIView):
    def get(self, request):
        ...
```

### custom_exception_handler

**Source:** `src/api/exception_handlers.py`

Registered as `REST_FRAMEWORK["EXCEPTION_HANDLER"]`. Normalizes all errors to `{"message": "...", "extra": {...}}`. Handles `ApplicationError`, Django `ValidationError`, and all DRF exceptions.

### get_paginated_response

**Source:** `src/api/utils.py`

```python
get_paginated_response(
    *,
    pagination_class=None,   # defaults to LimitOffsetPagination
    serializer_class,
    queryset,
    request,
    view,
)
```

Paginates a queryset and returns a DRF `Response`. Use in API view `get()` methods:

```python
return get_paginated_response(
    pagination_class=LimitOffsetPagination,
    serializer_class=self.OutputSerializer,
    queryset=users,
    request=request,
    view=self,
)
```

### inline_serializer

**Source:** `src/api/utils.py`

Creates a one-off serializer class without defining a full class:

```python
from api.utils import inline_serializer

serializer = inline_serializer(fields={
    "email": serializers.EmailField(),
    "is_active": serializers.BooleanField(),
})
```

### Pagination Classes

**Source:** `src/api/pagination.py`

| Class | Type | Default | Max | Query Params |
|---|---|---|---|---|
| `LimitOffsetPagination` | Limit/Offset | 50 | 100 | `?limit=&offset=` |
| `SmallPagePagination` | Page Number | 10 | 50 | `?page=&page_size=` |
| `MediumPagePagination` | Page Number | 25 | 100 | `?page=&page_size=` |
| `LargePagePagination` | Page Number | 50 | 200 | `?page=&page_size=` |

## Utils (`src/utils/`)

### model_update

**Source:** `src/utils/services.py`

```python
model_update(
    *,
    instance: models.Model,
    fields: list[str],       # allowed fields to update
    data: dict,              # submitted data
) -> tuple[Model, bool]     # (instance, has_updated)
```

Generic update following the HackSoft pattern. Only updates fields present in both `fields` and `data`. Handles M2M fields, runs `full_clean()`, and uses `update_fields` for efficient writes.

```python
from utils.services import model_update

user, has_updated = model_update(
    instance=user,
    fields=["first_name", "last_name"],
    data={"first_name": "John"},
)
```

### DynamicModelSerializer

**Source:** `src/utils/serializers.py`

ModelSerializer that supports dynamic field selection via query parameters:

- `?fields=id,email` — only return specified fields
- `?expand=profile` — include nested serializer fields

```python
from utils.serializers import DynamicModelSerializer

class UserSerializer(DynamicModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        expandable_fields = {
            "profile": (ProfileSerializer, {}),
        }
```

### ActiveManager

**Source:** `src/utils/managers.py`

Manager that returns only active records (`is_active=True`) by default. Also provides a `CustomQuerySet` with `.active()` and `.inactive()` chainable methods.

```python
from utils.managers import ActiveManager

class Product(BaseModel):
    is_active = models.BooleanField(default=True)

    objects = ActiveManager()       # Product.objects.all() returns only active
    all_objects = models.Manager()  # Product.all_objects.all() returns everything
```

### cache_viewset_list

**Source:** `src/utils/cache.py`

Decorator for caching view list actions. Generates a cache key from the request path and query params.

```python
from utils.cache import cache_viewset_list

@cache_viewset_list(timeout=300, key_prefix="users")
def list(self, request, *args, **kwargs):
    ...
```

### invalidate_cache_pattern

**Source:** `src/utils/cache.py`

Invalidates all cache keys matching a pattern. Requires a cache backend that supports `delete_pattern` (e.g., django-redis).

```python
from utils.cache import invalidate_cache_pattern

invalidate_cache_pattern("users:*")
```

### AccentInsensitiveSearchFilter

**Source:** `src/utils/filters.py`

DRF search filter that ignores accents/diacritics using PostgreSQL's `unaccent` extension.

```python
from utils.filters import AccentInsensitiveSearchFilter

class MyView(APIView):
    filter_backends = [AccentInsensitiveSearchFilter]
    search_fields = ["name", "email"]
```

Requires: `CREATE EXTENSION IF NOT EXISTS unaccent;` in PostgreSQL.

### ResilientTask

**Source:** `src/utils/tasks.py`

Celery task base class with automatic retry, exponential backoff, jitter, and admin email on final failure.

```python
from celery import shared_task
from utils.tasks import ResilientTask

@shared_task(base=ResilientTask, bind=True, max_retries=3)
def my_task(self, *, some_id: int):
    ...
```

Configuration: `autoretry_for=(Exception,)`, `retry_backoff=True`, `retry_backoff_max=600`, `retry_jitter=True`.

### task_on_commit

**Source:** `src/utils/tasks.py`

Schedules a Celery task to run after the current DB transaction commits.

```python
from utils.tasks import task_on_commit

@transaction.atomic
def my_service():
    obj = MyModel.objects.create(...)
    task_on_commit(process_object, object_id=obj.id)
```

<!-- TODO: Add documentation for any new utilities as they are created. -->
