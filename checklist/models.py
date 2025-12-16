from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class ChecklistType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checklisttype_create_by',
        verbose_name=_("Created By")
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checklisttype_last_updated_by',
        verbose_name=_("Last Updated By")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Checklist Type"
        verbose_name_plural = "Checklist Types"


class Checklist(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    checklist_type = models.ForeignKey(ChecklistType, on_delete=models.CASCADE)
    items = models.ManyToManyField('ListItem', through='ChecklistItem', related_name='checklists')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checklist_create_by',
        verbose_name=_("Created By")
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checklist_last_updated_by',
        verbose_name=_("Last Updated By")
    )

    def __str__(self):
        return f"{self.name} ({self.type.name})"

    
    class Meta:
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"
        unique_together = ('name', 'checklist_type')


class Sections(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='sections')
    checklist_type = models.ForeignKey(ChecklistType, on_delete=models.CASCADE, related_name='checklisttype_sections')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sections_create_by',
        verbose_name=_("Created By")
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sections_last_updated_by',
        verbose_name=_("Last Updated By")
    )

    def __str__(self):
        return f"{self.name} - {self.checklist.name}"

    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        ordering = ['order']
        unique_together = ('checklist', 'checklist_type', 'name')


class ChecklistProgress(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE)
    
    #  need the stream id here
    stream = models.ForeignKey(Checklist, on_delete=models.CASCADE)
    items = models.ForeignKey('ListItem',  related_name='checklist_progress_items')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='checklist_progress'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return f"Progress of {self.user} on {self.checklist.name}"

    class Meta:
        verbose_name = "Checklist Progress"
        verbose_name_plural = "Checklist Progress Records"
        unique_together = ('items', 'user', 'stream') # the stream id here



class ListItem(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listitem_create_by',
        verbose_name=_("Created By")
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listitem_last_updated_by',
        verbose_name=_("Last Updated By")
    )

    def __str__(self):
        return f"{self.name} ({self.type.name})"

    class Meta:
        verbose_name = "List Item"
        verbose_name_plural = "List Items"


