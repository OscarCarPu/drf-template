# App Name — Business Rules

> Source of truth for app-related business logic.
> Every rule here must have a corresponding test that enforces it.

## Entity Creation

| Rule ID | Rule | Tested in |
|---------|------|-----------|
| APP-CREATE-01 | | `test_services::` |

## Entity Update

| Rule ID | Rule | Tested in |
|---------|------|-----------|
| APP-UPDATE-01 | | `test_services::` |

## Entity Deletion / Deactivation

| Rule ID | Rule | Tested in |
|---------|------|-----------|
| APP-DEACT-01 | | `test_services::` |

## Authentication & Permissions

| Rule ID | Rule | Tested in |
|---------|------|-----------|
| APP-AUTH-01 | All API endpoints require authentication | `test_apis::test_requires_auth` |
