from django.core.management.base import BaseCommand
from faker import Faker

from accounts.models import User


class Command(BaseCommand):
    help = 'Create fake User records that follow Versiona business rules'

    """
    Each fake user is created the way the product creates real ones (A1/It9):
    a personal Organization is provisioned via ensure_personal_org, which also
    starts the 14-day Pro trial (billing.Subscription). No fake user is ever
    staff or superuser — delete_fake_data relies on that to clean up safely.
    """

    def add_arguments(self, parser):
        parser.add_argument('number_of_users', type=int, nargs='?', default=10)

    def handle(self, *args, **options):
        from orgs.services import ensure_personal_org

        number_of_users = options['number_of_users']
        fake = Faker()

        for _ in range(number_of_users):
            user = User.objects.create_user(
                email=fake.unique.email(),
                password='secreta123',  # deterministic dev password
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone=fake.phone_number(),
                is_active=True,
            )
            org = ensure_personal_org(user)
            self.stdout.write(self.style.SUCCESS(
                f'User "{user.email}" created with personal org "{org.slug}" (trial)'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'{number_of_users} User records created with personal orgs + trials'
        ))
