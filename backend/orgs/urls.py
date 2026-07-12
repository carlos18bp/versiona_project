from django.urls import path

from . import views

urlpatterns = [
    path('me/onboarding/', views.my_onboarding, name='my-onboarding'),
    path('invitations/<str:token>/', views.invitation_state, name='invitation-state'),
    path('invitations/<str:token>/accept/', views.invitation_accept, name='invitation-accept'),
    path('orgs/', views.my_orgs, name='my-orgs'),
    path('orgs/<uuid:org>/trash/', views.org_trash, name='org-trash'),
]
