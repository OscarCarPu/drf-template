import factory

from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.django.Password("testpass123")
    is_active = True

    class Params:
        admin = factory.Trait(
            is_staff=True,
            is_superuser=True,
        )
