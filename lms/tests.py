# from django.test import TestCase

# # Create your tests here.


# # from rest_framework import viewsets, status
# # from rest_framework.decorators import action
# # from rest_framework.response import Response
# # from rest_framework.permissions import IsAuthenticated
# # from django.core.exceptions import ValidationError


# # from .models import ChecklistType, Checklist, ListItem, ChecklistItem
# # from .serializers import (
# #     ChecklistTypeSerializer,
# #     ChecklistSerializer,
# #     ListItemSerializer,
# #     ChecklistItemSerializer,
# # )


# # class ChecklistTypeViewSet(viewsets.ModelViewSet):
# #     """
# #     ViewSet for managing Checklist Types with custom behavior.
    
# #     Provides standard CRUD operations plus custom actions:
# #     - list_with_stats: Get all types with item counts
# #     - by_name: Filter by name
# #     """
# #     queryset = ChecklistType.objects.all()
# #     serializer_class = ChecklistTypeSerializer
# #     permission_classes = [IsAuthenticated]

# #     def perform_create(self, serializer):
# #         """Override to automatically set created_by to current user"""
# #         serializer.save(created_by=self.request.user)

# #     def perform_update(self, serializer):
# #         """Override to automatically set last_updated_by to current user"""
# #         serializer.save(last_updated_by=self.request.user)

# #     @action(detail=False, methods=['get'])
# #     def list_with_stats(self, request):
# #         """
# #         Get all checklist types with item statistics.
# #         Returns count of checklists and items for each type.
# #         """
# #         types = self.get_queryset()
# #         data = []
        
# #         for type_obj in types:
# #             checklist_count = Checklist.objects.filter(type=type_obj).count()
# #             item_count = ListItem.objects.filter(type=type_obj).count()
            
# #             type_data = ChecklistTypeSerializer(type_obj).data
# #             type_data['checklist_count'] = checklist_count
# #             type_data['item_count'] = item_count
# #             data.append(type_data)
        
# #         return Response(data)

# #     @action(detail=False, methods=['get'])
# #     def by_name(self, request):
# #         """
# #         Filter checklist types by name (case-insensitive).
# #         Query parameter: name=<search_term>
# #         """
# #         name = request.query_params.get('name', '')
        
# #         if not name:
# #             return Response(
# #                 {'error': 'name parameter is required'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         queryset = self.get_queryset().filter(name__icontains=name)
# #         serializer = self.get_serializer(queryset, many=True)
# #         return Response(serializer.data)


# # class ListItemViewSet(viewsets.ModelViewSet):
# #     """
# #     ViewSet for managing List Items with custom behavior.
    
# #     Provides standard CRUD operations plus custom actions:
# #     - by_status: Filter items by status
# #     - by_type: Filter items by checklist type
# #     - bulk_status_update: Update status for multiple items
# #     """
# #     queryset = ListItem.objects.all()
# #     serializer_class = ListItemSerializer
# #     permission_classes = [IsAuthenticated]

# #     def perform_create(self, serializer):
# #         """Override to automatically set created_by to current user"""
# #         serializer.save(created_by=self.request.user)

# #     def perform_update(self, serializer):
# #         """Override to automatically set last_updated_by to current user"""
# #         serializer.save(last_updated_by=self.request.user)

# #     @action(detail=False, methods=['get'])
# #     def by_status(self, request):
# #         """
# #         Filter list items by status.
# #         Query parameter: status=<pending|in_progress|completed|blocked>
# #         """
# #         status_filter = request.query_params.get('status', '')
        
# #         if not status_filter:
# #             return Response(
# #                 {'error': 'status parameter is required (pending, in_progress, completed, or blocked)'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         queryset = self.get_queryset().filter(status=status_filter)
# #         serializer = self.get_serializer(queryset, many=True)
# #         return Response(serializer.data)

# #     @action(detail=False, methods=['get'])
# #     def by_type(self, request):
# #         """
# #         Filter list items by checklist type ID.
# #         Query parameter: type_id=<id>
# #         """
# #         type_id = request.query_params.get('type_id', '')
        
# #         if not type_id:
# #             return Response(
# #                 {'error': 'type_id parameter is required'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         queryset = self.get_queryset().filter(type_id=type_id)
# #         serializer = self.get_serializer(queryset, many=True)
# #         return Response(serializer.data)

