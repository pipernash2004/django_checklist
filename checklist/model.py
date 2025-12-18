from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings



# ------------------------------------------------------
# ABSTRACT MODELS
# ------------------------------------------------------

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True), verbose_name=_("Updated At")

    class Meta:
        abstract = True


class UserStampedModel(models.Model):
    created_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_%(class)s",
        verbose_name=_("Created By")
    )
    updated_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_%(class)s",
        verbose_name=_("Last Updated By")
    )

    class Meta:
        abstract = True

#  category for checklist 
class ChecklistType(TimeStampedModel, UserStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Checklist Type"
        verbose_name_plural = "Checklist Types"

#  the checklist template designed by the admin 
class Checklist(TimeStampedModel, UserStampedModel):
    
    CHECKLIST_CHOICES = [
        ('pre_stream', 'Pre_Stream'),
        ('on_stream', 'On_Stream'),
        ('post_stream', 'Post_Stream'),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    checklist_type = models.ForeignKey(ChecklistType, on_delete=models.CASCADE, related_name='checklist_type_checklists', null=True,  
    blank=True)
    order = models.PositiveIntegerField(default=0)
    roles = models.ManyToManyField(
        'crew.Role',
        related_name='checklists',  # OK here — primary usage
        blank=True,
        help_text=_("Roles responsible for or allowed to use this checklist"))
    notes = models.TextField(blank=True, null=True)
    phase = models.CharField(
    max_length=20,
    choices=CHECKLIST_CHOICES,default='on_stream')
  

    def __str__(self):
    
        type_name = self.checklist_type.name if self.checklist_type else "No Type"
        return f"{self.name} - ({type_name})"

    
    class Meta:
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"
        unique_together = ('name', 'checklist_type')
        ordering = ['order']


class Section(TimeStampedModel, UserStampedModel):

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='sections')
    order = models.PositiveIntegerField(default=0)
 
    def __str__(self):
        return f"{self.name} - {self.checklist.name}"

    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        ordering = ['order']
        unique_together = ('checklist',  'name') # the section must be unique in the checklist 

#  the instance from the template checklist
class CrewMemberChecklist(TimeStampedModel, UserStampedModel):
    crew_member = models.ForeignKey(
        'crew.CrewMember',
        on_delete=models.CASCADE,
        related_name='assigned_checklists',
        verbose_name=_("Crew Member")
    )
    checklist = models.ForeignKey(
        Checklist,
        on_delete=models.CASCADE,
        related_name='crew_assignments',
        verbose_name=_("Checklist")
    )
    assigned_by = models.ForeignKey(
        "authentication.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_crew_checklists',
        verbose_name=_("Assigned By"),
        help_text=_("The user who assigned this checklist to the crew member")
    )
    stream = models.ForeignKey(
        'stream.Stream',
        on_delete=models.CASCADE,
        related_name='stream_checklist_progress'
    )
    
   

    class Meta:
        unique_together = ('crew_member', 'checklist', 'stream')
        verbose_name = "Crew Member Checklist Assignment"
        verbose_name_plural = "Crew Member Checklist Assignments"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.crew_member} → {self.checklist.name}"


class ListItem(TimeStampedModel, UserStampedModel):

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE , related_name='items', null=False, blank=False)

    def __str__(self):
        
      
        section_name = self.section.name if self.section else "No Type"
        return f"{self.name} -({section_name})"


    class Meta:
        verbose_name = "List Item"
        verbose_name_plural = "List Items"
        unique_together = ('section', 'name')


class ListItemProgress(models.Model):
    assignment = models.ForeignKey(
        CrewMemberChecklist,
        on_delete=models.CASCADE,
        related_name='item_progress'
    )

    item = models.ForeignKey(
        ListItem,
        on_delete=models.CASCADE
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('assignment', 'item')

    def __str__(self):
        return f'{self.item.name} → {self.completed}'


