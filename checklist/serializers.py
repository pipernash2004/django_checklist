"""
DRF Serializers for checklist app with full validation and Swagger documentation.
Handles model conversion, JSON validation, field exposure, and business rules.
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import Role, ChecklistType, Checklist, Sections, ListItem, ChecklistProgress
from .services import (
    ChecklistService
  
)

User = get_user_model()


# ============================================================
# USER SERIALIZERS (for nested use)
# ============================================================

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for nested representations (id and username only)."""
    
    class Meta:
        model = User
        fields = ['id', 'username']
        read_only_fields = ['id', 'username']


# ============================================================
# ROLE SERIALIZERS
# ============================================================

class RoleListSerializer(serializers.ModelSerializer):
    """Serializer for listing roles with essential fields."""
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'created_at', 
            'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class RoleDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed role information."""
    created_by = UserBasicSerializer(read_only=True)
    last_updated_by = UserBasicSerializer(read_only=True)
    checklist_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'checklist_count',
            'created_at', 'updated_at', 'created_by', 'last_updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'last_updated_by']
    



class RoleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating roles."""
    
    class Meta:
        model = Role
        fields = ['name', 'description']
    
    def validate_name(self, value):
        """Validate role name is not empty and is unique."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Role name cannot be empty.")
            )
        # Uniqueness checks moved to service layer.
        return value.strip().upper()
    
    def validate_description(self, value):
        """Validate description field."""
        if value and len(value.strip()) > 2000:
            raise serializers.ValidationError(
                _("Description cannot exceed 2000 characters.")
            )
        return value or ""


# ============================================================
# CHECKLIST TYPE SERIALIZERS
# ============================================================

class ChecklistTypeListSerializer(serializers.ModelSerializer):
    """Serializer for listing checklist types."""
    created_by = UserBasicSerializer(read_only=True)
    checklist_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ChecklistType
        fields = [
            'id', 'name', 'description', 'checklist_count',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    # `checklist_count` should be provided/annotated by the view/service layer.


class ChecklistTypeDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed checklist type information."""
    created_by = UserBasicSerializer(read_only=True)
    last_updated_by = UserBasicSerializer(read_only=True)
    checklist_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ChecklistType
        fields = [
            'id', 'name', 'description', 'checklist_count',
            'created_at', 'updated_at', 'created_by', 'last_updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'last_updated_by']
    
    # `checklist_count` should be provided/annotated by the view/service layer.


class ChecklistTypeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating checklist types."""
    
    class Meta:
        model = ChecklistType
        fields = ['name', 'description']
    
    def validate_name(self, value):
        """Validate checklist type name."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Checklist type name cannot be empty.")
            )
        
        return value.strip()
    
    def validate_description(self, value):
        """Validate description field."""
        if value and len(value.strip()) > 2000:
            raise serializers.ValidationError(
                _("Description cannot exceed 2000 characters.")
            )
        return value or ""


# ============================================================
# SECTION SERIALIZERS
# ============================================================

class SectionBasicSerializer(serializers.ModelSerializer):
    """Serializer for basic section information."""
    
    class Meta:
        model = Sections
        fields = ['id', 'name', 'description', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class ListItemNestedSerializer(serializers.ModelSerializer):
    """Serializer for list items nested in sections (detail view).
    
    Used only for reading nested list items within sections.
    Exposes annotated progress_count from the prefetched queryset.
    """
    created_by = UserBasicSerializer(read_only=True)
    progress_count = serializers.SerializerMethodField()

    class Meta:
        model = ListItem
        fields = [
            'id', 'name', 'description', 'progress_count',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_progress_count(self, obj):
        """Get progress count from annotated field if available, else query."""
        # If the queryset was prefetched with annotation, use it
        if hasattr(obj, 'progress_count'):
            return obj.progress_count
        # Fallback for cases where annotation wasn't applied
        return obj.checklist_progress_items.count()


class SectionWithItemsSerializer(serializers.ModelSerializer):
    """Serializer for sections with nested list items (for detail/read view).
    
    This is the primary serializer for reading sections in detail views.
    It includes all nested list items using the ListItemNestedSerializer.
    Uses the actual reverse relation name 'listitem_set' from the ListItem model.
    
    Depends on proper prefetching in the view's get_queryset().
    """
    created_by = UserBasicSerializer(read_only=True)
    last_updated_by = UserBasicSerializer(read_only=True)
    # Use the actual reverse relation from ListItem model (listitem_set since no related_name specified)
    items = ListItemNestedSerializer(many=True, read_only=True, source='listitem_set')
    list_items_count = serializers.SerializerMethodField()

    class Meta:
        model = Sections
        fields = [
            'id', 'name', 'description', 'order', 'list_items_count',
            'items', 'created_at', 'updated_at', 'created_by', 'last_updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'last_updated_by']
    
    def get_list_items_count(self, obj):
        """Get list items count from annotated field if available, else query."""
        # If the queryset was annotated with list_items_count, use it
        if hasattr(obj, 'list_items_count'):
            return obj.list_items_count
        # Fallback for cases where annotation wasn't applied
        return obj.listitem_set.count()


class SectionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed section information."""
    created_by = UserBasicSerializer(read_only=True)
    last_updated_by = UserBasicSerializer(read_only=True)
    list_items_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Sections
        fields = [
            'id', 'name', 'description', 'order', 'list_items_count',
            'created_at', 'updated_at', 'created_by', 'last_updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'last_updated_by']
 


class SectionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating sections."""
    checklist_id = serializers.IntegerField(write_only=True)
    checklist_type_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Sections
        fields = ['name', 'description', 'order', 'checklist_id', 'checklist_type_id']
    
    def validate_name(self, value):
        """Validate section name."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Section name cannot be empty.")
            )
        
        if len(value.strip()) > 255:
            raise serializers.ValidationError(
                _("Section name cannot exceed 255 characters.")
            )
        
        return value.strip()
    
    def validate_order(self, value):
        """Validate order field."""
        if value < 0:
            raise serializers.ValidationError(
                _("Order must be a non-negative number.")
            )
        return value
    
    def validate_description(self, value):
        """Validate description field."""
        if value and len(value.strip()) > 2000:
            raise serializers.ValidationError(
                _("Description cannot exceed 2000 characters.")
            )
        return value or ""
    
    def validate(self, data):
        """Validate checklist existence and uniqueness."""
        # Existence, uniqueness and cross-model validations are handled in services.
        return data


