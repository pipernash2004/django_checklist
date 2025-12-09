from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from pytz import common_timezones

class CustomUser(AbstractUser): 
    USER_TYPE_CHOICES = (
        ('company_user', _('Company User')),
        ('individual', _('Individual')),
        ('visitor', _('Visitor')),
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='individual',
        verbose_name=_("User Type")
    )

    TIMEZONE_CHOICES = [(tz, tz) for tz in common_timezones]

    user_timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='Africa/Harare',
        verbose_name=_("User Timezone")
    )

    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    is_2fa_enabled = models.BooleanField(default=False)

    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True, verbose_name=_("Profile Picture"))
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name=_("Phone Number"))

    role = models.CharField(
        max_length=50,
        choices=[
            ('client', _('Client')),
            ('funeral_director', _('Funeral Director')),
            ('staff', _('Staff')),
            ('admin', _('Admin')),
            ('crew', _('Crew')),
        ],
        default='client',
        verbose_name=_("Role")
    )

    organization = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Organization"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='custom_user_groups',
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_permissions',
    )

    email = models.EmailField(_("Email Address"), unique=True, blank=False, null=False)

    USERNAME_FIELD = 'username'

    def clean(self):
        #  override clean to add custom validation if needed
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()

        # Check if password is already hashed
        if self.password and not self.password.startswith('pbkdf2_'):
            # Hash the password if it's not already hashed
            self.set_password(self.password)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
