from django.urls import path

from . import views

urlpatterns = [
    path('jobs/<uuid:job>/', views.job_detail, name='job-detail'),
]
