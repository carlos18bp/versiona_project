from django.urls import path

from . import views

urlpatterns = [
    path('orgs/<uuid:org>/audit/', views.org_audit, name='org-audit'),
    path('projects/<uuid:proj>/activity/', views.project_activity, name='project-activity'),
]
