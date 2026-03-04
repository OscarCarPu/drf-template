# ADR 0001: Adopt HackSoft Django Styleguide

## Status

**Accepted**

## Context

Django projects tend to accumulate business logic in models, views, and serializers without clear boundaries. As projects grow, this leads to:

- Fat models with mixed concerns (data + business logic + presentation)
- Views that directly manipulate querysets and contain inline business rules
- Difficulty testing business logic in isolation
- Unclear patterns for cross-app communication

We needed a set of conventions that:

1. Separate reads from writes
2. Keep business logic out of models and views
3. Provide a consistent, predictable file structure across apps
4. Scale well with team size

## Decision

We adopt the [HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide) as the foundational architecture for this project.

Key conventions:

- **Services** (`services.py`) — All write operations. Functions named `<entity>_<action>()`, decorated with `@transaction.atomic`, calling `full_clean()` before save.
- **Selectors** (`selectors.py`) — All read operations. Return `QuerySet` or `Optional[Model]`. Use `django-filter` FilterSets.
- **APIs** (`apis.py`) — One `APIView` per operation. Nested `InputSerializer` / `OutputSerializer`. Delegate to services and selectors.
- **Models** (`models.py`) — Data and constraints only. No business logic.
- **Error handling** — `ApplicationError` for business errors, normalized to `{"message", "extra"}` by a custom exception handler.

The `users/` app serves as the reference implementation of all patterns.

## Consequences

**Positive:**

- Clear, consistent structure across all apps
- Business logic is easily testable in isolation (call service functions directly)
- New developers can find code predictably (services for writes, selectors for reads)
- Cross-app communication has explicit boundaries (import services/selectors, not models)

**Negative:**

- More files per app compared to vanilla Django (services.py, selectors.py, filters.py, factories.py)
- Simple CRUD operations require more boilerplate than ModelViewSet
- Developers unfamiliar with the styleguide need onboarding

**Neutral:**

- We chose plain `APIView` over `ViewSet` — this is more explicit but requires more URL wiring

---

<!-- Template for future ADRs:

# ADR NNNN: Title

## Status

Proposed | Accepted | Deprecated | Superseded by [ADR NNNN](NNNN-title.md)

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

-->
