from django.contrib import admin
from .models import SystemLog


@admin.register(SystemLog )
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'table_name', 'record_id', 'ip_address', 'additional_info')
    list_filter = ('action', 'table_name', 'timestamp', 'user')
    search_fields = ('user__username', 'table_name', 'record_id', 'additional_info', 'ip_address')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)  # Ensures latest logs appear first
    readonly_fields = (
        'user', 'action', 'table_name', 'record_id', 'changes',
        'timestamp', 'ip_address', 'additional_info'
    )
    fieldsets = (
        (None, {
            'fields': ('user', 'action', 'table_name', 'record_id')
        }),
        ('Details', {
            'fields': ('changes', 'ip_address', 'additional_info')
        }),
        ('Metadata', {
            'fields': ('timestamp',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # Optimize query with select_related for user and ensure ordering
        return super().get_queryset(request).select_related('user').order_by('-timestamp')