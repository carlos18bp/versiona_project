import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from core.admin_site import admin_site

from .forms.user import UserChangeForm, UserCreationForm
from .models import PasswordCode, User
from .utils.auth_utils import generate_auth_tokens

logger = logging.getLogger(__name__)


# ============================================================================
# USER MANAGEMENT
# ============================================================================

class VersionaUserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'login_as_link')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone')}),
        (_('Role'), {'fields': ('role',)}),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2', 'role'),
            },
        ),
    )

    readonly_fields = ('date_joined', 'login_as_link')
    filter_horizontal = ('groups', 'user_permissions')

    def login_as_link(self, obj):
        if not obj or not obj.pk:
            return '—'
        url = reverse('myadmin:accounts_user_login_as', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="text-decoration:none" target="_blank" rel="noopener">Login as this user</a>',
            url,
        )
    login_as_link.short_description = _('Impersonate')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:user_id>/login_as/',
                self.admin_site.admin_view(self.login_as_user_view),
                name='accounts_user_login_as',
            ),
        ]
        return custom_urls + urls

    def login_as_user_view(self, request, user_id):
        if not (request.user.is_active and request.user.is_superuser):
            raise PermissionDenied('Only active superusers can use Login-as.')

        target = get_object_or_404(User, pk=user_id)
        change_url = reverse('myadmin:accounts_user_change', args=[user_id])

        if target.is_superuser and target.pk != request.user.pk:
            messages.error(request, _('You cannot log in as another superuser.'))
            return HttpResponseRedirect(change_url)

        if not target.is_active:
            messages.error(request, _('This user is inactive.'))
            return HttpResponseRedirect(change_url)

        tokens = generate_auth_tokens(target)
        logger.info('admin %s logged in as user %s', request.user.email, target.email)

        query = urlencode({
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'redirect': '/',
        })
        return HttpResponseRedirect(f'{settings.FRONTEND_URL}/admin-login?{query}')


class PasswordCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'used')
    search_fields = ('user__email', 'code')
    list_filter = ('used', 'created_at')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        # Don't allow manual creation from admin
        return False


admin_site.register(User, VersionaUserAdmin)
admin_site.register(PasswordCode, PasswordCodeAdmin)
