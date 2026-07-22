from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = 'Delete fake records from the database'

    """
    To delete fake data via console, run:
    python3 manage.py delete_fake_data --confirm

    Note: This command will NOT delete superusers or admin users to protect
    system administrators. Versiona domain models (orgs, projects, documents)
    join here as each vertical iteration lands.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all fake data.',
        )

    def handle(self, *args, **options):
        if not options.get('confirm'):
            raise CommandError('Deletion not confirmed. Re-run with --confirm.')

        self.stdout.write(self.style.SUCCESS('==== Deleting Fake Data ===='))

        # Delete Users (excluding superusers and staff)
        self.stdout.write(self.style.SUCCESS('\n--- Deleting Users ---'))
        users_to_delete = User.objects.filter(is_superuser=False, is_staff=False)
        user_count = users_to_delete.count()
        protected_count = (
            User.objects.filter(is_superuser=True).count()
            + User.objects.filter(is_staff=True, is_superuser=False).count()
        )

        for user in users_to_delete:
            user.delete()

        self.stdout.write(self.style.SUCCESS(f'{user_count} Users deleted'))
        self.stdout.write(self.style.WARNING(
            f'{protected_count} Admin/Superuser accounts protected and not deleted'
        ))

        self.stdout.write(self.style.SUCCESS('\n==== Fake Data Deletion Complete ===='))
