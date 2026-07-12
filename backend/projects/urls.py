from django.urls import path

from . import views

urlpatterns = [
    path('orgs/<uuid:org>/projects/', views.org_projects, name='org-projects'),
    path('projects/<uuid:proj>/', views.project_detail, name='project-detail'),
    path('projects/<uuid:proj>/members/', views.project_members, name='project-members'),
    path('projects/<uuid:proj>/restore/', views.project_restore, name='project-restore'),
    path('projects/<uuid:proj>/archive/', views.project_archive, name='project-archive'),
    path('projects/<uuid:proj>/unarchive/', views.project_unarchive, name='project-unarchive'),
]
