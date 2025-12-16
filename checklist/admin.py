from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html
from .models import Role, ChecklistType, Checklist, Sections, ListItem, ChecklistProgress


# ============================================================
# ROLE ADMIN
# ============================================================

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description_short', 'checklist_count', 'created_at', 'created_by']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'last_updated_by']
    ordering = ['name']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description')
        }),
        (_('System Fields'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'last_updated_by'),
            'classes': ('collapse',)
        }),
    )

    def description_short(self, obj):
        """Display truncated description."""
        return obj.description[:50] + '...' if obj.description and len(obj.description) > 50 else obj.description
    description_short.short_description = _('Description')

    def checklist_count(self, obj):
        """Display count of checklists using this role."""
        count = obj.checklists_roles.count()
        return format_html(
            '<span style="background-color: #417690; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    checklist_count.short_description = _('Checklists')

    def save_model(self, request, obj, form, change):
        """Set created_by/last_updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# LIST ITEM INLINE
# ============================================================

class ListItemInline(admin.TabularInline):
    model = ListItem
    extra = 1
    fields = ['name', 'description', 'created_by', 'created_at']
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'last_updated_by']
    can_delete = True

    def save_formset(self, request, form, formset, change):
        """Set user automatically for new items."""
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.created_by = request.user
            instance.last_updated_by = request.user
        formset.save()


# ============================================================
# SECTIONS INLINE
# ============================================================

class SectionsInline(admin.TabularInline):
    model = Sections
    extra = 1
    fields = ['name', 'description', 'checklist_type', 'order', 'created_by']
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'last_updated_by']
    can_delete = True

    def save_formset(self, request, form, formset, change):
        """Set user automatically for new sections."""
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.created_by = request.user
            instance.last_updated_by = request.user
        formset.save()


# ============================================================
# SECTIONS ADMIN (with nested ListItems)
# ============================================================

@admin.register(Sections)
class SectionsAdmin(admin.ModelAdmin):
    list_display = ['name', 'checklist_link', 'checklist_type', 'order', 'item_count', 'created_at']
    list_filter = ['checklist', 'checklist_type', 'created_at', 'order']
    search_fields = ['name', 'description', 'checklist__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'last_updated_by', 'item_count']
    ordering = ['checklist', 'order']
    inlines = [ListItemInline]

    fieldsets = (
        (_('Section Information'), {
            'fields': ('name', 'description', 'checklist', 'checklist_type', 'order')
        }),
        (_('Statistics'), {
            'fields': ('item_count',),
            'classes': ('collapse',)
        }),
        (_('System Fields'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'last_updated_by'),
            'classes': ('collapse',)
        }),
    )

    def checklist_link(self, obj):
        """Display clickable checklist link."""
        url = reverse('admin:checklist_checklist_change', args=[obj.checklist.id])
        return format_html('<a href="{}">{}</a>', url, obj.checklist.name)
    checklist_link.short_description = _('Checklist')

    def item_count(self, obj):
        """Display count of list items in section."""
        count = obj.listitem_set.count()
        return format_html(
            '<span style="background-color: #417690; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    item_count.short_description = _('Items')

    def save_model(self, request, obj, form, change):
        """Set created_by/last_updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# CHECKLIST TYPE ADMIN
# ============================================================

@admin.register(ChecklistType)
class ChecklistTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description_short', 'checklist_count', 'section_count', 'created_at', 'created_by']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'last_updated_by', 'stats']
    ordering = ['name']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description')
        }),
        (_('Statistics'), {
            'fields': ('stats',),
            'classes': ('collapse',)
        }),
        (_('System Fields'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'last_updated_by'),
            'classes': ('collapse',)
        }),
    )

    def description_short(self, obj):
        """Display truncated description."""
        return obj.description[:50] + '...' if obj.description and len(obj.description) > 50 else obj.description
    description_short.short_description = _('Description')

    def checklist_count(self, obj):
        """Display count of checklists with this type."""
        count = obj.checklist_type_checklists.count()
        return format_html(
            '<span style="background-color: #417690; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    checklist_count.short_description = _('Checklists')

    def section_count(self, obj):
        """Display count of sections for this type."""
        count = obj.checklisttype_sections.count()
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    section_count.short_description = _('Sections')

    def stats(self, obj):
        """Display comprehensive statistics."""
        checklists = obj.checklist_type_checklists.count()
        sections = obj.checklisttype_sections.count()
        items = ListItem.objects.filter(section__checklist_type=obj).count()
        
        return format_html(
            '<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
            '<p><strong>Checklists:</strong> {}</p>'
            '<p><strong>Sections:</strong> {}</p>'
            '<p><strong>List Items:</strong> {}</p>'
            '</div>',
            checklists, sections, items
        )
    stats.short_description = _('Statistics')

    def save_model(self, request, obj, form, change):
        """Set created_by/last_updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# CHECKLIST ADMIN (Main - with nested creation)
# ============================================================

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ['name', 'checklist_type_link', 'phase_badge', 'role_count', 'section_count', 'created_at', 'created_by']
    list_filter = ['checklist_type', 'phase', 'created_at']
    search_fields = ['name', 'description', 'checklist_type__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'last_updated_by', 'stats']
    filter_horizontal = ['roles']
    ordering = ['-created_at']
    inlines = [SectionsInline]

    fieldsets = (
        (_('Checklist Information'), {
            'fields': ('name', 'description', 'checklist_type', 'phase', 'notes')
        }),
        (_('Roles & Permissions'), {
            'fields': ('roles',),
            'description': _('Select roles that are allowed or responsible for this checklist')
        }),
        (_('Statistics'), {
            'fields': ('stats',),
            'classes': ('collapse',)
        }),
        (_('System Fields'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'last_updated_by'),
            'classes': ('collapse',)
        }),
    )

    def checklist_type_link(self, obj):
        """Display clickable checklist type link."""
        if obj.checklist_type:
            url = reverse('admin:checklist_checklisttype_change', args=[obj.checklist_type.id])
            return format_html('<a href="{}">{}</a>', url, obj.checklist_type.name)
        return _('No Type')
    checklist_type_link.short_description = _('Checklist Type')

    def phase_badge(self, obj):
        """Display phase with color badge."""
        colors = {
            'pre-stream': '#ffc107',
            'on-stream': '#28a745',
            'post-stream': '#dc3545',
        }
        color = colors.get(obj.phase, '#6c757d')
        label = obj.get_phase_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color, label
        )
    phase_badge.short_description = _('Phase')

    def role_count(self, obj):
        """Display count of assigned roles."""
        count = obj.roles.count()
        return format_html(
            '<span style="background-color: #417690; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    role_count.short_description = _('Roles')

    def section_count(self, obj):
        """Display count of sections."""
        count = obj.sections.count()
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    section_count.short_description = _('Sections')

    def stats(self, obj):
        """Display comprehensive statistics."""
        sections = obj.sections.count()
        items = ListItem.objects.filter(section__checklist=obj).count()
        progress = obj.checklist_progress.count()
        
        return format_html(
            '<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
            '<p><strong>Sections:</strong> {}</p>'
            '<p><strong>List Items:</strong> {}</p>'
            '<p><strong>Progress Records:</strong> {}</p>'
            '</div>',
            sections, items, progress
        )
    stats.short_description = _('Statistics')

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """Set created_by/last_updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)

    @transaction.atomic
    def save_related(self, request, form, formsets, change):
        """Handle roles assignment and nested saves."""
        super().save_related(request, form, formsets, change)


