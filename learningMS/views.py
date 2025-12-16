# Standard library imports
import json
import logging

# Django imports
from django.db import transaction
from django.db.models import Count, Q, Avg
from django.utils import timezone

# Third-party imports
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

# Local app imports
from .models import Course, Lesson, Enrollment, LessonProgress, Review, Achievement
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseCreateUpdateSerializer,
    LessonBasicSerializer, LessonDetailSerializer, LessonCreateUpdateSerializer,
    EnrollmentListSerializer, EnrollmentDetailSerializer,
    LessonProgressSerializer,
    ReviewListSerializer, ReviewDetailSerializer, ReviewCreateSerializer,
    AchievementSerializer, CourseProgressSerializer, DashboardOverviewSerializer
)
from .services import (
    CourseService, LessonService, EnrollmentService, ReviewService,
    AchievementService, DashboardService, ValidationService
)
from drf_spectacular.utils import extend_schema

logger = logging.getLogger(__name__)

# ============================================================
# COURSE VIEWSET
# ============================================================

class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course management.
    
    Actions:
    - list: Get all courses with filtering
    - retrieve: Get course details
    - create: Create new course (staff only)
    - update/partial_update: Update course (instructor/admin)
    - destroy: Delete course (admin only)
    
    Custom actions:
    - enroll: Enroll current user in course
    - lessons: Get course lessons
    - stats: Get course statistics
    - reviews: Get course reviews
    """
    queryset = Course.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description', 'category']
    filterset_fields = ['level', 'category', 'course_type']
    ordering_fields = ['title', 'created_at', 'duration']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CourseListSerializer
        elif self.action == 'retrieve':
            return CourseDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        return CourseDetailSerializer

    def get_queryset(self):
        """Optimize queryset based on action."""
        queryset = super().get_queryset()
        
        if self.action == 'list':
            queryset = queryset.select_related('instructor')
        elif self.action == 'retrieve':
            queryset = queryset.prefetch_related('lessons').select_related('instructor')
        
        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]

    def _check_instructor_permission(self, course):
        """Check if user is instructor/admin of course."""
        return (
            self.request.user == course.instructor or
            self.request.user.is_staff
        )

    def perform_create(self, serializer):
        """Auto-set instructor to current user."""
        try:
            validated_data = serializer.validated_data
            validated_data['instructor'] = self.request.user
            validated_data['created_by'] = self.request.user
            validated_data['updated_by'] = self.request.user
            CourseService.create_course(self.request.user, validated_data)
        except Exception as e:
            logger.error(f"Error creating course: {str(e)}")
            raise

    def perform_update(self, serializer):
        """Set updated_by to current user."""
        try:
            course = self.get_object()
            validated_data = serializer.validated_data
            CourseService.update_course(course, self.request.user, validated_data)
        except Exception as e:
            logger.error(f"Error updating course: {str(e)}")
            raise

    def perform_destroy(self, instance):
        """Only admin can delete."""
        try:
            CourseService.delete_course(instance, self.request.user)
        except Exception as e:
            logger.error(f"Error deleting course: {str(e)}")
            raise

    def list(self, request, *args, **kwargs):
        """List courses with filtering and pagination."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            logger.debug(f"User {request.user.id} viewing course list, page {request.query_params.get('page', 1)}")

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.debug(f"Listing {len(page)} courses")
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error listing courses: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to list courses"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll current user in course."""
        try:
            course = self.get_object()
            enrollment, created = EnrollmentService.enroll_user_in_course(request.user, course)

            if not created:
                logger.info(f"User {request.user.id} already enrolled in course {course.id}")
                return Response(
                    {'message': 'Already enrolled in this course.'},
                    status=status.HTTP_200_OK
                )

            logger.info(f"User {request.user.id} enrolled in course {course.id}")
            serializer = EnrollmentListSerializer(enrollment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(
                {'error': str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error enrolling user: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to enroll in course"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        """Get all lessons for this course."""
        try:
            course = self.get_object()
            lessons = CourseService.get_course_lessons(course)
            serializer = LessonBasicSerializer(lessons, many=True)
            logger.debug(f"Retrieved {len(lessons)} lessons for course {course.id}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting course lessons: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to retrieve lessons"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get course statistics."""
        try:
            course = self.get_object()
            stats_data = CourseService.get_course_stats(course)
            return Response(stats_data)
        except Exception as e:
            logger.error(f"Error getting course stats: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to retrieve statistics"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for this course."""
        try:
            course = self.get_object()
            reviews = CourseService.get_course_reviews(course)
            serializer = ReviewListSerializer(reviews, many=True)
            logger.debug(f"Retrieved {len(reviews)} reviews for course {course.id}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting course reviews: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to retrieve reviews"},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================
# LESSON VIEWSET
# ============================================================

class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lesson management.
    
    Actions:
    - list: Get lessons (filtered by course)
    - retrieve: Get lesson details
    - create: Create new lesson (staff only)
    - update/partial_update: Update lesson (instructor/admin)
    - destroy: Delete lesson (admin only)
    
    Custom actions:
    - complete: Mark lesson as complete
    - status: Get user's completion status
    """
    queryset = Lesson.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['course', 'lesson_type']
    ordering_fields = ['order', 'duration', 'created_at']
    ordering = ['order']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return LessonDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return LessonCreateUpdateSerializer
        return LessonBasicSerializer

    def get_queryset(self):
        """Filter by course if provided."""
        queryset = super().get_queryset()
        course_id = self.request.query_params.get('course_id')
        
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.select_related('course').order_by('order')

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]

    def _check_instructor_permission(self, lesson):
        """Check if user is instructor/admin of lesson's course."""
        return (
            self.request.user == lesson.course.instructor or
            self.request.user.is_staff
        )

    def perform_create(self, serializer):
        """Auto-set timestamps."""
        try:
            validated_data = serializer.validated_data
            validated_data['created_by'] = self.request.user
            validated_data['updated_by'] = self.request.user
            LessonService.create_lesson(self.request.user, validated_data)
        except Exception as e:
            logger.error(f"Error creating lesson: {str(e)}")
            raise

    def perform_update(self, serializer):
        """Set updated_by to current user."""
        try:
            lesson = self.get_object()
            validated_data = serializer.validated_data
            LessonService.update_lesson(lesson, self.request.user, validated_data)
        except Exception as e:
            logger.error(f"Error updating lesson: {str(e)}")
            raise

    def perform_destroy(self, instance):
        """Only admin can delete."""
        try:
            LessonService.delete_lesson(instance, self.request.user)
        except Exception as e:
            logger.error(f"Error deleting lesson: {str(e)}")
            raise

    def list(self, request, *args, **kwargs):
        """List lessons with filtering."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            logger.debug(f"User {request.user.id if request.user.is_authenticated else 'anonymous'} viewing lesson list")

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error listing lessons: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to list lessons"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def complete(self, request, pk=None):
        """Mark lesson as complete."""
        try:
            lesson = self.get_object()
            crew_member = ValidationService.check_crew_member_exists(request.user)

            result = LessonService.complete_lesson(lesson, crew_member)
            
            return Response({
                'status': 'completed',
                'lesson_progress': LessonProgressSerializer(result['progress']).data,
                'course_progress': result['stats']
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response(
                {'error': str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error completing lesson: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to complete lesson"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def status(self, request, pk=None):
        """Get user's completion status for this lesson."""
        try:
            lesson = self.get_object()
            crew_member = ValidationService.check_crew_member_exists(request.user)
            
            status_data = LessonService.get_lesson_completion_status(lesson, crew_member)
            logger.debug(f"User {request.user.id} checked status for lesson {lesson.id}")
            return Response(status_data)

        except ValidationError as e:
            return Response(
                {'error': str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting lesson status: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to retrieve lesson status"},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================
# ENROLLMENT VIEWSET
# ============================================================

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing enrollments.
    
    Actions:
    - list: Get user's enrollments
    - retrieve: Get specific enrollment
    
    Custom actions:
    - my-courses: Get user's active courses
    - completed: Get user's completed courses
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['course']
    ordering_fields = ['started_at', 'overall_progress']
    ordering = ['-started_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return EnrollmentDetailSerializer
        return EnrollmentListSerializer

    def get_queryset(self):
        """Return only current user's enrollments."""
        try:
            crew_member = ValidationService.check_crew_member_exists(self.request.user)
            logger.debug(f"Filtering enrollments for user {self.request.user.id}")
            return EnrollmentService.get_user_enrollments(crew_member)
        except ValidationError:
            logger.warning(f"User {self.request.user.id} has no crew profile")
            return Enrollment.objects.none()

    def list(self, request, *args, **kwargs):
        """List user's enrollments."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.debug(f"Listing {len(page)} enrollments for user {request.user.id}")
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error listing enrollments: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to list enrollments"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def my_courses(self, request):
        """Get user's active (in-progress) courses."""
        try:
            crew_member = ValidationService.check_crew_member_exists(request.user)
            enrollments = EnrollmentService.get_active_enrollments(crew_member)
            serializer = self.get_serializer(enrollments, many=True)
            logger.debug(f"Retrieved {len(enrollments)} active courses for user {request.user.id}")
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {'error': str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting active courses: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to retrieve active courses"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get user's completed courses."""
        try:
            crew_member = ValidationService.check_crew_member_exists(request.user)
            enrollments = EnrollmentService.get_completed_enrollments(crew_member)
            serializer = self.get_serializer(enrollments, many=True)
            logger.debug(f"Retrieved {len(enrollments)} completed courses for user {request.user.id}")
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {'error': str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting completed courses: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to retrieve completed courses"},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================
# REVIEW VIEWSET
# ============================================================

class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    
    Actions:
    - list: Get reviews (filtered by course)
    - retrieve: Get review details
    - create: Create new review
    - update/partial_update: Update own review
    - destroy: Delete own review
    """
    queryset = Review.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['comment', 'crew_member__name']
    filterset_fields = ['course', 'rating']
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ReviewCreateSerializer
        elif self.action == 'retrieve':
            return ReviewDetailSerializer
        return ReviewListSerializer

    def get_queryset(self):
        """Filter by course if provided."""
        queryset = super().get_queryset()
        course_id = self.request.query_params.get('course_id')
        
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.select_related('crew_member', 'course').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """List reviews with filtering."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            logger.debug(f"User {request.user.id if request.user.is_authenticated else 'anonymous'} viewing review list")

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error listing reviews: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to list reviews"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        """Create review with current user as reviewer."""
        try:
            course = serializer.validated_data.get('course')
            rating = serializer.validated_data.get('rating')
            comment = serializer.validated_data.get('comment')
            review = ReviewService.create_review(self.request.user, course, rating, comment)
            logger.info(f"User {self.request.user.id} created review for course {course.id}")
        except Exception as e:
            logger.error(f"Error creating review: {str(e)}")
            raise

    def perform_update(self, serializer):
        """Only allow updating own review."""
        try:
            review = self.get_object()
            validated_data = serializer.validated_data
            ReviewService.update_review(review, self.request.user, validated_data)
            logger.info(f"User {self.request.user.id} updated review {review.id}")
        except Exception as e:
            logger.error(f"Error updating review: {str(e)}")
            raise

    def perform_destroy(self, instance):
        """Only allow deleting own review."""
        try:
            ReviewService.delete_review(instance, self.request.user)
            logger.info(f"User {self.request.user.id} deleted review {instance.id}")
        except Exception as e:
            logger.error(f"Error deleting review: {str(e)}")
            raise


# ============================================================
# ACHIEVEMENT VIEWSET
# ============================================================

class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing achievements.
    
    Actions:
    - list: Get achievements (filtered by user)
    - retrieve: Get achievement details
    
    Custom actions:
    - my: Get current user's achievements
    """
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['crew_member']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter by user if provided."""
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        
        if user_id:
            queryset = queryset.filter(crew_member__user_id=user_id)
            logger.debug(f"Filtering achievements for user {user_id}")
        
        return queryset.select_related('crew_member').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """List achievements."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.debug(f"Listing {len(page)} achievements")
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error listing achievements: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to list achievements"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my(self, request):
        """Get current user's achievements."""
        try:
            crew_member = ValidationService.check_crew_member_exists(request.user)
            achievements = AchievementService.get_user_achievements(crew_member)
            serializer = self.get_serializer(achievements, many=True)
            logger.debug(f"Retrieved {len(achievements)} achievements for user {request.user.id}")
            return Response(serializer.data)
        except ValidationError as e:
            logger.warning(f"User {request.user.id} attempted achievement check without crew profile")
            return Response(
                {'error': str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting user achievements: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to retrieve achievements"},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================
# DASHBOARD VIEWSET
# ============================================================

class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard endpoints.
    
    Custom actions:
    - overview: Quick stats overview
    - progress: Detailed progress tracking
    """
    permission_classes = [permissions.IsAuthenticated]
    @extend_schema(
        responses=DashboardOverviewSerializer
    )

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get user's learning dashboard overview."""
        try:
            crew_member = ValidationService.check_crew_member_exists(request.user)
            dashboard_data = DashboardService.get_dashboard_overview(crew_member)
            return Response(dashboard_data)
        except ValidationError as e:
            logger.warning(f"User {request.user.id} attempted dashboard access without crew profile")
            return Response(
                {'error': str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to retrieve dashboard overview"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses=CourseProgressSerializer(many=True)
    )
    @action(detail=False, methods=['get'])
    def progress(self, request):
        """Get detailed progress tracking for user."""
        try:
            crew_member = ValidationService.check_crew_member_exists(request.user)
            progress_data = DashboardService.get_detailed_progress(crew_member)
            logger.debug(f"Retrieved progress details for user {request.user.id}")
            return Response(progress_data)
        except ValidationError as e:
            logger.warning(f"User {request.user.id} attempted progress check without crew profile")
            return Response(
                {'error': str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting progress details: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to retrieve progress details"},
                status=status.HTTP_400_BAD_REQUEST
            )
