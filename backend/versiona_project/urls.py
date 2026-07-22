from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.admin_site import admin_site


def health_check(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('api/health/', health_check, name='health-check'),
    path('admin/', admin_site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('accounts.urls')),
    path('api/', include('core.urls')),
    path('api/', include('orgs.urls')),
    path('api/', include('projects.urls')),
    path('api/', include('documents.urls')),
    path('api/', include('engine.urls')),
    path('api/', include('comparisons.urls')),
    path('api/', include('reviews.urls')),
    path('api/', include('notifications.urls')),
    path('api/', include('observations.urls')),
    path('api/', include('audit.urls')),
    path('api/', include('checks.urls')),
    path('api/', include('billing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if getattr(settings, 'ENABLE_SILK', False):
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
