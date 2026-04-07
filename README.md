# Project Name

> Short project description.

## Stack

- Python 3.14 / Django 6.0 / DRF 3.17
- PostgreSQL 17 / Redis 7
- django.tasks (lightweight) + Celery + Beat (heavy/periodic)
- Docker Compose

## Quick Start

```bash
make init
```

This copies `.env.example` to `.env`, builds containers, starts services, and runs migrations.

Visit http://localhost:8000/api/schema/swagger/ for API docs.

### Create a superuser

```bash
make createsuperuser
```

## Development

```bash
make up              # start all services (attached)
make up-d            # start all services (detached)
make down            # stop all services
make logs            # tail logs
```

### Django commands

```bash
make migrate         # run migrations
make makemigrations  # create new migrations
make shell           # Django shell_plus
make bash            # bash inside backend container
make dbshell         # PostgreSQL shell
```

### Tests

```bash
make testing              # all: unit+integration parallel, then e2e sequential
make testing-unit         # unit only (no DB) — parallel
make testing-integration  # integration only (with DB) — parallel
make testing-e2e          # e2e only — sequential
make testing-cov          # all tests with coverage
```

### Code quality

```bash
make lint            # ruff check + format check
make lint-fix        # ruff check --fix + format
```

### OpenAPI schema

```bash
make schema          # generate schema.yml
```

Run `make help` to see all available commands.

## Project Structure

```
src/
├── main/              # Django project config
│   ├── settings/      # Modular settings (base, tasks, celery, caches, etc.)
│   ├── urls.py        # Root URL config
│   ├── celery.py      # Celery app (heavy/periodic tasks)
│   └── wsgi.py / asgi.py
│
├── core/              # Shared base classes
│   ├── models.py      # BaseModel (created_at, updated_at)
│   └── exceptions.py  # ApplicationError
│
├── api/               # API infrastructure
│   ├── exception_handlers.py  # Normalized {message, extra} errors
│   ├── mixins.py              # ApiAuthMixin (Session + Token)
│   ├── pagination.py          # LimitOffset + page-based variants
│   └── utils.py               # get_paginated_response, inline_serializer
│
├── utils/             # Reusable utilities
│   ├── serializers.py # DynamicModelSerializer (?fields=, ?expand=)
│   ├── services.py    # model_update()
│   ├── managers.py    # ActiveManager, CustomQuerySet
│   ├── cache.py       # cache_viewset_list, invalidate_cache_pattern
│   ├── filters.py     # AccentInsensitiveSearchFilter
│   └── tasks.py       # enqueue_on_commit, ResilientTask, task_on_commit
│
└── users/             # Example app (demonstrates all patterns)
    ├── models.py      # Custom User (email-based)
    ├── services.py    # user_create, user_update, user_deactivate
    ├── selectors.py   # user_list, user_get
    ├── apis.py        # HackSoft-style APIViews
    ├── filters.py     # UserFilter (django-filter)
    ├── tasks.py       # send_welcome_email (django.tasks)
    ├── factories.py   # UserFactory (factory_boy)
    └── tests/         # test_models, test_services, test_selectors, test_apis

docs/
├── specs/             # Business rules (source of truth for tests)
└── technical/         # Architecture, API, deployment, testing docs
```

## Architecture

Follows the [HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide):

- **Specs** — Business rules in `docs/specs/`, enforced by tests
- **Services** — `<entity>_<action>()`, `@transaction.atomic`, `full_clean()` before save
- **Selectors** — `<entity>_<action>()`, return QuerySet or Optional[Model]
- **APIs** — One APIView per operation, nested Input/Output serializers, delegate to services/selectors
- **Errors** — All exceptions normalized to `{"message": "...", "extra": {"fields": {...}}}`

## Background Tasks

| System | Use for |
|---|---|
| **django.tasks** | Lightweight async: emails, notifications, webhooks |
| **Celery** | Heavy computation, periodic/cron, complex retry |

## Environment Variables

See [`.env.example`](.env.example) for all available variables.

## Docker Services

| Service        | Port  | Description                |
| -------------- | ----- | -------------------------- |
| backend        | 8000  | Django dev server          |
| celeryworker   | —     | Celery worker (heavy tasks)|
| celerybeat     | —     | Celery beat (periodic)     |
| flower         | 5555  | Celery monitoring          |
| postgres       | 5432  | PostgreSQL 17              |
| redis          | 6379  | Redis 7                    |

## Production

```bash
docker compose -f docker-compose.prod.yml up -d
```

Uses Gunicorn, WhiteNoise for static files, resource limits, and no volume mounts.