# #     @action(detail=False, methods=['post'])
# #     def bulk_status_update(self, request):
# #         """
# #         Update status for multiple items at once.
# #         Expected payload: {'item_ids': [1, 2, 3], 'status': 'completed'}
# #         """
# #         item_ids = request.data.get('item_ids', [])
# #         new_status = request.data.get('status', '')
        
# #         if not item_ids or not new_status:
# #             return Response(
# #                 {'error': 'item_ids and status are required'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         # Validate status
# #         valid_statuses = [choice[0] for choice in ListItem.STATUS_CHOICES]
# #         if new_status not in valid_statuses:
# #             return Response(
# #                 {'error': f'status must be one of: {", ".join(valid_statuses)}'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         updated_count = ListItem.objects.filter(id__in=item_ids).update(
# #             status=new_status,
# #             last_updated_by=request.user
# #         )
        
# #         return Response({
# #             'message': f'Updated {updated_count} items',
# #             'updated_count': updated_count
# #         })


# # class ChecklistViewSet(viewsets.ModelViewSet):
# #     """
# #     ViewSet for managing Checklists with custom behavior.
    
# #     Provides standard CRUD operations plus custom actions:
# #     - add_item: Add an item to a checklist
# #     - remove_item: Remove an item from a checklist
# #     - by_type: Filter checklists by type
# #     - get_progress: Get completion progress of a checklist
# #     """
# #     queryset = Checklist.objects.all()
# #     serializer_class = ChecklistSerializer
# #     permission_classes = [IsAuthenticated]

# #     def perform_create(self, serializer):
# #         """Override to automatically set created_by to current user"""
# #         serializer.save(created_by=self.request.user)

# #     def perform_update(self, serializer):
# #         """Override to automatically set last_updated_by to current user"""
# #         serializer.save(last_updated_by=self.request.user)

# #     @action(detail=True, methods=['post'])
# #     def add_item(self, request, pk=None):
# #         """
# #         Add a list item to this checklist.
# #         Expected payload: {'item_id': <id>}
# #         """
# #         checklist = self.get_object()
# #         item_id = request.data.get('item_id')
        
# #         if not item_id:
# #             return Response(
# #                 {'error': 'item_id is required'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         try:
# #             item = ListItem.objects.get(id=item_id)
# #         except ListItem.DoesNotExist:
# #             return Response(
# #                 {'error': 'ListItem not found'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )
        
# #         try:
# #             checklist.add_item(item)
# #             return Response({
# #                 'message': f'Item "{item.name}" added to checklist',
# #                 'status': 'success'
# #             }, status=status.HTTP_201_CREATED)
# #         except ValidationError as e:
# #             return Response(
# #                 {'error': str(e)},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )

# #     @action(detail=True, methods=['post'])
# #     def remove_item(self, request, pk=None):
# #         """
# #         Remove a list item from this checklist.
# #         Expected payload: {'item_id': <id>}
# #         """
# #         checklist = self.get_object()
# #         item_id = request.data.get('item_id')
        
# #         if not item_id:
# #             return Response(
# #                 {'error': 'item_id is required'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         try:
# #             ChecklistItem.objects.get(checklist=checklist, list_item_id=item_id).delete()
# #             return Response({
# #                 'message': 'Item removed from checklist',
# #                 'status': 'success'
# #             })
# #         except ChecklistItem.DoesNotExist:
# #             return Response(
# #                 {'error': 'Item not found in this checklist'},
# #                 status=status.HTTP_404_NOT_FOUND
# #             )

# #     @action(detail=False, methods=['get'])
# #     def by_type(self, request):
# #         """
# #         Filter checklists by type ID.
# #         Query parameter: type_id=<id>
# #         """
# #         type_id = request.query_params.get('type_id', '')
        
# #         if not type_id:
# #             return Response(
# #                 {'error': 'type_id parameter is required'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         queryset = self.get_queryset().filter(type_id=type_id)
# #         serializer = self.get_serializer(queryset, many=True)
# #         return Response(serializer.data)

# #     @action(detail=True, methods=['get'])
# #     def get_progress(self, request, pk=None):
# #         """
# #         Get the completion progress of a checklist.
# #         Returns: total items, completed items, and percentage.
# #         """
# #         checklist = self.get_object()
        
