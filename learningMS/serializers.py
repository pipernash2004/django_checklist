from rest_framework import serializers
from .models import Course, Lesson, Enrollment, LessonProgress, Review, Achievement


# ============================================================
# COURSE SERIALIZERS
# ============================================================

class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for listing courses with essential fields."""
    instructor = serializers.StringRelatedField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'level', 'category', 'cover_image',
            'instructor', 'duration', 'course_type', 'skills',
            'average_rating', 'review_count'
        ]

    def get_average_rating(self, obj):
        """Calculate average rating from reviews."""
        reviews = obj.reviews.all()
        if not reviews.exists():
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def get_review_count(self, obj):
        """Count total reviews for course."""
        return obj.reviews.count()


class LessonBasicSerializer(serializers.ModelSerializer):
    """Serializer for lesson basic info (used in nested representations)."""

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order', 'duration', 'lesson_type']


class CourseDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed course information with nested lessons."""
    instructor = serializers.StringRelatedField()
    lessons = LessonBasicSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'level', 'category',
            'cover_image', 'instructor', 'duration', 'course_type',
            'skills', 'requirements', 'lessons',
            'average_rating', 'review_count', 'enrollment_count'
        ]

    def get_average_rating(self, obj):
        """Calculate average rating from reviews."""
        reviews = obj.reviews.all()
        if not reviews.exists():
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def get_review_count(self, obj):
        """Count total reviews for course."""
        return obj.reviews.count()

    def get_enrollment_count(self, obj):
        """Count total enrollments for course."""
        return obj.enrollments.count()


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating courses."""

    class Meta:
        model = Course
        fields = [
            'title', 'description', 'course_type', 'cover_image',
            'skills', 'requirements', 'level', 'category', 'duration'
        ]

    def validate_duration(self, value):
        """Validate duration is positive."""
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than 0.")
        return value

    def validate_skills(self, value):
        """Validate skills is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be a list.")
        if len(value) > 50:
            raise serializers.ValidationError("Maximum 50 skills allowed.")
        return value

    def validate_requirements(self, value):
        """Validate requirements is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Requirements must be a list.")
        if len(value) > 50:
            raise serializers.ValidationError("Maximum 50 requirements allowed.")
        return value

    def create(self, validated_data):
        """Create course with current user as instructor."""
        validated_data['instructor'] = self.context['request'].user
        return super().create(validated_data)


# ============================================================
# LESSON SERIALIZERS
# ============================================================

class LessonDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed lesson information."""
    course = serializers.PrimaryKeyRelatedField(read_only=True)
    completion_status = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'lesson_type', 'content_url',
            'order', 'duration', 'course', 'completion_status'
        ]

    def get_completion_status(self, obj):
        """Get user's completion status for this lesson."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        try:
            crew_member = request.user.crew_member
            progress = LessonProgress.objects.get(
                crew_member=crew_member,
                lesson=obj
            )
            return {
                'completed': True,
                'completed_at': progress.created_at
            }
        except (LessonProgress.DoesNotExist, AttributeError):
            return {
                'completed': False,
                'completed_at': None
            }


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating lessons."""

    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'lesson_type', 'content_url',
            'order', 'duration', 'course'
        ]

    def validate_duration(self, value):
        """Validate duration is positive."""
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than 0.")
        return value

    def validate_order(self, value):
        """Validate order is positive."""
        if value <= 0:
            raise serializers.ValidationError("Order must be greater than 0.")
        return value


# ============================================================
# ENROLLMENT SERIALIZERS
# ============================================================

class CourseMinimalSerializer(serializers.ModelSerializer):
    """Minimal course info for nested in enrollment."""

    class Meta:
        model = Course
        fields = ['id', 'title', 'category', 'duration']


class EnrollmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing enrollments."""
    course = CourseMinimalSerializer(read_only=True)
    lessons_completed = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'overall_progress', 'started_at',
            'completed_at', 'lessons_completed', 'total_lessons'
        ]

    def get_lessons_completed(self, obj):
        """Count completed lessons for this enrollment."""
        return LessonProgress.objects.filter(
            crew_member=obj.crew_member,
            lesson__course=obj.course
        ).count()

    def get_total_lessons(self, obj):
        """Get total lessons in course."""
        return obj.course.lessons.count()


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed enrollment information."""
    course = CourseDetailSerializer(read_only=True)
    lessons_completed = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()
    last_accessed_lesson = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'overall_progress', 'started_at',
            'completed_at', 'lessons_completed', 'total_lessons',
            'last_accessed_lesson'
        ]

    def get_lessons_completed(self, obj):
        """Count completed lessons."""
        return LessonProgress.objects.filter(
            crew_member=obj.crew_member,
            lesson__course=obj.course
        ).count()

    def get_total_lessons(self, obj):
        """Get total lessons in course."""
        return obj.course.lessons.count()

    def get_last_accessed_lesson(self, obj):
        """Get last completed lesson."""
        progress = LessonProgress.objects.filter(
            crew_member=obj.crew_member,
            lesson__course=obj.course
        ).select_related('lesson').order_by('-created_at').first()

        if progress:
            return {
                'id': progress.lesson.id,
                'title': progress.lesson.title,
                'order': progress.lesson.order
            }
        return None


# ============================================================
# LESSON PROGRESS SERIALIZER
# ============================================================

class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for lesson progress tracking."""
    lesson = LessonBasicSerializer(read_only=True)

    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# REVIEW SERIALIZERS
# ============================================================

class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer for listing reviews."""
    crew_member_name = serializers.CharField(
        source='crew_member.name',
        read_only=True
    )

    class Meta:
        model = Review
        fields = ['id', 'crew_member_name', 'rating', 'comment', 'created_at']

    def to_representation(self, instance):
        """Truncate comment for list view."""
        data = super().to_representation(instance)
        if data.get('comment') and len(data['comment']) > 40:
            data['comment'] = data['comment'][:40] + '...'
        return data


class ReviewDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed review information."""
    crew_member = serializers.StringRelatedField(read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'crew_member', 'rating', 'comment',
            'created_at', 'updated_at', 'can_edit', 'can_delete'
        ]

    def get_can_edit(self, obj):
        """Check if current user can edit this review."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.crew_member.user == request.user

    def get_can_delete(self, obj):
        """Check if current user can delete this review."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.crew_member.user == request.user


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews."""

    class Meta:
        model = Review
        fields = ['course', 'rating', 'comment']

    def validate_rating(self, value):
        """Validate rating is between 1 and 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_comment(self, value):
        """Validate comment is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment cannot be empty.")
        return value

    def validate(self, data):
        """Check if user already has a review for this course."""
        request = self.context.get('request')
        course = data.get('course')

        if request and request.user.is_authenticated:
            try:
                crew_member = request.user.crew_member
                existing = Review.objects.filter(
                    crew_member=crew_member,
                    course=course
                ).exists()
                if existing:
                    raise serializers.ValidationError(
                        "You have already reviewed this course."
                    )
            except AttributeError:
                pass

        return data

    def create(self, validated_data):
        """Create review with current user as reviewer."""
        request = self.context.get('request')
        validated_data['crew_member'] = request.user.crew_member
        return super().create(validated_data)


# ============================================================
# ACHIEVEMENT SERIALIZERS
# ============================================================

class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for achievements/badges."""
    category = serializers.SerializerMethodField()
    earned_date = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'icon', 'category', 'earned_date']

    def get_category(self, obj):
        """Derive category from achievement title."""
        title_lower = obj.title.lower()
        if 'course' in title_lower:
            return 'course'
        elif 'lesson' in title_lower:
            return 'lesson'
        elif 'learning' in title_lower or 'streak' in title_lower:
            return 'engagement'
        else:
            return 'other'

#  dashboard serialzier
class DashboardOverviewSerializer(serializers.Serializer):
    in_progress_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    total_lessons_completed = serializers.IntegerField()
    total_learning_hours = serializers.FloatField()
    recent_achievements = AchievementSerializer(many=True)


class CourseProgressSerializer(serializers.Serializer):
    """Serializer that matches the progress item returned by the dashboard `progress` endpoint."""
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    overall_progress = serializers.IntegerField()
    lessons_completed = serializers.IntegerField()
    total_lessons = serializers.IntegerField()
    started_at = serializers.DateTimeField(allow_null=True)
    completed_at = serializers.DateTimeField(allow_null=True, required=False)