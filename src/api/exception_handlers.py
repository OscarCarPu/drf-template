from core.exceptions import ApplicationError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, ctx):
    """
    Normalize all errors to: {"message": "...", "extra": {"fields": {...}}}

    Handles:
    - Django ValidationError -> DRF ValidationError
    - ApplicationError -> 400 with message + extra
    - All DRF exceptions -> normalized format
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        exc = drf_exceptions.ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    # Handle ApplicationError
    if isinstance(exc, ApplicationError):
        data = {
            "message": exc.message,
            "extra": exc.extra,
        }
        return Response(data, status=400)

    # Let DRF handle the rest
    response = drf_exception_handler(exc, ctx)

    if response is None:
        return response

    # Normalize DRF error response
    if isinstance(response.data, list):
        response.data = {
            "message": response.data[0] if response.data else "Error",
            "extra": {},
        }
    elif isinstance(response.data, dict):
        # DRF ValidationError with field errors
        if "detail" in response.data:
            response.data = {
                "message": str(response.data["detail"]),
                "extra": {},
            }
        else:
            # Field-level validation errors
            first_error = next(iter(response.data.values()), ["Error"])
            if isinstance(first_error, list):
                first_error = first_error[0]

            response.data = {
                "message": "Validation error.",
                "extra": {"fields": {k: v if isinstance(v, list) else [v] for k, v in response.data.items()}},
            }

    return response
