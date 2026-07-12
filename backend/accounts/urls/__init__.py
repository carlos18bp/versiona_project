from django.urls import include, path

urlpatterns = [
    path('', include('accounts.urls.auth')),
    path('google-captcha/', include('accounts.urls.captcha')),
]
