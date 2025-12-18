from django.contrib import admin
from django.db.models import Count, Q, Max
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .model import (
    Checklist,
    Section,
    ListItem,
    ListItemProgress,
    CrewMemberChecklist,
    ChecklistType,
)
from management.admin import muzukuru_admin_site


# ------------------------------------------------------
# INLINES
# ------------------------------------------------------

class SectionInline(admin.TabularInline):
    """Sections belong to a Checklist"""
    model = Section
    extra = 0
    fields = ('name', 'description', 'order')
    ordering = ('order',)


class ListItemInline(admin.TabularInline):
    """List items belong to a Section"""
    model = ListItem
    extra = 0
    fields = ('name', 'description')


# ------------------------------------------------------
# CHECKLIST TYPE
# ------------------------------------------------------

@admin.register(ChecklistType, site=muzukuru_admin_site)
class ChecklistTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

    fieldsets = (
        (None, {'fields': ('name', 'description')}),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_by', 'updated_by')


# ------------------------------------------------------
# CHECKLIST
# ------------------------------------------------------

@admin.register(Checklist, site=muzukuru_admin_site)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('name', 'checklist_type', 'phase', 'created_at')
    list_filter = ('phase', 'checklist_type')
    search_fields = ('name', 'description', 'notes')
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'checklist_type', 'description', 'roles', 'phase', 'notes')
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_by', 'updated_by')
    filter_horizontal = ('roles',)
    inlines = [SectionInline]


# ------------------------------------------------------
# SECTION
# ------------------------------------------------------

@admin.register(Section, site=muzukuru_admin_site)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'checklist', 'order')
    list_filter = ('checklist',)
    search_fields = ('name', 'description', 'checklist__name')
    ordering = ('checklist', 'order')
    autocomplete_fields = ['checklist']
    inlines = [ListItemInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'checklist', 'order')
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_by', 'updated_by')


# ------------------------------------------------------
# LIST ITEM (TEMPLATE ONLY – NO STATUS)
# ------------------------------------------------------

@admin.register(ListItem, site=muzukuru_admin_site)
class ListItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'created_at')
    list_filter = ('section__checklist__phase', 'section')
    search_fields = ('name', 'description')
    ordering = ('section__order', 'name')
    autocomplete_fields = ['section']

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'section')
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_by', 'updated_by')


# ------------------------------------------------------
# CREW MEMBER CHECKLIST (COMPUTED STATUS)
# ------------------------------------------------------

@admin.register(CrewMemberChecklist, site=muzukuru_admin_site)
class CrewMemberChecklistAdmin(admin.ModelAdmin):
    list_display = (
        'crew_member',
        'checklist',
        'stream',
        'status_display',
        'progress_display',
        'created_at',
    )
    list_filter = ('checklist__phase', 'checklist', 'stream')
    search_fields = (
        'crew_member__user__username',
        'crew_member__user__first_name',
        'crew_member__user__last_name',
        'checklist__name',
    )
    autocomplete_fields = ['crew_member', 'checklist', 'assigned_by']
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('crew_member', 'checklist', 'stream', 'assigned_by')
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            total_items=Count('item_progress'),
            completed_items=Count('item_progress', filter=Q(item_progress__completed=True)),
            last_completed_at=Max('item_progress__completed_at'),
        ).select_related('crew_member__user', 'checklist', 'stream')

    def status_display(self, obj):
        if obj.total_items == 0:
            return 'pending'
        if obj.completed_items == 0:
            return 'pending'
        if obj.completed_items < obj.total_items:
            return 'in_progress'
        return 'completed'

    status_display.short_description = 'Status'

    def progress_display(self, obj):
        if obj.total_items == 0:
            return '0%'
        percent = int((obj.completed_items / obj.total_items) * 100)
        return format_html('<strong>{}%</strong>', percent)

    progress_display.short_description = 'Progress'


# ------------------------------------------------------
# LIST ITEM PROGRESS 
# ------------------------------------------------------

@admin.register(ListItemProgress, site=muzukuru_admin_site)
class ListItemProgressAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'item', 'completed', 'completed_at')
    list_filter = ('completed', 'completed_at')
    search_fields = (
        'assignment__crew_member__user__username',
        'assignment__crew_member__user__first_name',
        'assignment__crew_member__user__last_name',
        'item__name',
    )
    autocomplete_fields = ['assignment', 'item']
    ordering = ('-completed_at',)

    fieldsets = (
        (None, {
            'fields': ('assignment', 'item', 'completed', 'completed_at')
        }),
    )
    readonly_fields = ('completed_at',)
