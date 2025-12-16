"""
Business logic services for learningMS app.
Extracted from views and serializers to follow clean architecture principles.
"""

import logging
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models.functions import TruncDate
from itertools import chain
from operator import attrgetter

from .models import Course, Lesson, Enrollment, LessonProgress, Review, Achievement

User = get_user_model()

logger = logging.getLogger(__name__)


# ============================================================
# COURSE SERVICES
# ============================================================

class CourseService:
    """Service for course-related business logic."""

    @staticmethod
    def calculate_average_rating(course):
        """Calculate average rating from reviews."""
        reviews = course.reviews.all()
        if not reviews.exists():
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @staticmethod
    def get_review_count(course):
        """Count total reviews for course."""
        return course.reviews.count()

    @staticmethod
    def get_enrollment_count(course):
        """Count total enrollments for course."""
        return course.enrollments.count()

    @staticmethod
    def get_course_stats(course):
        """Get comprehensive course statistics."""
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
        return stats_data

    @staticmethod
    def get_course_lessons(course):
        """Get all lessons for a course ordered by lesson order."""
        return course.lessons.all().order_by('order')

    @staticmethod
    def get_course_reviews(course):
        """Get all reviews for a course ordered by creation date."""
        return course.reviews.all().order_by('-created_at')

    @staticmethod
    def create_course(user, validated_data):
        """Create a new course with current user as instructor."""
        validated_data['instructor'] = user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
        course = Course.objects.create(**validated_data)
        logger.info(f"Course created by user {user.id}: {course.title}")
        return course

    @staticmethod
    def update_course(course, user, validated_data):
        """Update course with current user as updater."""
        validated_data['updated_by'] = user
        for attr, value in validated_data.items():
            setattr(course, attr, value)
        course.save()
        logger.info(f"Course updated by user {user.id}: {course.title}")
        return course

    @staticmethod
    def delete_course(course, user):
        """Delete course (only admin can delete)."""
        if not user.is_staff:
            logger.warning(f"Non-admin user {user.id} attempted to delete course {course.id}")
            raise ValidationError("Only admin can delete courses.")
        try:
            course.delete()
            logger.info(f"Course deleted by user {user.id}: {course.title}")
        except Exception as e:
            logger.error(f"Error deleting course: {str(e)}")
            raise


# ============================================================
# LESSON SERVICES
# ============================================================

