from django.db import models


def model_update(*, instance: models.Model, fields: list[str], data: dict, **kwargs) -> tuple[models.Model, bool]:
    """
    Generic model update service following the HackSoft pattern.

    Performs update on an instance by:
    1. Only updating fields present in both `fields` and `data`
    2. Handling M2M fields separately
    3. Running full_clean() before saving
    4. Using update_fields for efficient DB writes

    Usage:
        user, has_updated = model_update(
            instance=user,
            fields=["first_name", "last_name"],
            data={"first_name": "John"},
        )

    Returns:
        Tuple of (instance, has_updated: bool)
    """
    m2m_data = {}
    update_fields = []

    model_fields = {field.name: field for field in instance._meta.get_fields()}

    for field in fields:
        if field not in data:
            continue

        model_field = model_fields.get(field)

        # Handle M2M fields separately
        if model_field and isinstance(model_field, models.ManyToManyField):
            m2m_data[field] = data[field]
            continue

        if getattr(instance, field) != data[field]:
            setattr(instance, field, data[field])
            update_fields.append(field)

    has_updated = bool(update_fields) or bool(m2m_data)

    if has_updated:
        if update_fields:
            instance.full_clean()
            # Always include updated_at if the model has it
            if hasattr(instance, "updated_at"):
                update_fields.append("updated_at")
            instance.save(update_fields=update_fields)

        for field_name, value in m2m_data.items():
            getattr(instance, field_name).set(value)

    return instance, has_updated
