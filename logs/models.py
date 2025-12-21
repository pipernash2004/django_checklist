from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

User = settings.AUTH_USER_MODEL



class SystemLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
    )

    user = models.ForeignKey(
    User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_logs'
    )
    action = models.CharField(
        max_length=255,
        choices=ACTION_CHOICES
    )
    table_name = models.CharField(
        max_length=100,
        help_text="Name of the database table affected"
    )
    record_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID of the affected record"
    )
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text="Details of changes made (for UPDATE actions)"
    )
    timestamp = models.DateTimeField(
        default=timezone.now
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    additional_info = models.TextField(
        null=True,
        blank=True,
        help_text="Additional context or details"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['table_name', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} on {self.table_name} at {self.timestamp}"

    @classmethod
    def log_action(cls, user, action, table_name, record_id=None, changes=None, ip_address=None, additional_info=None):
        """
        Helper method to create a log entry
        """
        log = cls(
            user=user,
            action=action,
            table_name=table_name,
            record_id=record_id,
            changes=changes,
            ip_address=ip_address,
            additional_info=additional_info
        )
        log.save()
        return log