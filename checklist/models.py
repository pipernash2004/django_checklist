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
    type = models.ForeignKey(ChecklistType, on_delete=models.CASCADE)
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

    def add_item(self, item):
        if item.type != self.type:
            raise ValidationError("List item type must match the checklist type.")
        ChecklistItem.objects.create(checklist=self, list_item=item)

    class Meta:
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"


class ListItem(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type = models.ForeignKey(ChecklistType, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
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


class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE)
    list_item = models.ForeignKey(ListItem, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checklistitem_created_by',
        verbose_name=_("Created By")
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checklistitem_last_updated_by',
        verbose_name=_("Last Updated By")
    )

    class Meta:
        unique_together = ('checklist', 'list_item')
        verbose_name = "Checklist Item"
        verbose_name_plural = "Checklist Items"

    def clean(self):
        if self.checklist.type != self.list_item.type:
            raise ValidationError("List item type must match the checklist type.")

    def __str__(self):
        return f"{self.checklist.name} - {self.list_item.name}"
