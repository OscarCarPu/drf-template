# Background Tasks

This project uses **two task systems** with clear separation of concerns:

| System | Use for | Examples |
|---|---|---|
| **django.tasks** | Lightweight, fire-and-forget async work | Emails, notifications, webhooks, cache warming |
| **Celery** | Heavy computation, periodic/cron, complex retry | Reports, data exports, scheduled jobs, ETL |

## django.tasks — Lightweight Tasks

### Configuration

Settings: `src/main/settings/tasks.py`

```python
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
    }
}
```

`ImmediateBackend` runs tasks synchronously in the same process — no separate worker needed.

### Writing Tasks

```python
# src/users/tasks.py
from django.tasks import task

@task()
def send_welcome_email(*, user_id: int):
    from django.core.mail import send_mail
    from users.models import User

    user = User.objects.get(id=user_id)
    send_mail(
        subject="Welcome!",
        message=f"Hi {user.first_name or user.email}, welcome!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
```

### Dispatching Tasks

Use `enqueue_on_commit()` to dispatch after the DB transaction commits:

```python
# src/users/services.py
from utils.tasks import enqueue_on_commit

@transaction.atomic
def user_create(*, email: str, password: str, ...) -> User:
    user = User.objects.create_user(...)
    enqueue_on_commit(send_welcome_email, user_id=user.id)
    return user
```

How it works:

```python
def enqueue_on_commit(task_func, **kwargs):
    transaction.on_commit(lambda: task_func.enqueue(**kwargs))
```

If the transaction rolls back, the task is never dispatched.

## Celery — Heavy / Periodic Tasks

### Configuration

Settings: `src/main/settings/celery.py`

```python
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_TIME_LIMIT = 30 * 60      # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
```

Celery app: `src/main/celery.py`

### Writing Tasks with ResilientTask

`ResilientTask` (`src/utils/tasks.py`) provides automatic retry with exponential backoff:

```python
from celery import shared_task
from utils.tasks import ResilientTask

@shared_task(base=ResilientTask, bind=True, max_retries=3)
def generate_monthly_report(self, *, report_id: int):
    # Heavy computation that benefits from Celery's retry logic
    ...
```

### Dispatching Celery Tasks

Use `task_on_commit()` for Celery tasks:

```python
from utils.tasks import task_on_commit

@transaction.atomic
def report_create(...):
    report = Report.objects.create(...)
    task_on_commit(generate_monthly_report, report_id=report.id)
    return report
```

### Periodic Tasks

Managed through **django-celery-beat** and the Django admin:

1. Go to Django Admin → Periodic Tasks.
2. Create a new periodic task, selecting the registered task and a schedule.

## Docker Services

| Service | System | Command | Port |
|---|---|---|---|
| `celeryworker` | Celery | `celery-worker` | — |
| `celerybeat` | Celery | `celery-beat` | — |
| `flower` | Celery | `celery-flower` | 5555 |

## Testing Tasks

Call the task function directly — don't go through the broker:

```python
@pytest.mark.integration
@pytest.mark.django_db
def test_send_welcome_email():
    user = UserFactory()
    send_welcome_email(user_id=user.id)
```

When testing services that dispatch tasks, mock `enqueue_on_commit` or `task_on_commit`:

```python
# For django.tasks
with patch("users.services.enqueue_on_commit"):
    user = user_create(email="test@example.com", password="testpass123")

# For Celery tasks
with patch("reports.services.task_on_commit"):
    report = report_create(...)
```

## When to Use Which

| Criteria | django.tasks | Celery |
|---|---|---|
| Email sending | ✓ | |
| Push notifications | ✓ | |
| Webhook delivery | ✓ | |
| Cache warming | ✓ | |
| Data export / ETL | | ✓ |
| Report generation | | ✓ |
| Periodic/cron schedule | | ✓ |
| Complex retry with backoff | | ✓ |
| Long-running (>5 min) | | ✓ |
