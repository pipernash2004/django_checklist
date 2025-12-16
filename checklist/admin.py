from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ChecklistType, Checklist, ListItem, ChecklistProgress,Sections
 # your custom admin site

# class ChecklistItemInline(admin.TabularInline):
#     model = ChecklistItem
#     extra = 1
#     fields = ('list_item',)
#     # No readonly fields needed here, as creation date might not be on ChecklistItem

class ChecklistTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
    )


class SectionsAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
    )


class ChecklistProgressAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
    )


class ChecklistTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
    )
class ListItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'status')
    list_filter = ('type', 'status')
    search_fields = ('name', 'description', 'type__name')
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'type', 'status')
        }),
    )

class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    list_filter = ('type',)
    search_fields = ('name', 'description', 'type__name')
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'type')
        }),
    )



class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'list_item')
    list_filter = ('checklist__type',)
    search_fields = ('checklist__name', 'list_item__name')
    ordering = ('checklist', 'list_item')

    fieldsets = (
        (None, {
            'fields': ('checklist', 'list_item')
        }),
    )


admin.site.register(ChecklistType, ChecklistTypeAdmin)
admin.site.register(ListItem, ListItemAdmin)
admin.site.register(Checklist, ChecklistAdmin)
admin.site.register(ChecklistProgress, ChecklistProgressAdmin)   
admin.site.register(Sections, SectionsAdmin)
