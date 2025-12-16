from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ChecklistType, Checklist, Sections, ListItem, ChecklistProgress


# ============================================================
# CHECKLIST TYPE ADMIN
# ============================================================

@admin.register(ChecklistType)
class ChecklistTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'created_by']
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
    fields = ['name', 'description', 'created_by']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'last_updated_by']


# ============================================================
# SECTIONS ADMIN
# ============================================================

@admin.register(Sections)
class SectionsAdmin(admin.ModelAdmin):
    list_display = ['name', 'checklist', 'checklist_type', 'order', 'created_at']
    list_filter = ['checklist', 'checklist_type', 'created_at']
    search_fields = ['name', 'description', 'checklist__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'last_updated_by']
    ordering = ['order']
    inlines = [ListItemInline]

    fieldsets = (
        (_('Section Information'), {
            'fields': ('name', 'description', 'checklist', 'checklist_type', 'order')
        }),
        (_('System Fields'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'last_updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by/last_updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# SECTIONS INLINE
# ============================================================

class SectionsInline(admin.TabularInline):
    model = Sections
    extra = 1
    fields = ['name', 'order', 'checklist_type']
    readonly_fields = ['created_by', 'last_updated_by']


# ============================================================
# CHECKLIST ADMIN
# ============================================================

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ['name', 'checklist_type', 'created_at', 'created_by']
    list_filter = ['checklist_type', 'created_at']
    search_fields = ['name', 'description', 'checklist_type__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'last_updated_by']
    ordering = ['name']
    inlines = [SectionsInline]

    fieldsets = (
        (_('Checklist Information'), {
            'fields': ('name', 'description', 'checklist_type')
        }),
        (_('System Fields'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'last_updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by/last_updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.last_updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# LIST ITEM ADMIN
# ============================================================

@admin.register(ListItem)
class ListItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'section', 'created_at', 'created_by']
    list_filter = ['section__checklist', 'created_at']
    search_fields = ['name', 'description', 'section__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'last_updated_by']
    ordering = ['name']

    fieldsets = (
        (_('Item Information'), {
            'fields': ('name', 'description', 'section')
        }),
        (_('System Fields'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'last_updated_by'),
            'classes': ('collapse',)
        }),
    )

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
    list_display = ['user', 'checklist', 'items', 'status', 'created_at']
    list_filter = ['status', 'checklist', 'created_at']
    search_fields = ['user__username', 'checklist__name', 'items__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        (_('Progress Information'), {
            'fields': ('user', 'checklist', 'items', 'status')
        }),
        (_('Timeline'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