# ============================================================
# LIST ITEM ADMIN
# ============================================================

@admin.register(ListItem)
class ListItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'section_link', 'checklist_link', 'progress_count', 'created_at', 'created_by']
    list_filter = ['section__checklist', 'section', 'created_at']
    search_fields = ['name', 'description', 'section__name', 'section__checklist__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'last_updated_by', 'progress_count']
    ordering = ['section', 'name']

    fieldsets = (
        (_('Item Information'), {
            'fields': ('name', 'description', 'section')
        }),
        (_('Statistics'), {
            'fields': ('progress_count',),
            'classes': ('collapse',)
        }),
        (_('System Fields'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'last_updated_by'),
            'classes': ('collapse',)
        }),
    )

    def section_link(self, obj):
        """Display clickable section link."""
        url = reverse('admin:checklist_sections_change', args=[obj.section.id])
        return format_html('<a href="{}">{}</a>', url, obj.section.name)
    section_link.short_description = _('Section')

    def checklist_link(self, obj):
        """Display clickable checklist link."""
        url = reverse('admin:checklist_checklist_change', args=[obj.section.checklist.id])
        return format_html('<a href="{}">{}</a>', url, obj.section.checklist.name)
    checklist_link.short_description = _('Checklist')

    def progress_count(self, obj):
        """Display count of progress records."""
        count = obj.checklist_progress_items.count()
        return format_html(
            '<span style="background-color: #417690; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    progress_count.short_description = _('Progress Records')

    def save_model(self, request, obj, form, change):
        """Set created_by/last_updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# CHECKLIST PROGRESS ADMIN
# ============================================================

@admin.register(ChecklistProgress)
class ChecklistProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'checklist_link', 'item_link', 'status_badge', 'progress_percentage', 'created_at', 'updated_at']
    list_filter = ['status', 'checklist', 'created_at']
    search_fields = ['user__username', 'user__email', 'checklist__name', 'items__name']
    readonly_fields = ['created_at', 'updated_at', 'progress_percentage']
    ordering = ['-created_at']

    fieldsets = (
        (_('Progress Information'), {
            'fields': ('user', 'checklist', 'items', 'status')
        }),
        (_('Progress Details'), {
            'fields': ('progress_percentage',),
            'classes': ('collapse',)
        }),
        (_('Timeline'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def checklist_link(self, obj):
        """Display clickable checklist link."""
        url = reverse('admin:checklist_checklist_change', args=[obj.checklist.id])
        return format_html('<a href="{}">{}</a>', url, obj.checklist.name)
    checklist_link.short_description = _('Checklist')

    def item_link(self, obj):
        """Display clickable list item link."""
        if obj.items:
            url = reverse('admin:checklist_listitem_change', args=[obj.items.id])
            return format_html('<a href="{}">{}</a>', url, obj.items.name)
        return _('No Item')
    item_link.short_description = _('Item')

    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            'pending': '#6c757d',
            'in_progress': '#ffc107',
            'completed': '#28a745',
            'blocked': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        label = obj.get_status_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color, label
        )
    status_badge.short_description = _('Status')

    def progress_percentage(self, obj):
        """Calculate and display progress percentage."""
        total_items = obj.checklist.sections.aggregate(
            count=Count('listitem')
        )['count'] or 0
        
        if total_items == 0:
            percentage = 0
        else:
            completed = obj.checklist.checklist_progress.filter(status='completed').count()
            percentage = (completed / total_items) * 100
        
        return format_html(
            '<div style="background-color: #f0f0f0; padding: 5px; border-radius: 3px;">'
            '<strong>{:.1f}%</strong> Complete'
            '</div>',
            percentage
        )
    progress_percentage.short_description = _('Progress %')

    def has_add_permission(self, request):
        """Allow only staff to create progress records."""
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        """Allow only staff to delete progress records."""
        return request.user.is_staff