class LessonService:
    """Service for lesson-related business logic."""

    @staticmethod
    def validate_duration(value):
        """Validate duration is positive."""
        if value <= 0:
            raise ValidationError("Duration must be greater than 0.")
        return value

    @staticmethod
    def validate_order(value):
        """Validate order is positive."""
        if value <= 0:
            raise ValidationError("Order must be greater than 0.")
        return value

    @staticmethod
    def get_lesson_completion_status(lesson, crew_member):
        """Get user's completion status for a lesson."""
        try:
            progress = LessonProgress.objects.get(
                crew_member=crew_member,
                lesson=lesson
            )
            return {
                'completed': True,
                'completed_at': progress.created_at
            }
        except LessonProgress.DoesNotExist:
            return {
                'completed': False,
                'completed_at': None
            }

    @staticmethod
    def create_lesson(user, validated_data):
        """Create a new lesson with current user as creator."""
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
        lesson = Lesson.objects.create(**validated_data)
        logger.info(f"Lesson created by user {user.id}: {lesson.title}")
        return lesson

    @staticmethod
    def update_lesson(lesson, user, validated_data):
        """Update lesson with current user as updater."""
        validated_data['updated_by'] = user
        for attr, value in validated_data.items():
            setattr(lesson, attr, value)
        lesson.save()
        logger.info(f"Lesson updated by user {user.id}: {lesson.title}")
        return lesson

    @staticmethod
    def delete_lesson(lesson, user):
        """Delete lesson (only admin can delete)."""
        if not user.is_staff:
            logger.warning(f"Non-admin user {user.id} attempted to delete lesson {lesson.id}")
            raise ValidationError("Only admin can delete lessons.")
        try:
            lesson.delete()
            logger.info(f"Lesson deleted by user {user.id}: {lesson.title}")
        except Exception as e:
            logger.error(f"Error deleting lesson: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def complete_lesson(lesson, crew_member):
        """Mark lesson as complete and update enrollment progress."""
        # Check if enrolled in course
        enrollment = Enrollment.objects.filter(
            crew_member=crew_member,
            course=lesson.course
        ).first()

        if not enrollment:
            logger.warning(f"User {crew_member} not enrolled in course {lesson.course.id}")
            raise ValidationError("Must be enrolled in course to complete lessons.")

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

        logger.info(f"User {crew_member} completed lesson {lesson.id}, course progress: {progress_percent}%")

        return {
            'progress': progress,
            'enrollment': enrollment,
            'stats': {
                'overall_progress': progress_percent,
                'lessons_completed': completed_lessons,
                'total_lessons': total_lessons
            }
        }


# ============================================================
# ENROLLMENT SERVICES
# ============================================================

class EnrollmentService:
    """Service for enrollment-related business logic."""

    @staticmethod
    @transaction.atomic
    def enroll_user_in_course(user, course):
        """Enroll user in a course."""
        try:
            crew_member = user.crew_member
        except AttributeError:
            logger.warning(f"User {user.id} attempted enrollment without crew profile")
            raise ValidationError("User must have a crew member profile.")

        # Check if already enrolled
        enrollment, created = Enrollment.objects.get_or_create(
            crew_member=crew_member,
            course=course,
            defaults={
                'created_by': user,
                'updated_by': user
            }
        )

        if not created:
            logger.info(f"User {user.id} already enrolled in course {course.id}")
            return enrollment, False

        logger.info(f"User {user.id} enrolled in course {course.id}")
        return enrollment, True

    @staticmethod
    def get_user_enrollments(crew_member):
        """Get all enrollments for a crew member."""
        return Enrollment.objects.filter(
            crew_member=crew_member
        ).select_related('course').prefetch_related('course__lessons')

    @staticmethod
    def get_active_enrollments(crew_member):
        """Get in-progress enrollments for a crew member."""
        return EnrollmentService.get_user_enrollments(crew_member).filter(
            overall_progress__lt=100
        )

    @staticmethod
    def get_completed_enrollments(crew_member):
        """Get completed enrollments for a crew member."""
        return EnrollmentService.get_user_enrollments(crew_member).filter(
            overall_progress=100
        )


# ============================================================
# REVIEW SERVICES
# ============================================================

class ReviewService:
    """Service for review-related business logic."""

    @staticmethod
    def validate_rating(value):
        """Validate rating is between 1 and 5."""
        if not 1 <= value <= 5:
            raise ValidationError("Rating must be between 1 and 5.")
        return value

    @staticmethod
    def validate_comment(value):
        """Validate comment is not empty."""
        if not value or not value.strip():
            raise ValidationError("Comment cannot be empty.")
        return value

    @staticmethod
    def check_existing_review(crew_member, course):
        """Check if user already has a review for this course."""
        return Review.objects.filter(
            crew_member=crew_member,
            course=course
        ).exists()

    @staticmethod
    def create_review(user, course, rating, comment):
        """Create a new review."""
        try:
            crew_member = user.crew_member
        except AttributeError:
            logger.warning(f"User {user.id} attempted review without crew profile")
            raise ValidationError("User must have a crew member profile.")

        # Check if already reviewed
        if ReviewService.check_existing_review(crew_member, course):
            raise ValidationError("You have already reviewed this course.")

        review = Review.objects.create(
            crew_member=crew_member,
            course=course,
            rating=rating,
            comment=comment
        )
        logger.info(f"User {user.id} created review for course {course.id}")
        return review

    @staticmethod
    def update_review(review, user, validated_data):
        """Update review (only reviewer can update)."""
        if review.crew_member.user != user:
            logger.warning(f"User {user.id} attempted to update review by {review.crew_member.user.id}")
            raise ValidationError("You can only update your own review.")

        for attr, value in validated_data.items():
            setattr(review, attr, value)
        review.save()
        logger.info(f"User {user.id} updated review {review.id}")
        return review

    @staticmethod
    def delete_review(review, user):
        """Delete review (only reviewer can delete)."""
        if review.crew_member.user != user:
            logger.warning(f"User {user.id} attempted to delete review by {review.crew_member.user.id}")
            raise ValidationError("You can only delete your own review.")
        review.delete()
        logger.info(f"User {user.id} deleted review {review.id}")

    @staticmethod
    def truncate_comment(comment, max_length=40):
        """Truncate comment for list view."""
        if comment and len(comment) > max_length:
            return comment[:max_length] + '...'
        return comment


# ============================================================
# ACHIEVEMENT SERVICES
# ============================================================

class AchievementService:
    """Service for achievement-related business logic."""

    @staticmethod
    def derive_category_from_title(title):
        """Derive category from achievement title."""
        title_lower = title.lower()
        if 'course' in title_lower:
            return 'course'
        elif 'lesson' in title_lower:
            return 'lesson'
        elif 'learning' in title_lower or 'streak' in title_lower:
            return 'engagement'
        else:
            return 'other'

    @staticmethod
    def get_user_achievements(crew_member):
        """Get all achievements for a user ordered by creation date."""
        return Achievement.objects.filter(
            crew_member=crew_member
        ).order_by('-created_at')

    @staticmethod
    def get_recent_achievements(crew_member, limit=3):
        """Get recent achievements for a user."""
        return AchievementService.get_user_achievements(crew_member)[:limit]


# ============================================================
# DASHBOARD SERVICES
# ============================================================

class DashboardService:
    """Service for dashboard-related business logic."""

    @staticmethod
    def get_dashboard_overview(crew_member):
        """Get user's learning dashboard overview."""
        # Get enrollments
        enrollments = Enrollment.objects.filter(crew_member=crew_member)
        in_progress = enrollments.filter(overall_progress__lt=100).count()
        completed = enrollments.filter(overall_progress=100).count()

        # Get achievements
        recent_achievements = AchievementService.get_recent_achievements(crew_member, limit=3)

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
            'recent_achievements': recent_achievements
        }

        logger.debug(f"Retrieved dashboard overview for user {crew_member.user.id}")
        return dashboard_data

    @staticmethod
    def get_detailed_progress(crew_member):
        """Get detailed progress tracking for user."""
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

        logger.debug(f"Retrieved progress details for user {crew_member.user.id}")
        return progress_data


