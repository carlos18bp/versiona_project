"""Job polling endpoint (docs/plan/03 §3 — C1/C2/E1/A1)."""

from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import require_project_role


@api_view(['GET'])
@require_project_role('viewer')
def job_detail(request, job):
    engine_job = request.resolved_object
    return Response({
        'public_id': str(engine_job.public_id),
        'job_type': engine_job.job_type,
        'status': engine_job.status,
        'attempts': engine_job.attempts,
        'error': engine_job.error_detail or None,
        'result': engine_job.result,
        'version_id': str(engine_job.document_version.public_id)
        if engine_job.document_version else None,
    })
