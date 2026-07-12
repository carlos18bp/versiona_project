from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    To generate fake data via console, run:
    python3 manage.py create_fake_data [numbers_of_records] (optional)

    Examples:
    python3 manage.py create_fake_data 20
    python3 manage.py create_fake_data --users 10

    Scenario generators for Versiona domain data (orgs, projects, documents
    with versions, seals, observations) join here as each vertical iteration
    lands (docs/plan/07 §5: --scenario=demo|e2e|onboarding).
    """

    help = 'Create fake data in the database'

    def add_arguments(self, parser):
        parser.add_argument('number_of_records', type=int, nargs='?', default=None)
        parser.add_argument('--users', type=int, default=10)

    def handle(self, *args, **options):
        number_of_records = options['number_of_records']
        users = number_of_records if number_of_records is not None else options['users']

        self.stdout.write(self.style.SUCCESS('==== Creating Fake Data ===='))

        self.stdout.write(self.style.SUCCESS('\n--- Creating Users ---'))
        call_command('create_users', number_of_users=users)

        self.stdout.write(self.style.SUCCESS('\n==== Fake Data Creation Complete ===='))
