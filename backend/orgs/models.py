"""
Organizations and org-level membership (docs/plan/02 §3.1 — flows A1/A2).

The personal workspace IS an organization of one (`kind=personal`), created
automatically at sign-up; the full onboarding wizard arrives with It6 (A1).
"""

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from core.models import PublicIdModel, TimestampedModel


class Organization(PublicIdModel, TimestampedModel):
    class Kind(models.TextChoices):
        PERSONAL = 'personal', 'Personal'
        TEAM = 'team', 'Team'

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.PERSONAL)

    def __str__(self):
        return self.name

    @classmethod
    def build_unique_slug(cls, name: str) -> str:
        base = slugify(name)[:120] or 'org'
        slug = base
        suffix = 1
        while cls.objects.filter(slug=slug).exists():
            suffix += 1
            slug = f'{base}-{suffix}'
        return slug


class OrganizationMembership(TimestampedModel):
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='org_memberships'
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'user'], name='uniq_org_membership'
            ),
        ]

    def __str__(self):
        return f'{self.user} @ {self.organization} ({self.role})'
