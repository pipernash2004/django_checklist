from rest_framework import serializers
from .model import (
    Checklist,
    Section,
    ListItem,
    ListItemProgress,
    CrewMemberChecklist,
    ChecklistType,
)
from crew.models import CrewMember



class CrewMemberChecklistSerializer(serializers.ModelSerializer):
    crew_member_name = serializers.CharField(source="crew_member.full_name", read_only=True)
    checklist_detail = ChecklistSerializer(source="checklist", read_only=True)

    class Meta:
        model = CrewMemberChecklist
        fields = [
            'id',
            'crew_member', 'crew_member_name',
            'checklist', 'checklist_detail',
            'created_at', 'updated_at',
            'created_by', 'last_updated_by'
        ]
        read_only_fields = ('created_at', 'updated_at')
