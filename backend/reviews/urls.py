from django.urls import path

from . import views

urlpatterns = [
    path('versions/<uuid:ver>/seals/', views.version_seals, name='version-seals'),
    path('versions/<uuid:ver>/seals/<uuid:seal_id>/revoke/', views.seal_revoke, name='seal-revoke'),
    path('versions/<uuid:ver>/seals/<uuid:seal_id>/verify/', views.seal_verify, name='seal-verify'),
    path('versions/<uuid:ver>/seal_plan/', views.version_seal_plan, name='version-seal-plan'),
    path('seal_keys/<str:key_id>/', views.seal_public_key, name='seal-public-key'),
]
