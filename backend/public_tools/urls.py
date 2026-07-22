from django.urls import path

from . import views

urlpatterns = [
    path('comparisons/', views.create_comparison, name='public-comparison-create'),
    path('comparisons/<uuid:pub>/', views.comparison_detail,
         name='public-comparison-detail'),
]
