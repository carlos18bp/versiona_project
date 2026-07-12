from django.urls import path

from . import views, views_reviews

urlpatterns = [
    path('versions/<uuid:ver>/seals/', views.version_seals, name='version-seals'),
    path('versions/<uuid:ver>/seals/<uuid:seal_id>/revoke/', views.seal_revoke, name='seal-revoke'),
    path('versions/<uuid:ver>/seals/<uuid:seal_id>/verify/', views.seal_verify, name='seal-verify'),
    path('versions/<uuid:ver>/seal_plan/', views.version_seal_plan, name='version-seal-plan'),
    path('seal_keys/<str:key_id>/', views.seal_public_key, name='seal-public-key'),
    path('versions/<uuid:ver>/reviews/', views_reviews.version_reviews, name='version-reviews'),
    path('versions/<uuid:ver>/reviews/<uuid:review_id>/cancel/', views_reviews.review_cancel, name='review-cancel'),
    path('versions/<uuid:ver>/review_context/', views_reviews.version_review_context, name='version-review-context'),
    path('me/review_assignments/', views_reviews.my_review_assignments, name='my-review-assignments'),
]
