from rest_framework import serializers


class DynamicModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that supports dynamic field selection and expansion.

    Usage:
        ?fields=id,email,name     — only return these fields
        ?expand=profile,company   — include nested serializer fields

    Configure expandable fields in Meta:
        class Meta:
            model = User
            fields = "__all__"
            expandable_fields = {
                "profile": (ProfileSerializer, {}),
                "company": (CompanySerializer, {"source": "company"}),
            }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if not request:
            return

        # ?fields= support
        fields_param = request.query_params.get("fields")
        if fields_param:
            allowed = set(fields_param.split(","))
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        # ?expand= support
        expand_param = request.query_params.get("expand")
        expandable_fields = getattr(self.Meta, "expandable_fields", {})
        if expand_param and expandable_fields:
            for field_name in expand_param.split(","):
                if field_name in expandable_fields:
                    serializer_class, kwargs_extra = expandable_fields[field_name]
                    self.fields[field_name] = serializer_class(**kwargs_extra)
