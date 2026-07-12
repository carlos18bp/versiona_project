from django.urls import path

from . import views

urlpatterns = [
    path('orgs/', views.my_orgs, name='my-orgs'),
    path('orgs/<uuid:org>/trash/', views.org_trash, name='org-trash'),
]