# #         checklist_items = ChecklistItem.objects.filter(checklist=checklist)
# #         total_items = checklist_items.count()
        
# #         if total_items == 0:
# #             return Response({
# #                 'checklist_id': checklist.id,
# #                 'checklist_name': checklist.name,
# #                 'total_items': 0,
# #                 'completed_items': 0,
# #                 'progress_percentage': 0
# #             })
        
# #         completed_items = checklist_items.filter(
# #             list_item__status='completed'
# #         ).count()
        
# #         progress_percentage = (completed_items / total_items) * 100
        
# #         return Response({
# #             'checklist_id': checklist.id,
# #             'checklist_name': checklist.name,
# #             'total_items': total_items,
# #             'completed_items': completed_items,
# #             'progress_percentage': round(progress_percentage, 2)
# #         })


# # class ChecklistItemViewSet(viewsets.ModelViewSet):
# #     """
# #     ViewSet for managing Checklist Items (junction between Checklist and ListItem).
    
# #     Provides standard CRUD operations plus custom actions:
# #     - by_checklist: Get all items in a specific checklist
# #     - by_status: Filter checklist items by list item status
# #     """
# #     queryset = ChecklistItem.objects.all()
# #     serializer_class = ChecklistItemSerializer
# #     permission_classes = [IsAuthenticated]

# #     def perform_create(self, serializer):
# #         """Override to automatically set created_by to current user"""
# #         serializer.save(created_by=self.request.user)

# #     def perform_update(self, serializer):
# #         """Override to automatically set last_updated_by to current user"""
# #         serializer.save(last_updated_by=self.request.user)

# #     @action(detail=False, methods=['get'])
# #     def by_checklist(self, request):
# #         """
# #         Get all items belonging to a specific checklist.
# #         Query parameter: checklist_id=<id>
# #         """
# #         checklist_id = request.query_params.get('checklist_id', '')
        
# #         if not checklist_id:
# #             return Response(
# #                 {'error': 'checklist_id parameter is required'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         queryset = self.get_queryset().filter(checklist_id=checklist_id)
# #         serializer = self.get_serializer(queryset, many=True)
# #         return Response(serializer.data)

# #     @action(detail=False, methods=['get'])
# #     def by_status(self, request):
# #         """
# #         Filter checklist items by their list item's status.
# #         Query parameter: status=<pending|in_progress|completed|blocked>
# #         """
# #         status_filter = request.query_params.get('status', '')
        
# #         if not status_filter:
# #             return Response(
# #                 {'error': 'status parameter is required'},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )
        
# #         queryset = self.get_queryset().filter(list_item__status=status_filter)
# #         serializer = self.get_serializer(queryset, many=True)
# #         return Response(serializer.data)



# from rest_framework import serializers
# from django.db import transaction
# from .models import (
#     Course, Lesson, Assessment, Choice, Question,
#     Enrollment, LessonProgress, Review,
#     AssessmentAttempt, Answer
# )

# # ============================================================
# # BASE SERIALIZERS
# # ============================================================

# class AuditModelSerializer(serializers.ModelSerializer):
#     """Base serializer for audit fields"""

#     class Meta:
#         abstract = True
#         read_only_fields = (
#             'id', 'created_at', 'updated_at',
#             'created_by', 'updated_by'
#         )


# # ============================================================
# # SIMPLE DETAIL SERIALIZERS
# # ============================================================

# class LessonDetailSerializer(AuditModelSerializer):
#     class Meta(AuditModelSerializer.Meta):
#         model = Lesson
#         fields = '__all__'


# class ChoiceDetailSerializer(AuditModelSerializer):
#     class Meta(AuditModelSerializer.Meta):
#         model = Choice
#         fields = '__all__'


# class QuestionDetailSerializer(AuditModelSerializer):
#     choices = ChoiceDetailSerializer(many=True, read_only=True)

#     class Meta(AuditModelSerializer.Meta):
#         model = Question
#         fields = '__all__'


# class AssessmentDetailSerializer(AuditModelSerializer):
#     questions = QuestionDetailSerializer(many=True, read_only=True)

#     class Meta(AuditModelSerializer.Meta):
#         model = Assessment
#         fields = '__all__'


