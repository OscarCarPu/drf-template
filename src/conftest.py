"""
Root conftest — shared fixtures and xdist worker isolation.

Each xdist worker gets its own Redis database (DB 1–N) so that
cache keys never collide across parallel workers.
"""

import pytest
from rest_framework.test import APIClient

from users.factories import UserFactory


# ---------------------------------------------------------------------------
# xdist isolation
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _isolate_redis_per_worker(request):
    """Assign a unique Redis DB to each xdist worker."""
    worker_input = getattr(request.config, "workerinput", None)
    if worker_input is None:
        return  # master / no xdist — keep defaults

    worker_num = int(worker_input["workerid"].replace("gw", ""))
    redis_db = worker_num + 1  # gw0→DB 1, gw1→DB 2, …

    from django.conf import settings

    for cache_conf in settings.CACHES.values():
        location = cache_conf.get("LOCATION", "")
        if "redis" in location:
            base = location.rsplit("/", 1)[0]
            cache_conf["LOCATION"] = f"{base}/{redis_db}"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def authenticated_client():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return client
