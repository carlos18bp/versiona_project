from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = 'Delete fake records from the database'

    """
    To delete fake data via console, run:
    python3 manage.py delete_fake_data --confirm

    Deletes every non-superuser User (fake data never creates staff/superusers)
    and then every Organization left without members — cascading its projects,
    documents and versions in the database. Storage objects (MinIO) belonging
    to cascaded documents are acceptable dev debris; production never runs this
    (the fake-data-refresh skill gates on DJANGO_ENV).
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all fake data.',
        )

    def handle(self, *args, **options):
        from orgs.models import Organization

        if not options.get('confirm'):
            raise CommandError('Deletion not confirmed. Re-run with --confirm.')

        self.stdout.write(self.style.SUCCESS('==== Deleting Fake Data ===='))

        self.stdout.write(self.style.SUCCESS('\n--- Deleting Users ---'))
        users_to_delete = User.objects.filter(is_superuser=False)
        user_count = users_to_delete.count()
        protected_count = User.objects.filter(is_superuser=True).count()

        for user in users_to_delete:
            user.delete()

        self.stdout.write(self.style.SUCCESS(f'{user_count} Users deleted'))
        self.stdout.write(self.style.WARNING(
            f'{protected_count} Superuser accounts protected and not deleted'
        ))

        self.stdout.write(self.style.SUCCESS('\n--- Deleting orphaned Organizations ---'))
        orphan_orgs = Organization.objects.filter(memberships__isnull=True)
        org_count = orphan_orgs.count()
        for org in orphan_orgs:
            org.delete()
        self.stdout.write(self.style.SUCCESS(f'{org_count} member-less Organizations deleted'))

        self.stdout.write(self.style.SUCCESS('\n==== Fake Data Deletion Complete ===='))
