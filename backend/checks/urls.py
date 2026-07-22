from django.urls import path

from . import views

urlpatterns = [
    path('orgs/<uuid:org>/checklist_templates/', views.org_checklist_templates, name='org-checklist-templates'),
    path('versions/<uuid:ver>/checks/', views.version_checks, name='version-checks'),
]