# class CourseDetailSerializer(AuditModelSerializer):
#     lessons = LessonDetailSerializer(many=True, read_only=True)
#     assessments = AssessmentDetailSerializer(many=True, read_only=True)

#     class Meta(AuditModelSerializer.Meta):
#         model = Course
#         fields = '__all__'


# # ============================================================
# # ENROLLMENT / REVIEW / PROGRESS
# # ============================================================

# class EnrollmentDetailSerializer(serializers.ModelSerializer):
#     course = CourseDetailSerializer(read_only=True)
#     user_name = serializers.CharField(source='user.get_full_name', read_only=True)

#     class Meta:
#         model = Enrollment
#         fields = '__all__'
#         read_only_fields = ('id', 'enrolled_at')


# class LessonProgressDetailSerializer(serializers.ModelSerializer):
#     lesson = LessonDetailSerializer(read_only=True)
#     user_name = serializers.CharField(source='user.get_full_name', read_only=True)

#     class Meta:
#         model = LessonProgress
#         fields = '__all__'
#         read_only_fields = ('id', 'created_at', 'updated_at')


# class ReviewDetailSerializer(AuditModelSerializer):
#     course = CourseDetailSerializer(read_only=True)
#     user_name = serializers.CharField(source='user.get_full_name', read_only=True)

#     class Meta(AuditModelSerializer.Meta):
#         model = Review
#         fields = '__all__'


# # ============================================================
# # NESTED CREATE SERIALIZERS
# # ============================================================

# class NestedChoiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Choice
#         fields = ('text', 'is_correct')


# class NestedQuestionSerializer(serializers.ModelSerializer):
#     choices = NestedChoiceSerializer(many=True, required=False)

#     class Meta:
#         model = Question
#         fields = ('text', 'order', 'question_type', 'choices')


# class NestedAssessmentSerializer(serializers.ModelSerializer):
#     questions = NestedQuestionSerializer(many=True, required=False)

#     class Meta:
#         model = Assessment
#         fields = ('title', 'description', 'pass_mark', 'is_published', 'questions')


# class NestedLessonSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Lesson
#         fields = ('title', 'description', 'order', 'duration_minutes', 'content_url')


# # ============================================================
# # COURSE FULL CREATE / UPDATE
# # ============================================================

# class CourseFullBaseSerializer(serializers.ModelSerializer):
#     lessons = NestedLessonSerializer(many=True, required=False)
#     assessments = NestedAssessmentSerializer(many=True, required=False)

#     class Meta:
#         model = Course
#         exclude = ('created_at', 'updated_at', 'created_by', 'updated_by')

#     def _save_nested(self, instance, lessons, assessments, user):
#         if lessons is not None:
#             instance.lessons.all().delete()
#             Lesson.objects.bulk_create([
#                 Lesson(course = instance, **l, created_by=user, updated_by=user)
#                 for l in lessons
#             ])

#         if assessments is not None:
#             instance.assessments.all().delete()
#             for assessment in assessments:
#                 questions = assessment.pop('questions', [])
#                 assessment = Assessment.objects.create(
#                     course=instance, created_by=user, updated_by=user, **assessment
#                 )
#                 for q in questions:
#                     choices = q.pop('choices', [])
#                     question = Question.objects.create(assessment=assessment, **q)
#                     Choice.objects.bulk_create([
#                         Choice(question=question, **c) for c in choices
#                     ])


# class CourseFullCreateSerializer(CourseFullBaseSerializer):

#     @transaction.atomic
#     def create(self, validated_data):
#         lessons = validated_data.pop('lessons', [])
#         assessments = validated_data.pop('assessments', [])
#         user = self.context['request'].user

#         course = Course.objects.create(
#             **validated_data, created_by=user, updated_by=user
#         )
#         self._save_nested(course, lessons, assessments, user)
#         return course


# class CourseFullUpdateSerializer(CourseFullBaseSerializer):

#     @transaction.atomic
#     def update(self, instance, validated_data):
#         lessons = validated_data.pop('lessons', None)
#         assessments = validated_data.pop('assessments', None)
#         user = self.context['request'].user

#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.updated_by = user
#         instance.save()

#         self._save_nested(instance, lessons, assessments, user)
#         return instance
