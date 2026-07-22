from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.admin_site import admin_site
from core.models import StagingPhaseBanner


# ============================================================================
# STAGING PHASE BANNER
# ============================================================================
# DO NOT DELETE this admin: it controls the staging review banner shown to
# clients. Hide via the `is_visible` toggle / "Hide banner" action — never
# unregister or remove the model. See `pre-staging-cleanup` skill for details.

class StagingPhaseBannerAdmin(admin.ModelAdmin):
    list_display = ('current_phase', 'is_visible', 'started_at', 'expires_at', 'days_remaining')
    readonly_fields = ('expires_at', 'days_remaining', 'is_expired', 'updated_at')
    fieldsets = (
        (_('Visibility'), {'fields': ('is_visible',)}),
        (_('Phase'), {'fields': ('current_phase', 'started_at', 'expires_at', 'days_remaining', 'is_expired')}),
        (_('Durations (calendar days)'), {'fields': ('design_duration_days', 'development_duration_days')}),
        (_('Contact'), {'fields': ('contact_whatsapp', 'contact_email')}),
        (_('Audit'), {'fields': ('updated_at',)}),
    )
    actions = ['start_design_phase', 'start_development_phase', 'show_banner', 'hide_banner']

    def has_add_permission(self, request):
        return not StagingPhaseBanner.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def start_design_phase(self, request, queryset):
        for obj in queryset:
            obj.current_phase = StagingPhaseBanner.PHASE_DESIGN
            obj.started_at = timezone.now()
            obj.save()
        self.message_user(request, _('Design phase started. Countdown reset.'))
    start_design_phase.short_description = _('▶ Start design phase (resets countdown)')

    def start_development_phase(self, request, queryset):
        for obj in queryset:
            obj.current_phase = StagingPhaseBanner.PHASE_DEVELOPMENT
            obj.started_at = timezone.now()
            obj.save()
        self.message_user(request, _('Development phase started. Countdown reset.'))
    start_development_phase.short_description = _('▶ Start development phase (resets countdown)')

    def show_banner(self, request, queryset):
        queryset.update(is_visible=True)
        self.message_user(request, _('Banner shown.'))
    show_banner.short_description = _('👁 Show banner')

    def hide_banner(self, request, queryset):
        queryset.update(is_visible=False)
        self.message_user(request, _('Banner hidden.'))
    hide_banner.short_description = _('🙈 Hide banner')


admin_site.register(StagingPhaseBanner, StagingPhaseBannerAdmin)
