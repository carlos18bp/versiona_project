from django.urls import path

from . import views

urlpatterns = [
    path('me/notifications/', views.my_notifications, name='my-notifications'),
    path('me/notifications/read_all/', views.notifications_read_all, name='notifications-read-all'),
    path('me/notifications/<uuid:notif>/read/', views.notification_read, name='notification-read'),
    path('me/notification_preferences/', views.my_notification_preferences, name='my-notification-preferences'),
]
