from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User

from .models import AdminProfile


def has_developer_workspace(request):
	profile = getattr(request.user, 'admin_profile', None)
	if profile:
		return profile.interface_mode == AdminProfile.DEVELOPER
	return request.user.is_superuser


class AdminProfileInline(admin.StackedInline):
	model = AdminProfile
	can_delete = False
	extra = 1
	verbose_name = 'Admin workspace'
	verbose_name_plural = 'Admin workspace'


class SiteUserAdmin(UserAdmin):
	inlines = (AdminProfileInline,)

	def has_module_permission(self, request):
		return has_developer_workspace(request)


class DeveloperGroupAdmin(admin.ModelAdmin):
	def has_module_permission(self, request):
		return has_developer_workspace(request)


admin.site.unregister(User)
admin.site.register(User, SiteUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, DeveloperGroupAdmin)
