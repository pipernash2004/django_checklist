from django.apps import AppConfig


class LmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lms'




# # ...existing code...
# from rest_framework import serializers
# from django.conf import settings
# from .models import ChecklistType, Checklist, ListItem, ChecklistProgress, Sections


# # creatting a base serializer to handle created_by and last_updated_by fields
# class AuditModelSerializer(serializers.ModelSerializer):
#     """
#     Base serializer to expose created_by/last_updated_by as usernames
#     and automatically set created_by/last_updated_by from request.user
#     on create/update.
#     """
#     created_by = serializers.SerializerMethodField(read_only=True)
#     last_updated_by = serializers.SerializerMethodField(read_only=True)

#     def get_created_by(self, obj):
#         return obj.created_by.username if getattr(obj, 'created_by', None) else None

#     def get_last_updated_by(self, obj):
#         return obj.last_updated_by.username if getattr(obj, 'last_updated_by', None) else None

#     def _get_request_user(self):
#         req = self.context.get('request') if hasattr(self, 'context') else None
#         return getattr(req, 'user', None)

#     def create(self, validated_data):
#         user = self._get_request_user()
#         if user and user.is_authenticated:
#             # ensure we set the user instance, not username string
#             validated_data['created_by'] = user
#         return super().create(validated_data)

#     def update(self, instance, validated_data):
#         user = self._get_request_user()
#         if user and user.is_authenticated:
#             validated_data['last_updated_by'] = user
#         return super().update(instance, validated_data)


# class ChecklistTypeSerializer(AuditModelSerializer):
#     class Meta:
#         model = ChecklistType
#         fields = [
#             'id', 'name', 'description',
#             'created_at', 'updated_at',
#             'created_by', 'last_updated_by'
#         ]
#         read_only_fields = ('created_at', 'updated_at', 'created_by', 'last_updated_by')


# class ListItemSerializer(AuditModelSerializer):
#     type_name = serializers.CharField(source="type.name", read_only=True)

#     class Meta:
#         model = ListItem
#         fields = [
#             'id', 'name', 'description',
#             'type', 'type_name',
#             'status',
#             'created_at', 'updated_at',
#             'created_by', 'last_updated_by'
#         ]
#         read_only_fields = ('created_at', 'updated_at', 'created_by', 'last_updated_by')


# class ChecklistItemSerializer(AuditModelSerializer):
#     list_item_detail = ListItemSerializer(source="list_item", read_only=True)

#     class Meta:
#         model = ChecklistItem
#         fields = [
#             'id', 'checklist', 'list_item',
#             'list_item_detail',
#             'created_at', 'updated_at',
#             'created_by', 'last_updated_by'
#         ]
#         read_only_fields = ('created_at', 'updated_at', 'created_by', 'last_updated_by')


# class ChecklistSerializer(AuditModelSerializer):
#     type_name = serializers.CharField(source="type.name", read_only=True)
#     items = ChecklistItemSerializer(
#         source='checklistitem_set', many=True, read_only=True
#     )

#     class Meta:
#         model = Checklist
#         fields = [
#             'id', 'name', 'description',
#             'type', 'type_name',
#             'items',
#             'created_at', 'updated_at',
#             'created_by', 'last_updated_by'
#         ]
#         read_only_fields = ('created_at', 'updated_at', 'created_by', 'last_updated_by')

# # ...existing code...