from django.urls import path

from . import views

urlpatterns = [
    path('public/plans/', views.public_plans, name='public-plans'),
]
