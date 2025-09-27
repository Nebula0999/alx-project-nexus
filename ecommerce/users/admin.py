from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	fieldsets = (
		(None, {'fields': ('username', 'password')}),
		(_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
		(_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
		(_('Important dates'), {'fields': (
			'last_login', 'created_at', 'updated_at', 'verification_email_last_attempt', 'verification_email_last_success', 'verification_email_attempts'
		)}),
	)

	# Non-editable / automatically managed fields
	readonly_fields = (
		'last_login', 'created_at', 'updated_at',
		'verification_email_last_attempt', 'verification_email_last_success', 'verification_email_attempts'
	)
	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
		}),
	)
	list_display = (
		'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_verified',
		'verification_email_attempts', 'verification_email_last_success'
	)
	search_fields = ('username', 'email', 'first_name', 'last_name')
	ordering = ('username',)
