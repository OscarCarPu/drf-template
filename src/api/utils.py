from django.shortcuts import get_object_or_404
from rest_framework import serializers

from api.pagination import LimitOffsetPagination


def get_paginated_response(*, pagination_class=None, serializer_class, queryset, request, view):
    if pagination_class is None:
        pagination_class = LimitOffsetPagination

    paginator = pagination_class()
    page = paginator.paginate_queryset(queryset, request, view=view)

    if page is not None:
        serializer = serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = serializer_class(queryset, many=True)
    return serializer.data


def inline_serializer(*, fields, data=None, **kwargs):
    """
    Create a serializer class on the fly with the given fields.

    Usage:
        serializer = inline_serializer(fields={
            "email": serializers.EmailField(),
            "is_active": serializers.BooleanField(),
        })
    """
    serializer_class = type("InlineSerializer", (serializers.Serializer,), fields)

    if data is not None:
        return serializer_class(data=data, **kwargs)
    return serializer_class(**kwargs)


def get_object_or_404_from_queryset(queryset, **kwargs):
    return get_object_or_404(queryset, **kwargs)
