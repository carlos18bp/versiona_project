from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.db.models.deletion import ProtectedError

from accounts.models import User
from core.fake_data_guard import add_allow_production_argument, refuse_on_production


class Command(BaseCommand):
    help = 'Delete fake records from the database'

    """
    To delete fake data via console, run:
    python3 manage.py delete_fake_data --confirm

    Deletes every non-superuser User (fake data never creates staff/superusers)
    and then every Organization left without members — cascading its projects,
    documents and versions in the database. Users woven into PROTECTED domain
    evidence (Seal.reviewer, Certificate.issued_by, Invitation.invited_by) are
    PRESERVED, not force-deleted: sealed history is append-only by product
    invariant (I4) and this command never trades it away. Storage objects
    belonging to cascaded documents are acceptable dev debris.

    Production and staging are refused in code (core.fake_data_guard), not by
    convention: this used to rely on the fake-data-refresh skill checking
    DJANGO_ENV, which protected nobody running the command by hand.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all fake data.',
        )
        add_allow_production_argument(parser)

    def handle(self, *args, **options):
        from orgs.models import Organization

        refuse_on_production(options, 'delete_fake_data')

        if not options.get('confirm'):
            raise CommandError('Deletion not confirmed. Re-run with --confirm.')

        self.stdout.write(self.style.SUCCESS('==== Deleting Fake Data ===='))

        self.stdout.write(self.style.SUCCESS('\n--- Deleting Users ---'))
        superuser_count = User.objects.filter(is_superuser=True).count()
        deleted = 0
        kept_as_evidence = 0
        for user in User.objects.filter(is_superuser=False):
            try:
                user.delete()
                deleted += 1
            except ProtectedError:
                kept_as_evidence += 1

        self.stdout.write(self.style.SUCCESS(f'{deleted} Users deleted'))
        self.stdout.write(self.style.WARNING(
            f'{superuser_count} Superuser accounts protected and not deleted'
        ))
        if kept_as_evidence:
            self.stdout.write(self.style.WARNING(
                f'{kept_as_evidence} Users preserved: referenced by protected '
                'domain evidence (seals/certificates/invitations — I4)'
            ))

        self.stdout.write(self.style.SUCCESS('\n--- Deleting orphaned Organizations ---'))
        org_deleted = 0
        org_kept = 0
        for org in Organization.objects.filter(memberships__isnull=True):
            try:
                org.delete()
                org_deleted += 1
            except (ProtectedError, DatabaseError):
                org_kept += 1  # sealed history triggers/protected refs — keep
        self.stdout.write(self.style.SUCCESS(f'{org_deleted} member-less Organizations deleted'))
        if org_kept:
            self.stdout.write(self.style.WARNING(
                f'{org_kept} Organizations preserved (sealed/protected history)'
            ))

        self.stdout.write(self.style.SUCCESS('\n==== Fake Data Deletion Complete ===='))