# ============================================================
# LIST ITEM SERIALIZERS
# ============================================================

class ListItemBasicSerializer(serializers.ModelSerializer):
    """Serializer for basic list item information."""
    
    class Meta:
        model = ListItem
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class ListItemDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed list item information."""
    created_by = UserBasicSerializer(read_only=True)
    last_updated_by = UserBasicSerializer(read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    progress_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ListItem
        fields = [
            'id', 'name', 'description', 'section_name', 'progress_count',
            'created_at', 'updated_at', 'created_by', 'last_updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'last_updated_by']
    
  


class ListItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating list items."""
    section_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ListItem
        fields = ['name', 'description', 'section_id']
    
    def validate_name(self, value):
        """Validate list item name."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("List item name cannot be empty.")
            )
        
        if len(value.strip()) > 255:
            raise serializers.ValidationError(
                _("List item name cannot exceed 255 characters.")
            )
        
        return value.strip()
    
    def validate_description(self, value):
        """Validate description field."""
        if value and len(value.strip()) > 2000:
            raise serializers.ValidationError(
                _("Description cannot exceed 2000 characters.")
            )
        return value or ""
    
    def validate_section_id(self, value):
        """Validate section exists."""
        # Existence checks moved to service layer. Ensure positive id.
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                _("Invalid section id.")
            )
        return value


# ============================================================
# CHECKLIST SERIALIZERS
# ============================================================

class ChecklistListSerializer(serializers.ModelSerializer):
    """Serializer for listing checklists (lightweight, no nested sections/items)."""
    checklist_type = serializers.StringRelatedField()
    created_by = UserBasicSerializer(read_only=True)
    sections_count = serializers.IntegerField(read_only=True)
    roles_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Checklist
        fields = [
            'id', 'name', 'description', 'phase', 'checklist_type',
            'sections_count', 'roles_count', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

   

class ChecklistDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed checklist information with full section/item hierarchy.
    
    This is the primary read serializer for /checklists/{id}/ endpoint.
    It returns the complete hierarchy:
    - Checklist
      - Sections (with nested ListItems)
        - ListItems (with progress counts)
    
    All counts (sections_count, items_count, progress_count) are exposed from
    annotated fields provided by the view's get_queryset().
    
    Sections are nested using SectionWithItemsSerializer which includes all items
    with proper prefetching for optimal performance.
    """
    checklist_type = ChecklistTypeListSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    last_updated_by = UserBasicSerializer(read_only=True)
    # Use dedicated section serializer that includes nested items
    sections = SectionWithItemsSerializer(many=True, read_only=True)
    roles = RoleListSerializer(many=True, read_only=True)
    sections_count = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    progress_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Checklist
        fields = [
            'id', 'name', 'description', 'phase', 'notes',
            'checklist_type', 'sections', 'roles',
            'sections_count', 'items_count', 'progress_count',
            'created_at', 'updated_at', 'created_by', 'last_updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'last_updated_by']
    
    def get_sections_count(self, obj):
        """Get sections count from annotated field if available, else query."""
        if hasattr(obj, 'sections_count'):
            return obj.sections_count
        return obj.sections.count()
    
    def get_items_count(self, obj):
        """Get total items count from annotated field if available, else query."""
        if hasattr(obj, 'items_count'):
            return obj.items_count
        # Count all items across all sections
        return ListItem.objects.filter(section__checklist=obj).count()
    
    def get_progress_count(self, obj):
        """Get progress records count from annotated field if available, else query."""
        if hasattr(obj, 'progress_count'):
            return obj.progress_count
        return obj.checklist_progress.count()
    



class ChecklistCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating checklists."""
    checklist_type_id = serializers.IntegerField(required=False, allow_null=True)
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
   
 
    
    class Meta:
        model = Checklist
        fields = [
            'name', 'description', 'phase', 'notes',
            'checklist_type_id', 'role_ids'
        ]
    
    def validate_name(self, value):
        """Validate checklist name."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Checklist name cannot be empty.")
            )
        
        if len(value.strip()) > 255:
            raise serializers.ValidationError(
                _("Checklist name cannot exceed 255 characters.")
            )
        
        return value.strip()
    
    def validate_phase(self, value):
        """Validate phase choice."""
        valid_phases = ['pre-stream', 'on-stream', 'post-stream']
        if value not in valid_phases:
            raise serializers.ValidationError(
                _("Invalid phase. Must be one of: pre-stream, on-stream, post-stream.")
            )
        return value
    
    def validate_description(self, value):
        """Validate description field."""
        if value and len(value.strip()) > 2000:
            raise serializers.ValidationError(
                _("Description cannot exceed 2000 characters.")
            )
        return value or ""
    
    def validate_notes(self, value):
        """Validate notes field."""
        if value and len(value.strip()) > 2000:
            raise serializers.ValidationError(
                _("Notes cannot exceed 2000 characters.")
            )
        return value or ""
    
    def validate(self, data):
        """Validate checklist type existence and uniqueness."""
        # Existence and uniqueness validations moved to service layer.
        return data


