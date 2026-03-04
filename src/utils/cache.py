import functools
import hashlib

from django.core.cache import cache


def cache_viewset_list(timeout=60 * 5, key_prefix=""):
    """
    Decorator for caching ViewSet list actions.

    Generates a cache key from the request path and query params.

    Usage:
        @cache_viewset_list(timeout=300, key_prefix="users")
        def list(self, request, *args, **kwargs):
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            query_string = request.META.get("QUERY_STRING", "")
            raw_key = f"{key_prefix}:{request.path}:{query_string}"
            cache_key = hashlib.md5(raw_key.encode()).hexdigest()

            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            response = func(self, request, *args, **kwargs)
            cache.set(cache_key, response, timeout)
            return response

        return wrapper

    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalidate all cache keys matching a pattern.

    Requires a cache backend that supports `delete_pattern` (e.g., django-redis).

    Usage:
        invalidate_cache_pattern("users:*")
    """
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(pattern)
