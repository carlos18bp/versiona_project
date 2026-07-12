from django.urls import path

from . import views

urlpatterns = [
    path('projects/<uuid:proj>/activity/', views.project_activity, name='project-activity'),
]
