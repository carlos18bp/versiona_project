"""
Effective-role resolution and FBV permission decorators (docs/plan/03 §5,
invariant I12 — gap G24).

Rules:
- Org owner/admin ⇒ implicit `admin` on every project of the org.
- Org member ⇒ whatever their ProjectMembership says; no membership ⇒ no
  access, expressed as **404** (existence is never leaked across tenants).
- Insufficient role for a member ⇒ 403.
- The decorators resolve the target object from URL kwargs (public_id),
  walk up to the project, and attach `request.project`, `request.org`,
  `request.effective_role` (and the resolved object) for the view/service.
"""

from functools import wraps

from django.http import Http404
from rest_framework import status
from rest_framework.response import Response

from orgs.models import Organization, OrganizationMembership
from projects.models import Project, ProjectMembership

PROJECT_ROLE_ORDER = {'viewer': 0, 'reviewer': 1, 'editor': 2, 'admin': 3}
ORG_ROLE_ORDER = {'member': 0, 'admin': 1, 'owner': 2}


def resolve_org_role(user, organization) -> str | None:
    if not user or not user.is_authenticated:
        return None
    membership = OrganizationMembership.objects.filter(
        organization=organization, user=user, is_active=True
    ).first()
    return membership.role if membership else None


def resolve_effective_role(user, project) -> str | None:
    """Project-scope effective role (docs/plan/03 §5)."""
    org_role = resolve_org_role(user, project.organization)
    if org_role in ('owner', 'admin'):
        return 'admin'
    if org_role is None:
        return None
    membership = ProjectMembership.objects.filter(project=project, user=user).first()
    return membership.role if membership else None


def _resolve_project_from_kwargs(kwargs, include_trashed=False):
    """Walk URL kwargs up to the Project. Raises Http404 when absent (I12)."""
    from documents.models import Document, DocumentVersion
    from engine.models import EngineJob

    manager = Project.all_objects if include_trashed else Project.objects
    if 'proj' in kwargs:
        project = manager.filter(public_id=kwargs['proj']).first()
        if not project:
            raise Http404
        return project, None

    if 'doc' in kwargs:
        doc_manager = Document.all_objects if include_trashed else Document.objects
        document = (
            doc_manager.filter(public_id=kwargs['doc'])
            .select_related('project__organization')
            .first()
        )
        if not document or (not include_trashed and document.project.is_trashed):
            raise Http404
        return document.project, document

    if 'ver' in kwargs:
        ver_manager = DocumentVersion.all_objects if include_trashed else DocumentVersion.objects
        version = (
            ver_manager.filter(public_id=kwargs['ver'])
            .select_related('document__project__organization')
            .first()
        )
        if not version or (
            not include_trashed
            and (version.document.is_trashed or version.document.project.is_trashed)
        ):
            raise Http404
        return version.document.project, version

    if 'job' in kwargs:
        job = (
            EngineJob.objects.filter(public_id=kwargs['job'])
            .select_related('document_version__document__project__organization')
            .first()
        )
        if not job or not job.document_version:
            raise Http404
        return job.document_version.document.project, job

    raise Http404


def require_project_role(min_role: str, include_trashed: bool = False):
    """FBV decorator: membership → 404; insufficient role → 403 (I12)."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            project, resolved = _resolve_project_from_kwargs(kwargs, include_trashed)
            role = resolve_effective_role(request.user, project)
            if role is None:
                raise Http404
            if PROJECT_ROLE_ORDER[role] < PROJECT_ROLE_ORDER[min_role]:
                return Response(
                    {'error': 'Insufficient project role.'}, status=status.HTTP_403_FORBIDDEN
                )
            request.project = project
            request.org = project.organization
            request.effective_role = role
            request.resolved_object = resolved
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def require_org_role(min_role: str):
    """FBV decorator for org-scoped routes (`org` kwarg)."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            org = Organization.objects.filter(public_id=kwargs.get('org')).first()
            if not org:
                raise Http404
            role = resolve_org_role(request.user, org)
            if role is None:
                raise Http404
            if ORG_ROLE_ORDER[role] < ORG_ROLE_ORDER[min_role]:
                return Response(
                    {'error': 'Insufficient organization role.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            request.org = org
            request.org_role = role
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
