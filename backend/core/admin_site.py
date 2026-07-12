"""
Custom admin site for Versiona, organized by sections.

Apps register their models against `admin_site` (imported from here) inside
their own admin.py; new domain sections are added here as their vertical
iteration lands (docs/plan/09).
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class VersionaAdminSite(admin.AdminSite):
    site_header = 'Versiona Administration'
    site_title = 'Versiona Admin'
    index_title = 'Welcome to the Versiona Control Panel'

    def get_app_list(self, request):
        app_dict = self._build_app_dict(request)
        accounts_models = app_dict.get('accounts', {}).get('models', [])
        core_models = app_dict.get('core', {}).get('models', [])

        custom_app_list = [
            {
                'name': _('👥 User Management'),
                'app_label': 'user_management',
                'models': [
                    model for model in accounts_models
                    if model['object_name'] in ['User', 'PasswordCode']
                ],
            },
            {
                'name': _('🚧 Staging Phase Banner'),
                'app_label': 'staging_management',
                'models': [
                    model for model in core_models
                    if model['object_name'] in ['StagingPhaseBanner']
                ],
            },
        ]

        # Any app section not curated above still shows up (future iterations).
        curated_labels = {'accounts', 'core'}
        custom_app_list.extend(
            section for label, section in app_dict.items() if label not in curated_labels
        )

        return [section for section in custom_app_list if section['models']]


admin_site = VersionaAdminSite(name='myadmin')
