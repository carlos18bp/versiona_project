"""
Celery application for Versiona.

Broker and result backend: Redis (settings.CELERY_*). Queues follow
docs/plan/05 §7: `default` (domain work), `engine_light` (comparisons),
`engine_heavy` (analysis/OCR). Periodic tasks are declared statically in
settings.CELERY_BEAT_SCHEDULE and served by `celery beat`.

Run in development:
    celery -A versiona_project worker -l info -Q default,engine_light,engine_heavy
    celery -A versiona_project beat -l info
"""

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'versiona_project.settings')

app = Celery('versiona_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