# ============================================================
# CHECKLIST PROGRESS SERIALIZERS
# ============================================================

class ChecklistProgressListSerializer(serializers.ModelSerializer):
    """Serializer for listing checklist progress records."""
    user = UserBasicSerializer(read_only=True)
    checklist = serializers.StringRelatedField(read_only=True)
    list_item = serializers.StringRelatedField(source='items', read_only=True)
    
    class Meta:
        model = ChecklistProgress
        fields = [
            'id', 'checklist', 'list_item', 'status',
            'user', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']


class ChecklistProgressDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed checklist progress information."""
    user = UserBasicSerializer(read_only=True)
    checklist = ChecklistListSerializer(read_only=True)
    list_item = ListItemDetailSerializer(source='items', read_only=True)
    
    class Meta:
        model = ChecklistProgress
        fields = [
            'id', 'checklist', 'list_item', 'status',
            'user', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']


class ChecklistProgressCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating checklist progress."""
    checklist_id = serializers.IntegerField(write_only=True)
    list_item_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = ChecklistProgress
        fields = ['checklist_id', 'list_item_id', 'status']
    
    def validate_checklist_id(self, value):
        """Validate checklist exists."""
        # Existence checks moved to service layer.
        if value is not None and value <= 0:
            raise serializers.ValidationError(_("Invalid checklist id."))
        return value
    
    def validate_list_item_id(self, value):
        """Validate list item exists if provided."""
        # Existence checks moved to service layer.
        if value is not None and value <= 0:
            raise serializers.ValidationError(_("Invalid list item id."))
        return value
    
    def validate_status(self, value):
        """Validate status choice."""
        valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
        if value not in valid_statuses:
            raise serializers.ValidationError(
                _("Invalid status. Must be one of: pending, in_progress, completed, blocked.")
            )
        return value
    
    def validate(self, data):
        """Validate list item belongs to checklist if provided."""
        checklist_id = data.get('checklist_id')
        list_item_id = data.get('list_item_id')
        # Cross-model validations (e.g. belongs-to checks) moved to service layer.
        return data


class ChecklistProgressStatsSerializer(serializers.Serializer):
    """Serializer for checklist progress statistics."""
    total_progress_records = serializers.IntegerField(read_only=True)
    total_unique_users = serializers.IntegerField(read_only=True)
    pending = serializers.IntegerField(read_only=True)
    in_progress = serializers.IntegerField(read_only=True)
    completed = serializers.IntegerField(read_only=True)
    blocked = serializers.IntegerField(read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)


class ChecklistStatsSerializer(serializers.Serializer):
    """Serializer for checklist statistics."""
    total_sections = serializers.IntegerField(read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_progress_records = serializers.IntegerField(read_only=True)
    progress_by_status = serializers.DictField(read_only=True)
    roles_count = serializers.IntegerField(read_only=True)


class UserProgressSummarySerializer(serializers.Serializer):
    """Serializer for user progress summary."""
    total_checklists = serializers.IntegerField(read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    pending = serializers.IntegerField(read_only=True)
    in_progress = serializers.IntegerField(read_only=True)
    completed = serializers.IntegerField(read_only=True)
    blocked = serializers.IntegerField(read_only=True)


# ============================================================
# COMPOSITE / BULK CHECKLIST SERIALIZERS
# ============================================================


class BulkListItemSerializer(serializers.ModelSerializer):
    """Nested serializer for list items used in composite checklist payload."""

    id = serializers.IntegerField(required=False)

    class Meta:
        model = ListItem
        fields = ["id", "name", "description"]


class BulkSectionSerializer(serializers.ModelSerializer):
    """Nested serializer for sections used in composite checklist payload."""

    id = serializers.IntegerField(required=False)
    items = BulkListItemSerializer(many=True, required=False)

    class Meta:
        model = Sections
        fields = ["id", "name", "description", "order", "items"]


class ChecklistTypeNestedSerializer(serializers.Serializer):
    """Accept either {'id': <int>} to link existing type or {'name': <str>} to create a new one."""

    id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not data.get("id") and not data.get("name"):
            raise serializers.ValidationError(
                "Either 'id' (to link) or 'name' (to create) must be provided for checklist_type."
            )
        return data


class ChecklistCompositeSerializer(serializers.ModelSerializer):
    """Composite serializer that creates/updates a full checklist with nested sections/items and roles.

    Behavior:
    - `checklist_type`: accepts dict with `id` to link or `name` to create.
    - `roles`: list of role IDs to assign (must exist).
    - `sections`: list of sections; each may include `items` list.
    - `update()` performs a full replace of sections/items (existing sections are removed and recreated).
    """

    checklist_type = ChecklistTypeNestedSerializer(required=False, allow_null=True)
    roles = serializers.ListField(child=serializers.IntegerField(), required=False)
    sections = BulkSectionSerializer(many=True, required=False)

    class Meta:
        model = Checklist
        fields = [
            "id",
            "name",
            "description",
            "phase",
            "notes",
            "checklist_type",
            "roles",
            "sections",
        ]
        read_only_fields = ["id"]

    def validate_phase(self, value):
        valid_phases = ["pre-stream", "on-stream", "post-stream"]
        if value not in valid_phases:
            raise serializers.ValidationError(
                "Invalid phase. Must be one of: pre-stream, on-stream, post-stream."
            )
        return value


    def create(self, validated_data):
        user = self.context.get("user")
        try:
            return ChecklistService.create_full_checklist(user, validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(e.detail if hasattr(e, 'detail') else str(e))

    def update(self, instance, validated_data):
        user = self.context.get("user")
        try:
            return ChecklistService.update_full_checklist(user, instance.id, validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(e.detail if hasattr(e, 'detail') else str(e))

    def to_representation(self, instance):
        # reuse existing detailed serializer for consistent output
        return ChecklistDetailSerializer(instance, context=self.context).data

