from django.contrib.postgres.lookups import Unaccent
from django.db.models import CharField, TextField
from rest_framework.filters import SearchFilter

# Register unaccent transform for CharField and TextField
CharField.register_lookup(Unaccent)
TextField.register_lookup(Unaccent)


class AccentInsensitiveSearchFilter(SearchFilter):
    """
    Search filter that ignores accents/diacritics.

    Requires the PostgreSQL `unaccent` extension:
        CREATE EXTENSION IF NOT EXISTS unaccent;

    Usage in views:
        filter_backends = [AccentInsensitiveSearchFilter]
        search_fields = ["name", "email"]
    """

    def get_search_terms(self, request):
        return super().get_search_terms(request)

    def construct_search(self, field_name, queryset):
        return f"{field_name}__unaccent__icontains"
