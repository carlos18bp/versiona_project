from django.urls import path

from . import views

urlpatterns = [
    path('documents/<uuid:doc>/comparisons/', views.document_comparisons, name='document-comparisons'),
    path('comparisons/<uuid:cmp>/', views.comparison_detail, name='comparison-detail'),
    path('comparisons/<uuid:cmp>/sections/<str:sec>/diff/', views.comparison_section_diff, name='comparison-section-diff'),
]
