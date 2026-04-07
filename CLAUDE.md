# CLAUDE.md

## Project Overview

Django REST Framework API template following the [HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide). The `users/` app is the **reference implementation** — every pattern is demonstrated there.

## Spec-First Workflow

**Always follow this order when implementing features:**

1. **Spec** — Write business rules in `docs/specs/<app>.md` using the Rule ID format (`APP-ACTION-NN`). Copy `docs/specs/_TEMPLATE.md` as a starting point.
2. **Test** — Write failing tests that enforce each rule. Reference the Rule ID.
3. **Code** — Implement until tests pass.

Every business requirement must be traceable: spec -> test -> implementation.

## Architecture (HackSoft Styleguide)

Each app follows this structure:

```
src/<app>/
├── models.py       # Data only — extend BaseModel, no business logic
├── services.py     # Write operations: <entity>_<action>(), @transaction.atomic, full_clean()
├── selectors.py    # Read operations: return QuerySet or Optional[Model]
├── apis.py         # One APIView per operation, nested Input/Output serializers
├── filters.py      # django-filter FilterSet classes
├── factories.py    # factory_boy factories for tests
├── tasks.py        # Background tasks (django.tasks or Celery)
├── urls.py         # URL routing
└── tests/
    ├── test_unit.py        # @pytest.mark.unit — pure logic, no DB (model properties, error classes)
    ├── test_models.py      # @pytest.mark.integration — model creation, constraints, managers
    ├── test_services.py    # @pytest.mark.integration — business logic with DB
    ├── test_selectors.py   # @pytest.mark.integration — filtering, retrieval
    └── test_apis.py        # @pytest.mark.e2e — full HTTP request/response cycle
```

## Key Conventions

- **Services**: keyword-only arguments, never pass request objects, use `enqueue_on_commit()` or `task_on_commit()` for async work
- **Selectors**: return QuerySets (not lists) so pagination is lazy
- **APIs**: delegate to services/selectors, never touch ORM directly
- **Errors**: all normalized to `{"message": "...", "extra": {"fields": {...}}}` via `ApplicationError`
- **Models**: extend `core.models.BaseModel` for `created_at`/`updated_at`
- **Tasks**: `django.tasks` for lightweight (emails, notifications), Celery for heavy/periodic

## Key Files

- `docs/specs/<app>.md` — Business rules (source of truth)
- `docs/technical/adding-a-new-app.md` — Step-by-step guide with checklist
- `docs/technical/architecture.md` — Full architecture explanation
- `src/core/exceptions.py` — `ApplicationError`
- `src/api/exception_handlers.py` — Error normalization
- `src/utils/services.py` — `model_update()` utility
- `src/utils/tasks.py` — `enqueue_on_commit`, `ResilientTask`, `task_on_commit`

## Commands

```bash
make testing              # all tests: unit+integration parallel, then e2e sequential
make testing-unit         # unit only (no DB)
make testing-integration  # integration only (with DB)
make testing-e2e          # e2e only (sequential)
make testing-cov          # tests with coverage
make lint                 # ruff check + format check
make lint-fix             # ruff fix + format
```

## Code Style

- Ruff with E/F/W/I rules, line-length 120
- Config in `pyproject.toml`
- Run `make lint-fix` before committing

## Adding a New App

Follow `docs/technical/adding-a-new-app.md`. Summary:

1. Document business rules in `docs/specs/<app>.md`
2. `python manage.py startapp <app>` inside the container
3. Set up the file structure (delete `views.py`, create `services.py`, `selectors.py`, `apis.py`, etc.)
4. Register in `INSTALLED_APPS`
5. Implement model -> services -> selectors -> filters -> APIs -> URLs -> factories -> tests
6. Wire URLs in `src/api/urls.py`
7. Verify against the checklist in the adding-a-new-app guide
