from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Song, SortFilter, God, Raaga, ContactMessage


def has_developer_workspace(request):
    profile = getattr(request.user, 'admin_profile', None)
    if profile:
        return profile.interface_mode == 'developer'
    return request.user.is_superuser


class DeveloperOnlyAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return has_developer_workspace(request) and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return has_developer_workspace(request) and super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return has_developer_workspace(request) and super().has_change_permission(request, obj)

    def has_add_permission(self, request):
        if not has_developer_workspace(request):
            return request.user.is_staff
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return has_developer_workspace(request) and super().has_delete_permission(request, obj)


class SongAdmin(admin.ModelAdmin):
    list_display = ('name', 'god', 'Raaga', 'sort_filter')
    list_filter = ('god', 'Raaga', 'sort_filter')
    search_fields = ('name', 'description', 'god__name', 'Raaga__name')
    list_select_related = ('god', 'Raaga', 'sort_filter')
    ordering = ('name',)

    def has_module_permission(self, request):
        if not has_developer_workspace(request):
            return request.user.is_staff
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if not has_developer_workspace(request):
            return request.user.is_staff
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if not has_developer_workspace(request):
            return request.user.is_staff
        return super().has_change_permission(request, obj)

    def has_add_permission(self, request):
        if not has_developer_workspace(request):
            return request.user.is_staff
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        if not has_developer_workspace(request):
            return False
        return super().has_delete_permission(request, obj)


admin.site.register(Song, SongAdmin)

class SortFilterAdmin(DeveloperOnlyAdmin):
    list_display = ('name', 'description')


admin.site.register(SortFilter, SortFilterAdmin)

class GodAdmin(DeveloperOnlyAdmin):
    list_display = ('name', 'description')

admin.site.register(God, GodAdmin)


class RaagaAdmin(DeveloperOnlyAdmin):
    list_display = ('name', 'description')

admin.site.register(Raaga, RaagaAdmin)


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'replied_at')
    actions = ['mark_as_replied']

    def mark_as_replied(self, request, queryset):
        queryset.update(status=ContactMessage.STATUS_REPLIED, replied_at=timezone.now())

    mark_as_replied.short_description = 'Mark selected messages as replied'

    def response_change(self, request, obj):
        if '_reply' in request.POST:
            reply_message = request.POST.get('reply_message', '').strip()
            if reply_message:
                send_mail(
                    subject=f'Re: {obj.subject}',
                    message=reply_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[obj.email],
                    fail_silently=False,
                )
                obj.status = ContactMessage.STATUS_REPLIED
                obj.replied_at = timezone.now()
                obj.save()
                self.message_user(request, f'Reply sent to {obj.email}.')
                return None
        return super().response_change(request, obj)


admin.site.register(ContactMessage, ContactMessageAdmin)