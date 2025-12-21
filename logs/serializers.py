from rest_framework import serializers
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from authentication.models import CustomUser  # Assuming CustomUser is your user model

class LogEntrySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    action = serializers.SerializerMethodField()
    content_type_name = serializers.CharField(source='content_type.name', read_only=True)
    
    class Meta:
        model = LogEntry
        fields = [
            'id',
            'action_time',
            'user',
            'user_email',
            'content_type',
            'content_type_name',
            'object_id',
            'object_repr',
            'action',
            'change_message',
        ]
        read_only_fields = fields

    def get_action(self, obj):
        """Convert action_flag to human-readable action name."""
        action_map = {
            ADDITION: 'Addition',
            CHANGE: 'Change',
            DELETION: 'Deletion',
        }
        return action_map.get(obj.action_flag, 'Unknown')