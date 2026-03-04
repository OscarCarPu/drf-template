from django.db import models


class CustomQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class ActiveManager(models.Manager):
    """
    Manager that returns only active records by default.

    Usage:
        class MyModel(BaseModel):
            is_active = models.BooleanField(default=True)

            objects = ActiveManager()
            all_objects = models.Manager()
    """

    def get_queryset(self):
        return CustomQuerySet(self.model, using=self._db).active()
