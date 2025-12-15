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
from drf_spectacular.utils import extend_schema, OpenApiResponse

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
            serializer.save(
                instructor=self.request.user,
                created_by=self.request.user,
                updated_by=self.request.user
            )
            logger.info(f"Course created by user {self.request.user.id}: {serializer.instance.title}")
        except Exception as e:
            logger.error(f"Error creating course: {str(e)}")
            raise

    def perform_update(self, serializer):
        """Set updated_by to current user."""
        try:
            serializer.save(updated_by=self.request.user)
            logger.info(f"Course updated by user {self.request.user.id}: {serializer.instance.title}")
        except Exception as e:
            logger.error(f"Error updating course: {str(e)}")
            raise

    def perform_destroy(self, instance):
        """Only admin can delete."""
        if not self.request.user.is_staff:
            logger.warning(f"Non-admin user {self.request.user.id} attempted to delete course {instance.id}")
            raise ValidationError("Only admin can delete courses.")
        try:
            instance.delete()
            logger.info(f"Course deleted by user {self.request.user.id}: {instance.title}")
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
            
            try:
                crew_member = request.user.crew_member
            except AttributeError:
                logger.warning(f"User {request.user.id} attempted enrollment without crew profile")
                return Response(
                    {'error': 'User must have a crew member profile.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if already enrolled
            enrollment, created = Enrollment.objects.get_or_create(
                crew_member=crew_member,
                course=course,
                defaults={
                    'created_by': request.user,
                    'updated_by': request.user
                }
            )

            if not created:
                logger.info(f"User {request.user.id} already enrolled in course {course.id}")
                return Response(
                    {'message': 'Already enrolled in this course.'},
                    status=status.HTTP_200_OK
                )

            logger.info(f"User {request.user.id} enrolled in course {course.id}")
            serializer = EnrollmentListSerializer(enrollment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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
            lessons = course.lessons.all().order_by('order')
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
            
            enrollments = course.enrollments.all()
            total_enrollments = enrollments.count()
            completed_enrollments = enrollments.filter(completed_at__isnull=False).count()
            
            completion_rate = (
                (completed_enrollments / total_enrollments * 100)
                if total_enrollments > 0 else 0
            )

            reviews = course.reviews.all()
            average_rating = (
                reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            )

            total_lessons = course.lessons.count()
            total_duration = course.duration

            stats_data = {
                'total_enrollments': total_enrollments,
                'completed_enrollments': completed_enrollments,
                'completion_rate': round(completion_rate, 2),
                'average_rating': round(average_rating, 1),
                'review_count': reviews.count(),
                'total_lessons': total_lessons,
                'total_duration': total_duration
            }
            
            logger.debug(f"Retrieved stats for course {course.id}")
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
            reviews = course.reviews.all().order_by('-created_at')
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
            serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user
            )
            logger.info(f"Lesson created by user {self.request.user.id}: {serializer.instance.title}")
        except Exception as e:
            logger.error(f"Error creating lesson: {str(e)}")
            raise

    def perform_update(self, serializer):
        """Set updated_by to current user."""
        try:
            serializer.save(updated_by=self.request.user)
            logger.info(f"Lesson updated by user {self.request.user.id}: {serializer.instance.title}")
        except Exception as e:
            logger.error(f"Error updating lesson: {str(e)}")
            raise

    def perform_destroy(self, instance):
        """Only admin can delete."""
        if not self.request.user.is_staff:
            logger.warning(f"Non-admin user {self.request.user.id} attempted to delete lesson {instance.id}")
            raise ValidationError("Only admin can delete lessons.")
        try:
            instance.delete()
            logger.info(f"Lesson deleted by user {self.request.user.id}: {instance.title}")
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
            
            try:
                crew_member = request.user.crew_member
            except AttributeError:
                logger.warning(f"User {request.user.id} attempted lesson completion without crew profile")
                return Response(
                    {'error': 'User must have a crew member profile.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if enrolled in course
            enrollment = Enrollment.objects.filter(
                crew_member=crew_member,
                course=lesson.course
            ).first()

            if not enrollment:
                logger.warning(f"User {request.user.id} not enrolled in course {lesson.course.id}")
                return Response(
                    {'error': 'Must be enrolled in course to complete lessons.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create or get progress record
            progress, created = LessonProgress.objects.get_or_create(
                crew_member=crew_member,
                lesson=lesson
            )

            # Update enrollment progress
            total_lessons = lesson.course.lessons.count()
            completed_lessons = LessonProgress.objects.filter(
                crew_member=crew_member,
                lesson__course=lesson.course
            ).count()

            if total_lessons > 0:
                progress_percent = round((completed_lessons / total_lessons) * 100)
            else:
                progress_percent = 0

            enrollment.overall_progress = progress_percent
            
            if progress_percent == 100:
                enrollment.completed_at = timezone.now()

            enrollment.save()

            logger.info(f"User {request.user.id} completed lesson {lesson.id}, course progress: {progress_percent}%")

            return Response({
                'status': 'completed',
                'lesson_progress': LessonProgressSerializer(progress).data,
                'course_progress': {
                    'overall_progress': progress_percent,
                    'lessons_completed': completed_lessons,
                    'total_lessons': total_lessons
                }
            }, status=status.HTTP_200_OK)

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
            
            try:
                crew_member = request.user.crew_member
            except AttributeError:
                logger.warning(f"User {request.user.id} attempted to check status without crew profile")
                return Response(
                    {'error': 'User must have a crew member profile.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                progress = LessonProgress.objects.get(
                    crew_member=crew_member,
                    lesson=lesson
                )
                logger.debug(f"User {request.user.id} has completed lesson {lesson.id}")
                return Response({
                    'completed': True,
                    'completed_at': progress.created_at
                })
            except LessonProgress.DoesNotExist:
                logger.debug(f"User {request.user.id} has not completed lesson {lesson.id}")
                return Response({
                    'completed': False,
                    'completed_at': None
                })

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
            crew_member = self.request.user.crew_member
            logger.debug(f"Filtering enrollments for user {self.request.user.id}")
            return Enrollment.objects.filter(
                crew_member=crew_member
            ).select_related('course').prefetch_related('course__lessons')
        except AttributeError:
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
            enrollments = self.get_queryset().filter(overall_progress__lt=100)
            serializer = self.get_serializer(enrollments, many=True)
            logger.debug(f"Retrieved {len(enrollments)} active courses for user {request.user.id}")
            return Response(serializer.data)
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
            enrollments = self.get_queryset().filter(overall_progress=100)
            serializer = self.get_serializer(enrollments, many=True)
            logger.debug(f"Retrieved {len(enrollments)} completed courses for user {request.user.id}")
            return Response(serializer.data)
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
            serializer.save(crew_member=self.request.user.crew_member)
            logger.info(f"User {self.request.user.id} created review for course {serializer.instance.course.id}")
        except Exception as e:
            logger.error(f"Error creating review: {str(e)}")
            raise

    def perform_update(self, serializer):
        """Only allow updating own review."""
        try:
            review = self.get_object()
            if review.crew_member.user != self.request.user:
                logger.warning(f"User {self.request.user.id} attempted to update review by {review.crew_member.user.id}")
                raise ValidationError("You can only update your own review.")
            serializer.save()
            logger.info(f"User {self.request.user.id} updated review {review.id}")
        except Exception as e:
            logger.error(f"Error updating review: {str(e)}")
            raise

    def perform_destroy(self, instance):
        """Only allow deleting own review."""
        try:
            if instance.crew_member.user != self.request.user:
                logger.warning(f"User {self.request.user.id} attempted to delete review by {instance.crew_member.user.id}")
                raise ValidationError("You can only delete your own review.")
            instance.delete()
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
            crew_member = request.user.crew_member
            achievements = Achievement.objects.filter(
                crew_member=crew_member
            ).order_by('-created_at')
            serializer = self.get_serializer(achievements, many=True)
            logger.debug(f"Retrieved {len(achievements)} achievements for user {request.user.id}")
            return Response(serializer.data)
        except AttributeError:
            logger.warning(f"User {request.user.id} attempted achievement check without crew profile")
            return Response(
                {'error': 'User must have a crew member profile.'},
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
            crew_member = request.user.crew_member
        except AttributeError:
            logger.warning(f"User {request.user.id} attempted dashboard access without crew profile")
            return Response(
                {'error': 'User must have a crew member profile.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get enrollments
            enrollments = Enrollment.objects.filter(crew_member=crew_member)
            in_progress = enrollments.filter(overall_progress__lt=100).count()
            completed = enrollments.filter(overall_progress=100).count()

            # Get achievements
            achievements = Achievement.objects.filter(crew_member=crew_member)
            recent_achievements = achievements.order_by('-created_at')[:3]

            # Calculate learning stats
            total_lessons_completed = LessonProgress.objects.filter(
                crew_member=crew_member
            ).count()

            total_learning_minutes = Enrollment.objects.filter(
                crew_member=crew_member,
                completed_at__isnull=False
            ).values_list('course__duration', flat=True).sum() or 0

            dashboard_data = {
                'in_progress_count': in_progress,
                'completed_count': completed,
                'total_lessons_completed': total_lessons_completed,
                'total_learning_hours': round(total_learning_minutes / 60, 1),
                'recent_achievements': AchievementSerializer(
                    recent_achievements,
                    many=True
                ).data
            }

            logger.debug(f"Retrieved dashboard overview for user {request.user.id}")
            return Response(dashboard_data)

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
            crew_member = request.user.crew_member
        except AttributeError:
            logger.warning(f"User {request.user.id} attempted progress check without crew profile")
            return Response(
                {'error': 'User must have a crew member profile.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            enrollments = Enrollment.objects.filter(
                crew_member=crew_member
            ).select_related('course').prefetch_related('course__lessons')

            progress_data = []
            for enrollment in enrollments:
                total_lessons = enrollment.course.lessons.count()
                completed_lessons = LessonProgress.objects.filter(
                    crew_member=crew_member,
                    lesson__course=enrollment.course
                ).count()

                progress_data.append({
                    'course_id': enrollment.course.id,
                    'course_title': enrollment.course.title,
                    'overall_progress': enrollment.overall_progress,
                    'lessons_completed': completed_lessons,
                    'total_lessons': total_lessons,
                    'started_at': enrollment.started_at,
                    'completed_at': enrollment.completed_at
                })

            logger.debug(f"Retrieved progress details for user {request.user.id}")
            return Response(progress_data)

        except Exception as e:
            logger.error(f"Error getting progress details: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to retrieve progress details"},
                status=status.HTTP_400_BAD_REQUEST
            )
