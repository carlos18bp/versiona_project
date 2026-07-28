"""Deploy-time guards for object storage.

The whole "objects are reachable only through a signed URL" property rests on
one configuration fact: OBJECT_STORAGE_ROOT must not live inside a directory
that is served directly. urls.py serves MEDIA_ROOT unsigned under DEBUG, and the
fleet nginx site aliases /media/ and /static/ straight to the filesystem — so a
root nested in either would silently make every PDF readable by path.

A comment cannot enforce that; a system check can. Runs on `manage.py check`,
which `migrate`, `runserver` and the deploy script all invoke.
"""

import os

from django.conf import settings
from django.core.checks import Error, register


def _is_within(child: str, parent: str) -> bool:
    if not child or not parent:
        return False
    child_path = os.path.realpath(child)
    parent_path = os.path.realpath(parent)
    return os.path.commonpath([child_path, parent_path]) == parent_path


@register()
def object_storage_root_is_private(app_configs, **kwargs):
    root = str(getattr(settings, 'OBJECT_STORAGE_ROOT', '') or '')
    if not root:
        return [Error(
            'OBJECT_STORAGE_ROOT is empty.',
            hint='Set OBJECT_STORAGE_ROOT; the filesystem storage backend needs it.',
            id='documents.E001',
        )]

    errors = []
    for name in ('MEDIA_ROOT', 'STATIC_ROOT'):
        served = str(getattr(settings, name, '') or '')
        if _is_within(root, served):
            errors.append(Error(
                f'OBJECT_STORAGE_ROOT is inside {name} ({served}).',
                hint=(
                    f'{name} is served directly (nginx alias, and MEDIA_ROOT also by '
                    'urls.py under DEBUG), so objects there would be readable by '
                    'guessing their path. Move OBJECT_STORAGE_ROOT outside it.'
                ),
                id='documents.E002',
            ))
    return errors
