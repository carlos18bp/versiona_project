from django.urls import path

from . import views

urlpatterns = [
    path('projects/<uuid:proj>/documents/', views.project_documents, name='project-documents'),
    path('documents/<uuid:doc>/', views.document_detail, name='document-detail'),
    path('documents/<uuid:doc>/restore/', views.document_restore, name='document-restore'),
    path('documents/<uuid:doc>/versions/', views.document_versions, name='document-versions'),
    path('documents/<uuid:doc>/versions/upload_intent/', views.upload_intent, name='upload-intent'),
    path('documents/<uuid:doc>/versions/complete/', views.upload_complete, name='upload-complete'),
    path('versions/<uuid:ver>/', views.version_detail, name='version-detail'),
    path('versions/<uuid:ver>/restore/', views.version_restore, name='version-restore'),
    path('versions/<uuid:ver>/download/', views.version_download, name='version-download'),
    path('versions/<uuid:ver>/file/', views.version_file, name='version-file'),
    path('versions/<uuid:ver>/sections/', views.version_sections, name='version-sections'),
]
