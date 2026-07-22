from django.urls import path

from . import views

urlpatterns = [
    path('versions/<uuid:ver>/observations/', views.version_observations, name='version-observations'),
    path('observations/<uuid:obs>/replies/', views.observation_reply, name='observation-reply'),
    path('observations/<uuid:obs>/status/', views.observation_status, name='observation-status'),
]
