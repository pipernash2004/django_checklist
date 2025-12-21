
# ============================================================
# LEARNING MANAGEMENT SYSTEM - API VIEWS
# ============================================================
# This module provides REST API endpoints for managing:
# - Courses (creation, updates, nested lessons & assessments)
# - Lessons (course content modules)
# - Assessments (quizzes with questions and choices)
# ============================================================

# Standard library imports
import json
import logging

# Django imports
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

# Third-party imports
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import Lesson, Course, Assessment
from .serializers import (
    LessonListSerializer, LessonDetailSerializer, LessonCreateUpdateSerializer,
    AssessmentListSerializer, AssessmentDetailSerializer, AssessmentCreateUpdateSerializer,
     CourseListSerializer, CourseDetailSerializer, CourseCreateUpdateSerializer,
    CourseFullCreateSerializer, CourseFullDetailSerializer,
    CourseFullUpdateSerializer, CourseFullPatchSerializer
)
from .management.StandardResultsSetPagination import StandardResultsSetPagination

# Logger setup
logger = logging.getLogger(__name__)


# ============================================================
# LESSON VIEWSET
# ============================================================

class LessonViewSet(viewsets.ModelViewSet):

    
    queryset = Lesson.objects.all().select_related(
        'course', 'created_by', 'updated_by'
    ).order_by('-created_at')
    
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'course__title']
    filterset_fields = ['course', 'created_at']
    ordering_fields = ['order', 'duration_minutes', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
 
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
      
        try:
            instance = serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user
            )
            logger.info(f"Lesson created: ID {instance.pk} by user {self.request.user}")
        except Exception as e:
            logger.error(f"Error creating lesson: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
       
        try:
            instance = serializer.save(updated_by=self.request.user)
            logger.info(f"Lesson updated: ID {instance.pk} by user {self.request.user}")
        except Exception as e:
            logger.error(f"Error updating lesson: {str(e)}", exc_info=True)
            raise

    def perform_destroy(self, instance):
        
        try:
            lesson_id = instance.pk
            lesson_title = instance.title
            instance.delete()
            logger.info(f"Lesson deleted: ID {lesson_id} ({lesson_title}) by user {self.request.user}")
        except Exception as e:
            logger.error(f"Error deleting lesson: {str(e)}", exc_info=True)
            raise

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            logger.debug(f"Lesson creation response: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.warning(f"Validation error creating lesson: {str(e)}")
            return Response(
                {"detail": f"Validation error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating lesson: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to create lesson"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.debug(f"Listed {len(page)} lessons on page {request.query_params.get('page', 1)}")
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            logger.debug(f"Listed {queryset.count()} lessons without pagination")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing lessons: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to list lessons"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================
# ASSESSMENT VIEWSET
# ============================================================

class AssessmentViewSet(viewsets.ModelViewSet):
    
    queryset = Assessment.objects.all().select_related(
        'course', 'created_by', 'updated_by'
    ).prefetch_related('questions').order_by('-created_at')
    
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'course__title']
    filterset_fields = ['course', 'is_published', 'created_at']
    ordering_fields = ['title', 'pass_mark', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AssessmentListSerializer
        elif self.action == 'retrieve':
            return AssessmentDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AssessmentCreateUpdateSerializer
        return AssessmentDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """
        Create assessment and auto-set created_by and updated_by.
        
        Args:
            serializer: Validated assessment serializer
        """
        try:
            instance = serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user
            )
            logger.info(f"Assessment created: ID {instance.pk} by user {self.request.user}")
        except Exception as e:
            logger.error(f"Error creating assessment: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
        try:
            instance = serializer.save(updated_by=self.request.user)
            logger.info(f"Assessment updated: ID {instance.pk} by user {self.request.user}")
        except Exception as e:
            logger.error(f"Error updating assessment: {str(e)}", exc_info=True)
            raise

    def perform_destroy(self, instance):
        try:
            assessment_id = instance.pk
            assessment_title = instance.title
            instance.delete()
            logger.info(f"Assessment deleted: ID {assessment_id} ({assessment_title}) by user {self.request.user}")
        except Exception as e:
            logger.error(f"Error deleting assessment: {str(e)}", exc_info=True)
            raise

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            logger.debug(f"Assessment creation response: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.warning(f"Validation error creating assessment: {str(e)}")
            return Response(
                {"detail": f"Validation error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating assessment: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to create assessment"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.debug(f"Listed {len(page)} assessments on page {request.query_params.get('page', 1)}")
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            logger.debug(f"Listed {queryset.count()} assessments without pagination")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing assessments: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to list assessments"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================
# COURSE VIEWSET
# ============================================================

class CourseViewSet(viewsets.ModelViewSet):
    
    queryset = Course.objects.all().select_related(
        'instructor', 'created_by', 'updated_by'
    ).prefetch_related(
        'lessons', 'assessments', 'assessments__questions', 'assessments__questions__choices'
    ).order_by('-created_at')
    
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'content_type', 'instructor__first_name', 'instructor__last_name']
    filterset_fields = ['content_type', 'status', 'level']
    ordering_fields = ['title', 'duration_weeks', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Check if user has access permission
        if not self._has_access_permission(user):
            logger.warning(f"User {user} lacks permission to access courses")
            return Course.objects.none()
        
        try:
            user_company = getattr(user, 'company', None)
            if user_company:
                logger.debug(f"Filtering courses for user {user} with company {user_company}")
                queryset = queryset.filter(created_by__company=user_company)
            else:
                logger.debug(f"User {user} has no company, allowing access to all courses")
        except AttributeError as e:
            logger.error(f"User model {user} does not have expected attributes: {str(e)}")
            return Course.objects.none()
        
        return queryset

    def _has_access_permission(self, user):
        return user.is_superuser or hasattr(user, 'company')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CourseFullCreateSerializer
        elif self.action == 'update':
            return CourseFullUpdateSerializer
        elif self.action == 'partial_update':
            return CourseFullPatchSerializer
        elif self.action == 'list':
            return CourseListSerializer
        elif self.action == 'retrieve':
            return CourseFullDetailSerializer
        return CourseDetailSerializer

    def perform_create(self, serializer):
        try:
            instance = serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user
            )
            logger.info(f"Course created: ID {instance.pk} ({instance.title}) by user {self.request.user}")
            return instance
        except Exception as e:
            logger.error(f"Error creating course: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
  
        try:
            instance = serializer.save(updated_by=self.request.user)
            logger.info(f"Course updated: ID {instance.pk} ({instance.title}) by user {self.request.user}")
        except Exception as e:
            logger.error(f"Error updating course: {str(e)}", exc_info=True)
            raise

    def perform_destroy(self, instance):
        
        try:
            course_id = instance.pk
            course_title = instance.title
            instance.delete()
            logger.info(f"Course deleted: ID {course_id} ({course_title}) by user {self.request.user}")
        except Exception as e:
            logger.error(f"Error deleting course: {str(e)}", exc_info=True)
            raise

    def create(self, request, *args, **kwargs):
        try:
            logger.debug(f"Creating course with data: {self._sanitize_request_data(request.data)}")
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = self.perform_create(serializer)
            logger.debug(f"Course creation response: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.warning(f"Validation error creating course: {str(e)}")
            return Response(
                {"detail": f"Validation error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating course: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to create course"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.debug(f"Listed {len(page)} courses on page {request.query_params.get('page', 1)}")
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            logger.debug(f"Listed {queryset.count()} courses without pagination")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing courses: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to list courses"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            old_data = CourseDetailSerializer(instance).data
            logger.debug(f"Updating course ID {instance.pk} - Old data: {old_data}")
            
            response = super().update(request, *args, **kwargs)
            logger.debug(f"Course ID {instance.pk} updated successfully")
            return response
        except Exception as e:
            logger.error(f"Error updating course: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to update course"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, *args, **kwargs):
   
        try:
            instance = self.get_object()
            logger.debug(f"Partially updating course ID {instance.pk}")
            
            response = super().partial_update(request, *args, **kwargs)
            logger.debug(f"Course ID {instance.pk} partially updated successfully")
            return response
        except Exception as e:
            logger.error(f"Error partially updating course: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to update course"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            logger.debug(f"Deleting course ID {instance.pk} ({instance.title})")
            
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"Course deleted: {instance.pk} ({instance.title})")
            return response
        except Exception as e:
            logger.error(f"Error deleting course: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to delete course"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def _sanitize_request_data(data):
        def sanitize_value(value):
            """Recursively sanitize nested structures."""
            if isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [sanitize_value(v) for v in value]
            elif isinstance(value, UploadedFile):
                return f"File: {value.name} (size: {value.size} bytes)"
            return value

        sanitized = data.copy() if isinstance(data, dict) else dict(data)
        sensitive_fields = getattr(settings, 'SENSITIVE_FIELDS', ['password', 'token'])
        
        for key in list(sanitized.keys()):
            if key in sensitive_fields:
                sanitized[key] = '****'
            else:
                sanitized[key] = sanitize_value(sanitized[key])
        
        return sanitized

