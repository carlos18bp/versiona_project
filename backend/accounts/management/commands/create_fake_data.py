from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    To generate fake data via console, run:
    python3 manage.py create_fake_data [numbers_of_records] (optional)
    python3 manage.py create_fake_data --scenario=e2e

    Scenarios (docs/plan/07 §5):
    - (default)  random users via Faker
    - e2e        deterministic actors + org + project for the Playwright
                 harness (docs/plan/06 §5.1): {owner,admin,editor,reviewer,
                 viewer}@versiona.test / password 'secreta123', org 'Acme E2E',
                 project 'Torre E2E' with memberships per role. Idempotent.
    """

    help = 'Create fake data in the database'

    def add_arguments(self, parser):
        parser.add_argument('number_of_records', type=int, nargs='?', default=None)
        parser.add_argument('--users', type=int, default=10)
        parser.add_argument('--scenario', type=str, default='')

    def handle(self, *args, **options):
        if options.get('scenario') == 'e2e':
            self._seed_e2e()
            return

        number_of_records = options['number_of_records']
        users = number_of_records if number_of_records is not None else options['users']

        self.stdout.write(self.style.SUCCESS('==== Creating Fake Data ===='))

        self.stdout.write(self.style.SUCCESS('\n--- Creating Users ---'))
        call_command('create_users', number_of_users=users)

        self.stdout.write(self.style.SUCCESS('\n==== Fake Data Creation Complete ===='))

    def _seed_e2e(self):
        from django.contrib.auth import get_user_model

        from orgs.models import Organization, OrganizationMembership
        from projects.models import Project, ProjectConfigVersion, ProjectMembership

        User = get_user_model()
        self.stdout.write(self.style.SUCCESS('==== Seeding E2E scenario ===='))

        users = {}
        for alias in ('owner', 'admin', 'editor', 'reviewer', 'viewer'):
            user, created = User.objects.get_or_create(
                email=f'{alias}@versiona.test',
                defaults={'first_name': alias.title(), 'is_active': True},
            )
            if created:
                user.set_password('secreta123')
                user.save(update_fields=['password'])
            users[alias] = user

        org, _ = Organization.objects.get_or_create(
            slug='acme-e2e', defaults={'name': 'Acme E2E', 'kind': Organization.Kind.TEAM}
        )
        # The harness org exercises every flow: the free limits would block
        # the specs (7 members, N projects) — F1 has its own dedicated spec.
        if org.plan != 'enterprise':
            org.plan = 'enterprise'
            org.save(update_fields=['plan'])
        OrganizationMembership.objects.get_or_create(
            organization=org, user=users['owner'],
            defaults={'role': OrganizationMembership.Role.OWNER},
        )
        for alias in ('admin', 'editor', 'reviewer', 'viewer'):
            OrganizationMembership.objects.get_or_create(
                organization=org, user=users[alias],
                defaults={'role': OrganizationMembership.Role.MEMBER},
            )

        project, _ = Project.objects.get_or_create(
            organization=org, slug='torre-e2e', defaults={'name': 'Torre E2E'}
        )
        role_map = {
            'admin': ProjectMembership.Role.ADMIN,
            'editor': ProjectMembership.Role.EDITOR,
            'reviewer': ProjectMembership.Role.REVIEWER,
            'viewer': ProjectMembership.Role.VIEWER,
        }
        for alias, role in role_map.items():
            ProjectMembership.objects.get_or_create(
                project=project, user=users[alias], defaults={'role': role}
            )
        ProjectConfigVersion.current_for(project)

        self.stdout.write(self.style.SUCCESS(
            'E2E seed listo: 5 usuarios @versiona.test / org acme-e2e / proyecto torre-e2e'
        ))
