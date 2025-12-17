from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Role Name")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_create_by',
        verbose_name=_("Created By")
    )
    last_updated_by = models.ForeignKey(
       settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_last_updated_by',
        verbose_name=_("Created By")
    )


    def save(self, *args, **kwargs):
        """
        Override the save method to ensure the name field is always in uppercase.
        """
        self.name = self.name.upper()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")


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
    
    CHECKLIST_CHOICES = [
        ('pre-stream', 'Pre-Stream'),
        ('on-stream', 'On-Stream'),
        ('post-stream', 'Post-Stream'),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    checklist_type = models.ForeignKey(ChecklistType, on_delete=models.CASCADE, related_name='checklist_type_checklists', null=True,  
    blank=True)
    roles = models.ManyToManyField(
        Role,
        related_name='checklists_roles',
        blank=True,
        help_text="Roles allowed or responsible for this checklist"
    )
    notes = models.TextField(blank=True, null=True)
    phase = models.CharField(
    max_length=20,
    choices=CHECKLIST_CHOICES)
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
    
        type_name = self.checklist_type.name if self.checklist_type else "No Type"
        return f"{self.name} is added to ({type_name})"

    
    class Meta:
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"
        unique_together = ('name', 'checklist_type')


class Sections(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='sections')
    checklist_type = models.ForeignKey(ChecklistType, on_delete=models.CASCADE, related_name='checklisttype_sections' ,null=True,  
    blank=True)
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
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='checklist_progress')
    items = models.ForeignKey('ListItem',  related_name='checklist_progress_items', on_delete=models.CASCADE ,null=True,  
    blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_checklist_progress'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return f"Progress of {self.user} on {self.checklist.name}"

    class Meta:
        verbose_name = "Checklist Progress"
        verbose_name_plural = "Checklist Progress Records"
        unique_together = ('items', 'user')



class ListItem(models.Model):

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.CASCADE , related_name='listitem_set', null=True)
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
        
      
        section_name = self.section.name if self.section else "No Type"
        return f"{self.name} is added to the({section_name})"

    class Meta:
        verbose_name = "List Item"
        verbose_name_plural = "List Items"