# ============================================================
# VALIDATION SERVICES
# ============================================================

class ValidationService:
    """Service for cross-cutting validation logic."""

    @staticmethod
    def validate_course_duration(value):
        """Validate course duration is positive."""
        if value <= 0:
            raise ValidationError("Duration must be greater than 0.")
        return value

    @staticmethod
    def validate_skills(value):
        """Validate skills is a list with reasonable length."""
        if not isinstance(value, list):
            raise ValidationError("Skills must be a list.")
        if len(value) > 50:
            raise ValidationError("Maximum 50 skills allowed.")
        return value

    @staticmethod
    def validate_requirements(value):
        """Validate requirements is a list with reasonable length."""
        if not isinstance(value, list):
            raise ValidationError("Requirements must be a list.")
        if len(value) > 50:
            raise ValidationError("Maximum 50 requirements allowed.")
        return value

    @staticmethod
    def check_crew_member_exists(user):
        """Check if user has a crew member profile."""
        try:
            return user.crew_member
        except AttributeError:
            logger.warning(f"User {user.id} has no crew member profile")
            raise ValidationError("User must have a crew member profile.")

    @staticmethod
    def check_instructor_permission(user, course):
        """Check if user is instructor/admin of course."""
        return user == course.instructor or user.is_staff

    @staticmethod
    def check_lesson_instructor_permission(user, lesson):
        """Check if user is instructor/admin of lesson's course."""
        return user == lesson.course.instructor or user.is_staff



# ============================================================
# ADMIN DASHBOARD SERVICES
# ============================================================

class DashboardStatsService:

    @staticmethod
    def total_students():
        """
        Students are users who have at least one enrollment.
        """
        return User.objects.filter(
            course_enrollments__isnull=False
        ).distinct().count()

    @staticmethod
    def total_courses():
        return Course.objects.count()

    @staticmethod
    def pending_reviews():
        """
        Reviews awaiting moderation.
        """
        return Review.objects.filter(status='pending').count()

    @classmethod
    def get_stats(cls):
        """
        Aggregated stats endpoint
        """
        return {
            "total_students": cls.total_students(),
            "total_courses": cls.total_courses(),
            "pending_reviews": cls.pending_reviews(),
        }
class DashboardActivityService:

    @staticmethod
    def get_latest(limit=10):
        enrollments = (
            Enrollment.objects
            .select_related('crew_member', 'course')
            .order_by('-created_at')[:limit]
        )

        lesson_progress = (
            LessonProgress.objects
            .select_related('crew_member', 'lesson')
            .order_by('-created_at')[:limit]
        )

        reviews = (
            Review.objects
            .select_related('crew_member', 'course')
            .order_by('-created_at')[:limit]
        )

        activities = sorted(
            chain(enrollments, lesson_progress, reviews),
            key=attrgetter('created_at'),
            reverse=True
        )

        return activities[:limit]


class DashboardTrendService:

    @staticmethod
    def enrollment_trend():
        return (
            Enrollment.objects
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(total=Count('id'))
            .order_by('date')
        )