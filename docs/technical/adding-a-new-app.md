# Adding a New App

This guide walks through creating a new Django app that follows all project conventions. The `users/` app is the reference implementation — every pattern shown here is already demonstrated there.

## Step-by-Step

### 1. Create the App

```bash
# Inside the backend container
cd /app
python manage.py startapp orders
```

### 2. Set Up the File Structure

Replace the generated files to match the project layout:

```
src/orders/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── services.py       # create this
├── selectors.py      # create this
├── apis.py           # create this
├── urls.py           # create this
├── filters.py        # create this
├── factories.py      # create this
├── tasks.py          # create this (if needed)
└── tests/
    ├── __init__.py
    ├── test_unit.py
    ├── test_models.py
    ├── test_services.py
    ├── test_selectors.py
    └── test_apis.py
```

Delete the generated `views.py` and `tests.py` files — this project uses `apis.py` and a `tests/` directory.

### 3. Register in INSTALLED_APPS

Add the app to `src/main/settings/base.py`:

```python
INSTALLED_APPS = [
    ...
    # Local
    "core.apps.CoreConfig",
    "api.apps.ApiConfig",
    "utils.apps.UtilsConfig",
    "users.apps.UsersConfig",
    "orders.apps.OrdersConfig",  # <- add here
]
```

### 4. Define the Model

Extend `BaseModel` to get `created_at` and `updated_at`:

```python
# src/orders/models.py
from django.db import models
from core.models import BaseModel

class Order(BaseModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="orders")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id}"
```

Then create and run migrations:

```bash
python manage.py makemigrations orders
python manage.py migrate
```

### 5. Write Services

Service functions handle all write operations. Always use `@transaction.atomic` and keyword-only arguments:

```python
# src/orders/services.py
from django.db import transaction
from orders.models import Order

@transaction.atomic
def order_create(*, user, total: Decimal) -> Order:
    order = Order(user=user, total=total)
    order.full_clean()
    order.save()
    return order

@transaction.atomic
def order_update(*, order: Order, data: dict) -> Order:
    from utils.services import model_update
    order, _has_updated = model_update(instance=order, fields=["status"], data=data)
    return order
```

### 6. Write Selectors

Selectors handle all read operations. Return querysets for list operations:

```python
# src/orders/selectors.py
from django.db.models import QuerySet
from orders.filters import OrderFilter
from orders.models import Order

def order_list(*, filters: dict | None = None) -> QuerySet[Order]:
    filters = filters or {}
    qs = Order.objects.all()
    return OrderFilter(filters, qs).qs

def order_get(*, order_id: int) -> Order | None:
    return Order.objects.filter(id=order_id).first()
```

### 7. Define Filters

```python
# src/orders/filters.py
import django_filters
from orders.models import Order

class OrderFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(lookup_expr="exact")

    class Meta:
        model = Order
        fields = ["status"]
```

### 8. Build APIs

One `APIView` per operation. Use nested `InputSerializer` / `OutputSerializer` / `FilterSerializer`:

```python
# src/orders/apis.py
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.mixins import ApiAuthMixin
from api.pagination import LimitOffsetPagination
from api.utils import get_paginated_response
from orders.selectors import order_list
from orders.services import order_create

class OrderListApi(ApiAuthMixin, APIView):
    class FilterSerializer(serializers.Serializer):
        status = serializers.CharField(required=False)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Order
            fields = ("id", "user_id", "total", "status", "created_at")

    def get(self, request):
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        orders = order_list(filters=filter_serializer.validated_data)
        return get_paginated_response(
            pagination_class=LimitOffsetPagination,
            serializer_class=self.OutputSerializer,
            queryset=orders,
            request=request,
            view=self,
        )

class OrderCreateApi(ApiAuthMixin, APIView):
    class InputSerializer(serializers.Serializer):
        total = serializers.DecimalField(max_digits=10, decimal_places=2)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Order
            fields = ("id", "total", "status", "created_at")

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = order_create(user=request.user, **serializer.validated_data)
        return Response(self.OutputSerializer(order).data, status=status.HTTP_201_CREATED)
```

### 9. Wire URLs

```python
# src/orders/urls.py
from django.urls import path
from orders.apis import OrderCreateApi, OrderListApi

urlpatterns = [
    path("", OrderListApi.as_view(), name="order-list"),
    path("create/", OrderCreateApi.as_view(), name="order-create"),
]
```

Register in the API router:

```python
# src/api/urls.py
urlpatterns = [
    path("users/", include("users.urls")),
    path("orders/", include("orders.urls")),  # <- add here
]
```

### 10. Create Factories

```python
# src/orders/factories.py
import factory
from orders.models import Order
from users.factories import UserFactory

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    total = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    status = "pending"
```

### 11. Write Tests

Follow the pattern in `src/users/tests/`:

- `test_unit.py` — pure logic that needs no DB: model properties, error classes, helper functions (`@pytest.mark.unit`)
- `test_models.py` — model creation, constraints, managers (`@pytest.mark.integration`)
- `test_services.py` — business logic, side effects; mock `enqueue_on_commit` or `task_on_commit` (`@pytest.mark.integration`)
- `test_selectors.py` — filtering, retrieval, edge cases (`@pytest.mark.integration`)
- `test_apis.py` — auth, status codes, response shape (`@pytest.mark.e2e`)

## Checklist

- [ ] Business rules documented in `docs/specs/<app>.md`
- [ ] App created and registered in `INSTALLED_APPS`
- [ ] Model extends `BaseModel`, migrations created
- [ ] Services in `services.py` — `@transaction.atomic`, `full_clean()`
- [ ] Selectors in `selectors.py` — return `QuerySet` or `Optional[Model]`
- [ ] FilterSet in `filters.py`
- [ ] APIs in `apis.py` — one `APIView` per operation, nested serializers
- [ ] URLs in `urls.py`, included in `api/urls.py`
- [ ] Factory in `factories.py`
- [ ] Tests in `tests/` — models, services, selectors, APIs (with proper markers)
- [ ] Admin registered in `admin.py`
