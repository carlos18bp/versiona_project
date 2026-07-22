from django.contrib import admin

from core.admin_site import admin_site

from .models import Subscription


@admin.register(Subscription, site=admin_site)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('organization', 'plan_key', 'status', 'trial_ends_at')
    list_filter = ('status', 'plan_key')
    search_fields = ('organization__name', 'organization__slug')
    readonly_fields = ('trial_ending_notified_at', 'trial_expired_notified_at')
