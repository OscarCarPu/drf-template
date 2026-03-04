# Celery Tasks

## Infrastructure

| Component | Technology | Purpose |
|---|---|---|
| Broker | Redis (`redis://redis:6379/1`) | Message transport |
| Result backend | `django-db` | Store task results in PostgreSQL |
| Scheduler | `django-celery-beat` (`DatabaseScheduler`) | Periodic tasks via Django admin |
| Monitoring | Flower (port 5555) | Web-based task monitor |

Configuration: `src/main/settings/celery.py`

```python
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TIME_LIMIT = 30 * 60      # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
```

Celery app: `src/main/celery.py`

```python
app = Celery("main")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

## Writing Tasks with ResilientTask

`ResilientTask` (`src/utils/tasks.py`) is the base class for all tasks. It provides:

- **Automatic retry** on any exception
- **Exponential backoff** with jitter (max 10 minutes between retries)
- **Admin email notification** on final failure (in non-DEBUG mode)

```python
# src/users/tasks.py
from celery import shared_task
from utils.tasks import ResilientTask

@shared_task(base=ResilientTask, bind=True, max_retries=3)
def send_welcome_email(self, *, user_id: int):
    from users.models import User
    user = User.objects.get(id=user_id)

    send_mail(
        subject="Welcome!",
        message=f"Hi {user.first_name or user.email}, welcome!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
```

Key points:

- Always use `base=ResilientTask` and `bind=True`.
- Pass IDs (not model instances) as arguments — tasks are serialized as JSON.
- Import models inside the task function to avoid circular imports.

## Dispatching Tasks with task_on_commit

Use `task_on_commit()` (`src/utils/tasks.py`) to schedule a task **after the current database transaction commits**. This prevents tasks from running with data that hasn't been committed yet.

```python
# src/users/services.py
from utils.tasks import task_on_commit

@transaction.atomic
def user_create(*, email: str, password: str, ...) -> User:
    user = User.objects.create_user(email=email, password=password, ...)
    task_on_commit(send_welcome_email, user_id=user.id)
    return user
```

How it works:

```python
def task_on_commit(task, *args, **kwargs):
    transaction.on_commit(lambda: task.delay(*args, **kwargs))
```

If the transaction rolls back, the task is never dispatched.

## Periodic Tasks

Periodic tasks are managed through **django-celery-beat** and the Django admin interface.

1. Go to Django Admin → Periodic Tasks.
2. Create a new periodic task, selecting the registered task and a schedule (interval, crontab, etc.).

The beat scheduler reads from the database, so no code changes are needed to add/modify schedules.

## Docker Services

All Celery services are defined in `docker-compose.yml`:

| Service | Command | Port |
|---|---|---|
| `celeryworker` | `celery-worker` | — |
| `celerybeat` | `celery-beat` | — |
| `flower` | `celery-flower` | 5555 |

The entrypoint script (`docker/entrypoint.sh`) handles each command:

```bash
# Worker
celery -A main.celery worker -l INFO -Ofair --concurrency=2

# Beat
celery -A main.celery beat -l INFO --pidfile=/tmp/celerybeat.pid

# Flower
celery -A main.celery flower --port=5555
```

Environment variables for tuning:

| Variable | Default | Description |
|---|---|---|
| `CELERY_LOG_LEVEL` | `INFO` | Worker/beat log level |
| `CELERY_CONCURRENCY` | `2` | Number of worker processes |
| `FLOWER_PORT` | `5555` | Flower web UI port |

## Accessing Flower

In development: http://localhost:5555

<!-- TODO: Configure Flower authentication for production (--basic-auth or reverse proxy). -->

## Testing Tasks

Call the task function directly in tests — don't go through the broker:

```python
@pytest.mark.django_db
def test_send_welcome_email():
    user = UserFactory()
    send_welcome_email(user_id=user.id)
```

When testing services that dispatch tasks, mock `task_on_commit`:

```python
with patch("users.services.task_on_commit"):
    user = user_create(email="test@example.com", password="testpass123")
```
