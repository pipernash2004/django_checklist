from functools import partial
from rest_framework.decorators import action
from .models import *
from .serializers import *
from .management.StandardResultsSetPagination import StandardResultsSetPagination
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import OpenApiResponse
from rest_framework.response import Response
from django.db import transaction
from  django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
import json
import logging
from .models import Course
from .serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    CourseCreateUpdateSerializer,
    CourseFullCreateSerializer,
    LessonSerializer,
    AssessmentSerializer,
    QuestionSerializer,
    ChoiceSerializer,   
    LessonNestedSerializer,
    CourseCreateUpdateSerializer,
    EnrollmentSerializer,
    DashboardSerializer

)
from drf_spectacular.utils import extend_schema
from logs.models import SystemLog
from django.utils import timezone
from datetime import timedelta
# Logger setup
logger = logging.getLogger(__name__)


class DashboardViewSet(viewsets.ViewSet):
    
    serializer_class = DashboardSerializer

    @extend_schema(responses={200: DashboardSerializer})
    @action(detail=False, methods=["get"], url_path="overview", permission_classes=[IsAuthenticated])
    def stats(self, request):
        try:
            total_courses = Course.objects.count()
            total_students = Enrollment.objects.values("user").distinct().count()
            pending_reviews = Review.objects.filter(status="pending").count()
            active_assessments = Assessment.objects.filter(is_published=True).count()

            # ---- Enrollment Trends ----
            today = timezone.now().date()
            start_date = today - timedelta(days=6)

            enrollments = (
                Enrollment.objects
                .filter(created_at__date__gte=start_date)
                .values("created_at__date")
                .annotate(count=Count("id"))
            )

            trend_data = []
            for i in range(7):
                day = start_date + timedelta(days=i)
                count = next(
                    (e["count"] for e in enrollments if e["created_at__date"] == day),
                    0
                )
                trend_data.append({
                    "date": day,
                    "label": day.strftime("%b %d"),
                    "count": count,
                })

            dashboard_data = {
                "stats": {
                    "total_courses": total_courses,
                    "total_students": total_students,
                    "pending_reviews": pending_reviews,
                    "active_assessments": active_assessments,
                },
                "enrollment_trends": {
                    "range": "last_7_days",
                    "growth_percentage": 0.0,
                    "data": trend_data,
                },
                "recent_activities": ActivityLog.objects.order_by("-created_at")[:10]

            }

            serializer = DashboardSerializer(dashboard_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to fetch dashboard data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().select_related('instructor', 'created_by', 'updated_by')
    permission_classes = [IsAuthenticated]
    serializer_class = CourseListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['status', 'level', 'course_type']
    ordering_fields = '__all__'
    ordering = ['-id']



    def get_serializer_class(self):
        if self.action == "full_create":
            return CourseFullCreateSerializer
        elif self.action in [ "update", "partial_update"]:
            return CourseCreateUpdateSerializer
        elif self.action == "list":
            return CourseListSerializer
        elif self.action == "create":
            return CourseCreateUpdateSerializer
        elif self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer

    # ---------------------------
    # Helper: sanitize request data
    # ---------------------------
    def _sanitize_request_data(self, data):
        """Mask sensitive fields and uploaded files in request data"""
        def sanitize_value(value):
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

    # ---------------------------
    # LIST
    # ---------------------------
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.queryset)
            page = self.paginate_queryset(queryset)

            SystemLog.log_action(
                user=request.user,
                action='VIEW',
                table_name='course',
                record_id=None,
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Viewed course list, page {request.query_params.get('page', 1)}"
            )

            serializer = CourseListSerializer(page, many=True) if page is not None else CourseListSerializer(queryset, many=True)

            return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

        except Exception as e:
            logger.error(f"Error listing courses: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to list courses"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------------
    # RETRIEVE
    # ---------------------------
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = CourseDetailSerializer(instance)
            SystemLog.log_action(
                user=request.user,
                action='VIEW',
                table_name='course',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Viewed course '{instance.title}'"
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving course: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to retrieve course"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------------
    # CREATE
    # ---------------------------
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            sanitized_data = self._sanitize_request_data(request.data)
            serializer =   CourseCreateUpdateSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(created_by=request.user, updated_by=request.user)

            ActivityLog.objects.create(
                    user=request.user,
                    action="created",
                    target_type="Course",
                    target_id=instance.pk,
                    target_name=instance.title,
                )
            
            SystemLog.log_action(
                user=request.user,
                action='CREATE',
                table_name='course',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Created course '{instance.title}' with data: {json.dumps(sanitized_data)}"
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating course: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to create course: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    # ---------------------------
    # fULLCREATECOURSE
    # ---------------------------
    
    @extend_schema(
        responses={201: OpenApiResponse(response=CourseFullCreateSerializer)}
    )
    @action(detail=False, methods=['post'], url_path='full-create', permission_classes=[IsAuthenticated])
    @transaction.atomic
    def full_create(self, request, *args, **kwargs):
        try:
         
            serializer = CourseFullCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()

            
            sanitized_data = self._sanitize_request_data(request.data)
            
            ActivityLog.objects.create(
                    user=request.user,
                    action="created",
                    target_type="Course",
                    target_id=instance.pk,
                    target_name=instance.title,
                )
            SystemLog.log_action(
                user=request.user,
                action='CREATE',
                table_name='course',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Created full course '{instance.title}' with data: {json.dumps(sanitized_data)}"
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("Error creating full course", exc_info=True)
            return Response(
                {"detail": f"Failed to create course: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # ---------------------------
    # UPDATE / PARTIAL_UPDATE
    # ---------------------------
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.get('partial', False)
            instance = self.get_object()
            sanitized_data = self._sanitize_request_data(request.data)

            serializer = CourseCreateUpdateSerializer(instance, data=request.data, partial=partial, context={'request': request})
            serializer.is_valid(raise_exception=True)
            updated_instance = serializer.save(updated_by=request.user)

            SystemLog.log_action(
                user=request.user,
                action='UPDATE',
                table_name='course',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Updated course '{instance.title}' with data: {json.dumps(sanitized_data)}"
            )

            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating course: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to update course: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    # ---------------------------
    # DESTROY
    # ---------------------------
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            SystemLog.log_action(
                user=request.user,
                action='DELETE',
                table_name='course',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Deleted course '{instance.title}'"
            )
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting course: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to delete course: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.select_related('course', 'created_by', 'updated_by')
    # serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['course', 'order', 'duration_minutes']
    ordering_fields = '__all__'
    ordering = ['order']

    # ---------------------------
    # Serializer selection per action
    # ---------------------------
    def get_serializer_class(self):
        if self.action == 'list':
            return LessonNestedSerializer
        if self.action in ['retrieve']:
            return LessonSerializer
        # For create/update
        return LessonSerializer

    # ---------------------------
    # Helper: sanitize request data
    # ---------------------------
    def _sanitize_request_data(self, data):
        """Mask sensitive fields and uploaded files in request data"""
        def sanitize_value(value):
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

    # ---------------------------
    # LIST
    # ---------------------------
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.queryset)
            page = self.paginate_queryset(queryset)

            SystemLog.log_action(
                user=request.user,
                action='VIEW',
                table_name='lesson',
                record_id=None,
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Viewed lesson list, page {request.query_params.get('page', 1)}"
            )

            serializer = self.get_serializer(page, many=True) if page else self.get_serializer(queryset, many=True)
            return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

        except Exception as e:
            logger.error(f"Error listing lessons: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to list lessons"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------------
    # RETRIEVE
    # ---------------------------
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)

            SystemLog.log_action(
                user=request.user,
                action='VIEW',
                table_name='lesson',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Viewed lesson '{instance.title}'"
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving lesson: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to retrieve lesson"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------------
    # CREATE
    # ---------------------------
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            sanitized_data = self._sanitize_request_data(request.data)
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(created_by=request.user, updated_by=request.user)

            ActivityLog.objects.create(
                    user=request.user,
                    action="uploaded",
                    target_type="Lesson",
                    target_id=instance.pk,
                    target_name=instance.title,
                )

            SystemLog.log_action(
                user=request.user,
                action='CREATE',
                table_name='lesson',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Created lesson '{instance.title}' with data: {json.dumps(sanitized_data)}"
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating lesson: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to create lesson: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # ---------------------------
    # UPDATE / PARTIAL_UPDATE
    # ---------------------------
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.get('partial', False)
            instance = self.get_object()
            sanitized_data = self._sanitize_request_data(request.data)

            serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
            serializer.is_valid(raise_exception=True)
            updated_instance = serializer.save(updated_by=request.user)

            SystemLog.log_action(
                user=request.user,
                action='UPDATE',
                table_name='lesson',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Updated lesson '{instance.title}' with data: {json.dumps(sanitized_data)}"
            )

            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating lesson: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to update lesson: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    # ---------------------------
    # DESTROY
    # ---------------------------
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            SystemLog.log_action(
                user=request.user,
                action='DELETE',
                table_name='lesson',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Deleted lesson '{instance.title}'"
            )
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting lesson: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to delete lesson: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.select_related('course', 'created_by', 'updated_by')
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = []  # add filters if needed
    search_fields = ['title', 'description']
    ordering_fields = '__all__'
    ordering = ['-id']

    # ---------------------------
    # Helper: sanitize request data
    # ---------------------------
    def _sanitize_request_data(self, data):
        """Mask sensitive fields and uploaded files in request data"""
        def sanitize_value(value):
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

    # ---------------------------
    # LIST
    # ---------------------------
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.queryset)
            page = self.paginate_queryset(queryset)

            SystemLog.log_action(
                user=request.user,
                action='VIEW',
                table_name='assessment',
                record_id=None,
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Viewed assessment list, page {request.query_params.get('page', 1)}"
            )

            serializer = AssessmentSerializer(page, many=True) if page is not None else AssessmentSerializer(queryset, many=True)
            return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

        except Exception as e:
            logger.error(f"Error listing assessments: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to list assessments"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------------
    # RETRIEVE
    # ---------------------------
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = AssessmentSerializer(instance)
            SystemLog.log_action(
                user=request.user,
                action='VIEW',
                table_name='assessment',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Viewed assessment '{instance.title}'"
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving assessment: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to retrieve assessment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------------
    # CREATE
    # ---------------------------
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            sanitized_data = self._sanitize_request_data(request.data)
            serializer = AssessmentSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(created_by=request.user, updated_by=request.user)

            ActivityLog.objects.create(
                    user=request.user,
                    action="uploaded",
                    target_type="Assessment",
                    target_id=instance.pk,
                    target_name=instance.title,
                )

            SystemLog.log_action(
                user=request.user,
                action='CREATE',
                table_name='assessment',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Created assessment '{instance.title}' with data: {json.dumps(sanitized_data)}"
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating assessment: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to create assessment: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # ---------------------------
    # UPDATE / PARTIAL_UPDATE
    # ---------------------------
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.get('partial', False)
            instance = self.get_object()
            sanitized_data = self._sanitize_request_data(request.data)

            serializer = AssessmentSerializer(instance, data=request.data, partial=partial, context={'request': request})
            serializer.is_valid(raise_exception=True)
            updated_instance = serializer.save(updated_by=request.user)

            SystemLog.log_action(
                user=request.user,
                action='UPDATE',
                table_name='assessment',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Updated assessment '{instance.title}' with data: {json.dumps(sanitized_data)}"
            )

            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating assessment: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to update assessment: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    # ---------------------------
    # DESTROY
    # ---------------------------
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            SystemLog.log_action(
                user=request.user,
                action='DELETE',
                table_name='assessment',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Deleted assessment '{instance.title}'"
            )
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting assessment: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to delete assessment: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

# ---------------------------
# Question ViewSet
# ---------------------------
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().select_related('assessment', 'created_by', 'updated_by')
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]


      # ---------------------------
    # Helper: sanitize request data
    # ---------------------------
    def _sanitize_request_data(self, data):
        """Mask sensitive fields and uploaded files in request data"""
        def sanitize_value(value):
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


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            sanitized_data = self._sanitize_request_data(request.data)
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(created_by=request.user, updated_by=request.user)


            ActivityLog.objects.create(
                    user=request.user,
                    action="uploaded",
                    target_type="Question",
                    target_id=instance.pk,
                    target_name=instance.text,
                )

            SystemLog.log_action(
                user=request.user,
                action='CREATE',
                table_name='question',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Created question '{instance.text[:50]}' with data: {json.dumps(sanitized_data)}"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating question: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to create question: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.get('partial', False)
            instance = self.get_object()
            sanitized_data = sanitize_request_data(request.data)

            serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user)

            SystemLog.log_action(
                user=request.user,
                action='UPDATE',
                table_name='question',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Updated question '{instance.text[:50]}' with data: {json.dumps(sanitized_data)}"
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating question: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to update question: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            SystemLog.log_action(
                user=request.user,
                action='DELETE',
                table_name='question',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Deleted question '{instance.text[:50]}'"
            )
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting question: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to delete question: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# Choice ViewSet
# ---------------------------
class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.all().select_related('question', 'created_by', 'updated_by')
    serializer_class = ChoiceSerializer
    permission_classes = [IsAuthenticated]

      # ---------------------------
    # Helper: sanitize request data
    # ---------------------------
    def _sanitize_request_data(self, data):
        """Mask sensitive fields and uploaded files in request data"""
        def sanitize_value(value):
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


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            sanitized_data = self._sanitize_request_data(request.data)
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(created_by=request.user, updated_by=request.user)

            ActivityLog.objects.create(
                    user=request.user,
                    action="uploaded",
                target_type="Choice",
                    target_id=instance.pk,
                    target_name=instance.text,
                )

            SystemLog.log_action(
                user=request.user,
                action='CREATE',
                table_name='choice',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Created choice '{instance.text[:50]}' with data: {json.dumps(sanitized_data)}"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating choice: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to create choice: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.get('partial', False)
            instance = self.get_object()
            sanitized_data = sanitize_request_data(request.data)

            serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=request.user)

            SystemLog.log_action(
                user=request.user,
                action='UPDATE',
                table_name='choice',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Updated choice '{instance.text[:50]}' with data: {json.dumps(sanitized_data)}"
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating choice: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to update choice: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            SystemLog.log_action(
                user=request.user,
                action='DELETE',
                table_name='choice',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Deleted choice '{instance.text[:50]}'"
            )
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting choice: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to delete choice: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all().select_related('user', 'course')
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['course', 'user']

    # ---------------------------
    # Helper: sanitize request data
    # ---------------------------
    def _sanitize_request_data(self, data):
        """Mask sensitive fields and uploaded files in request data"""
        def sanitize_value(value):
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

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            sanitized_data = self._sanitize_request_data(request.data)
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)
            ActivityLog.objects.create(
                        user=request.user,
                        action="enrolled",
                        target_type="Enrollment",
                        target_id=instance.pk,
                        target_name=instance.course.title,
                    )

            SystemLog.log_action(
                user=request.user,
                action='CREATE',
                table_name='enrollment',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Enrolled user {request.user} to course {instance.course.title} with data: {json.dumps(sanitized_data)}"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating enrollment: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to enroll: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.get('partial', False)
            instance = self.get_object()
            sanitized_data = sanitize_request_data(request.data)

            serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()

            SystemLog.log_action(
                user=request.user,
                action='UPDATE',
                table_name='enrollment',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Updated enrollment for user {instance.user} in course {instance.course.title} with data: {json.dumps(sanitized_data)}"
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating enrollment: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to update enrollment: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            SystemLog.log_action(
                user=request.user,
                action='DELETE',
                table_name='enrollment',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Deleted enrollment of user {instance.user} from course {instance.course.title}"
            )
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting enrollment: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to delete enrollment: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
# ---------------------------
# ReviewSet
# ---------------------------


class ReviewViewSet(viewsets.ModelViewSet): 
    queryset = Review.objects.all().select_related('user', 'course')
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['course', 'user']

      # ---------------------------
    # Helper: sanitize request data
    # ---------------------------
    def _sanitize_request_data(self, data):
        """Mask sensitive fields and uploaded files in request data"""
        def sanitize_value(value):
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
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            sanitized_data = self._sanitize_request_data(request.data)
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(user=request.user)

            ActivityLog.objects.create(
                    user=request.user,
                    action="submitted_review",
                    target_type="Review",
                    target_id=instance.pk,
                    target_name=instance.comment[:50],
                )
                
            SystemLog.log_action(
                user=request.user,
                action='CREATE',
                table_name='review',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Created review by user {request.user} for course {instance.course.title} with data: {json.dumps(sanitized_data)}"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating review: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to create review: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    @transaction.atomic     
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.get('partial', False)
            instance = self.get_object()
            sanitized_data = sanitize_request_data(request.data)

            serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()

            SystemLog.log_action(
                user=request.user,
                action='UPDATE',
                table_name='review',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Updated review by user {instance.user} for course {instance.course.title} with data: {json.dumps(sanitized_data)}"
            )
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating review: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to update review: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    @transaction.atomic 
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            SystemLog.log_action(
                user=request.user,
                action='DELETE',
                table_name='review',
                record_id=str(instance.pk),
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_info=f"Deleted review by user {instance.user} for course {instance.course.title}"
            )
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting review: {str(e)}", exc_info=True)
            return Response({"detail": f"Failed to delete review: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
