# Users — Business Rules

> Source of truth for user-related business logic.
> Every rule here must have a corresponding test that enforces it.

## User Creation

| Rule ID | Rule | Tested in |
|---------|------|-----------|
| USR-CREATE-01 | Email is required and must be unique | `test_models::test_create_user`, `test_models::test_create_user_without_email_raises` |
| USR-CREATE-02 | Password is hashed before storage | `test_models::test_create_user` |
| USR-CREATE-03 | New users are active by default | `test_services::test_creates_user` |
| USR-CREATE-04 | A welcome email is enqueued after user creation | `test_services::test_creates_user` (mocked) |
| USR-CREATE-05 | Welcome email is dispatched only after the DB transaction commits | Enforced by `enqueue_on_commit` |

## User Update

| Rule ID | Rule | Tested in |
|---------|------|-----------|
| USR-UPDATE-01 | Only `first_name` and `last_name` are updatable | `test_services::test_ignores_non_allowed_fields` |
| USR-UPDATE-02 | `full_clean()` runs before save | Enforced by `model_update` utility |

## User Deactivation

| Rule ID | Rule | Tested in |
|---------|------|-----------|
| USR-DEACT-01 | An active user can be deactivated | `test_services::test_deactivates_user` |
| USR-DEACT-02 | Deactivating an already-deactivated user raises `ApplicationError` | `test_services::test_raises_if_already_deactivated` |

## Authentication

| Rule ID | Rule | Tested in |
|---------|------|-----------|
| USR-AUTH-01 | All API endpoints require authentication | `test_apis::test_requires_auth` |
| USR-AUTH-02 | Session and Token authentication are supported | Enforced by `ApiAuthMixin` |

## Superuser

| Rule ID | Rule | Tested in |
|---------|------|-----------|
| USR-SUPER-01 | Superuser must have `is_staff=True` and `is_superuser=True` | `test_models::test_create_superuser` |
