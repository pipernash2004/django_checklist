from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

# Register the project-specific CustomUser model with the admin site.
# We subclass Django's built-in `UserAdmin` to reuse the default user
# forms, password handling, and permissions UI, and then add our
# application-specific fields (user_type, role, etc.) so administrators
# can manage them from the admin interface.
from .models import CustomUser
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError


class CustomUserAdmin(UserAdmin):
	"""Admin for the custom user model.

	We extend `UserAdmin` to keep Django's user management niceties
	(password hashing forms, permission widgets) and then expose the
	additional fields defined on `CustomUser` so staff can manage them.
	"""
	model = CustomUser

	# Columns shown in the changelist (user list) view. Chosen to give
	# a quick overview of identity, account type and admin privileges.
	list_display = (
		'username', 'email', 'first_name', 'last_name',
		'user_type', 'role', 'is_staff', 'is_superuser'
	)

	# Filters in the right-hand sidebar to quickly narrow users by
	# business role or admin/staff status.
	list_filter = ('user_type', 'role', 'is_staff', 'is_superuser')

	# Search fields used by the admin search box. Using these fields
	# makes it fast to find a user by username, email or name.
	search_fields = ('username', 'email', 'first_name', 'last_name')
	ordering = ('username',)

	# Fieldsets group fields in the user change form. Grouping makes
	# the form easier to scan and maintain (personal, business, security,
	# permissions, dates).
	fieldsets = (
		(None, {'fields': ('username', 'password')}),
		(_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'profile_picture', 'phone_number')}),
		(_('Business info'), {'fields': ('user_type', 'role', 'organization')}),
		(_('Security'), {'fields': ('is_2fa_enabled', 'totp_secret', 'is_verified')}),
		(_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		(_('Important dates'), {'fields': ('last_login', 'date_joined')}),
	)

	# Fields shown on the add-user form. We include username/email and
	# password fields plus the primary business fields so admins can
	# create a user in one step.
	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('username', 'email', 'password1', 'password2', 'user_type', 'role'),
		}),
	)

	# Use custom forms so we can enforce business rules in the admin,
	# for example requiring an organization when `user_type` is
	# 'company_user'. These forms run server-side validation before
	# saving objects from the admin interface.
    
	# The `form` is used for the change view; `add_form` is for the
	# add-user view.
    
	# We'll define the form classes below and assign them here.
	form = None
	add_form = None


admin.site.register(CustomUser, CustomUserAdmin)


# --- Admin forms with business validation ---
class CustomUserCreationForm(UserCreationForm):
	class Meta:
		model = CustomUser
		fields = ('username', 'email', 'user_type', 'role', 'organization')

	def clean(self):
		cleaned = super().clean()
		user_type = cleaned.get('user_type')
		organization = cleaned.get('organization')
		# Business rule: company users must have an organization set
		if user_type == 'company_user' and not organization:
			raise ValidationError({'organization': 'Company users must have an organization.'})
		return cleaned


class CustomUserChangeForm(UserChangeForm):
	class Meta:
		model = CustomUser
		fields = ('username', 'email', 'user_type', 'role', 'organization')

	def clean(self):
		cleaned = super().clean()
		user_type = cleaned.get('user_type')
		organization = cleaned.get('organization')
		if user_type == 'company_user' and not organization:
			raise ValidationError({'organization': 'Company users must have an organization.'})
		return cleaned


# Assign the forms to the admin class after definitions
CustomUserAdmin.form = CustomUserChangeForm
CustomUserAdmin.add_form = CustomUserCreationForm
