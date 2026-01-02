from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from .models import (
    Course, Lesson, Enrollment, LessonProgress,
    Choice, Question, Assessment, Review,
    Answer, AssessmentAttempt, ActivityLog
)

# ============================================================
# READ (NESTED) SERIALIZERS
# ============================================================

class LessonNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "description",  
            "content_url",
            "duration_minutes",
        ]


class ChoiceNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]


class QuestionNestedSerializer(serializers.ModelSerializer):
    choices = ChoiceNestedSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "text", "question_type", "choices"]


class AssessmentNestedSerializer(serializers.ModelSerializer):
    questions = QuestionNestedSerializer(many=True)
    course = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Assessment
        # fields = [
        #     "id",
        #     "title",
        #     "description",
        #     "pass_mark",
        #     "is_published",
        #     "questions",
        # ]
        exclude = ("created_by", "updated_by" )


# ============================================================
# COURSE LIST & DETAIL
# ============================================================

class CourseListSerializer(serializers.ModelSerializer):
 

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "level",
            "status",
            "course_type",
            "content_type",
            "duration_weeks",
            "instructor",
            "thumbnail",
            "skills",
            "outcomes",
            "requirements",
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    lessons = LessonNestedSerializer(many=True,read_only=True)
    assessments = AssessmentNestedSerializer(many=True,read_only=True)

    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "level",
            "status",
            "skills",
            "outcomes",
            "requirements",
            "course_type",
            "content_type",
            "duration_weeks",
            "instructor",
            "thumbnail",
            "lessons",
            "assessments",
        ]

   

# ============================================================
# WRITE SERIALIZERS (CREATE / UPDATE)
# ============================================================

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceNestedSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "text", "question_type",  "choices"]

    def create(self, validated_data):
        choices_data = validated_data.pop("choices", [])
        question_obj= Question.objects.create(**validated_data)

        for choice in choices_data:
            Choice.objects.create(question_obj=question_obj, **choice)

        return question_obj


class AssessmentSerializer(serializers.ModelSerializer):
    questions = QuestionNestedSerializer(many=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "title",
            "description",
            "pass_mark",
            "is_published",
            "course",
            "questions",
        ]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        request = self.context["request"]

        assessment = Assessment.objects.create(
            **validated_data,
            created_by=request.user,
            updated_by=request.user,
        )

        for order, question in enumerate(questions_data, start=1):
            question.setdefault("order", order * 10)
            Question.objects.create(assessment=assessment, **question)
        return assessment


# ============================================================
# FULL COURSE CREATE (LESSONS + ASSESSMENTS)
# ============================================================
class CourseCreateUpdateSerializer(CourseListSerializer):

    def create (self, validated_data ):

        request = self.context["request"]
        course = Course.objects.create(
            **validated_data
        )
        return course
    
class CourseFullCreateSerializer(serializers.ModelSerializer):
    lessons = LessonNestedSerializer(many=True)
    assessments = AssessmentNestedSerializer(many=True)

    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "level",
            "status",
            "skills",
            "outcomes",
            "requirements",
            "course_type",
            "content_type",
            "duration_weeks",
            "instructor",
            "thumbnail",
            "lessons",
            "assessments",
        ]

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]

        lessons_data = validated_data.pop("lessons", [])
        assessments_data = validated_data.pop("assessments", [])

        course = Course.objects.create(
            **validated_data,
            created_by=request.user,
            updated_by=request.user
        )

      
        for order, lesson in enumerate(lessons_data, start=1):
            lesson.setdefault("order", order * 10)
            Lesson.objects.create(course=course, **lesson)

       
        for assessment in assessments_data:
            questions = assessment.pop("questions", [])
            assessment_obj = Assessment.objects.create(
                course=course,
                **assessment
            )

            for q_order, question in enumerate(questions, start=1):
                choices = question.pop("choices", [])
                question.setdefault("order", q_order * 10)

                question_obj = Question.objects.create(
                    assessment=assessment_obj,
                    **question
                )

                for choice in choices:
                    Choice.objects.create(
                        question=question_obj,
                        **choice
                    )

        return course
class CourseFullUpdateSerializer(serializers.ModelSerializer):
    lessons = LessonNestedSerializer(many=True)
    assessments = AssessmentNestedSerializer(many=True)

    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "level",
            "status",
            "skills",
            "outcomes",
            "requirements",
            "course_type",
            "content_type",
            "duration_weeks",
            "instructor",
            "thumbnail",
            "lessons",
            "assessments",
        ]

   


# ============================================================
# ENROLLMENT & PROGRESS
# ============================================================

class EnrollmentSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Enrollment
        fields = ["id", "user", "course", "enrolled_at"]
        read_only_fields = ["enrolled_at"]


class LessonProgressSerializer(serializers.ModelSerializer):
    mark_complete = serializers.BooleanField(
    write_only=True,
    required=False,
    help_text="User intent to manually complete non-video lessons")
    session_data = serializers.JSONField(
        required=False,
        help_text="Additional session data related to progress"
    )

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "progress_value",
            'mark_complete',
            "session_data",
        "is_completed",
        "completed_at",

        ]
        read_only_fields = ["completed_at", "is_completed"]


    def validate(self, attrs):
        request = self.context.get("request")
        lesson = self.context.get("lesson")

        if request is None or lesson is None:
            raise serializers.ValidationError("Invalid serializer context.")

        user = request.user

        if not Enrollment.objects.filter(
            user=user,
            course=lesson.course
        ).exists():
            raise serializers.ValidationError(
                "User is not enrolled in this course."
            )

        lesson_type = lesson.course.content_type

        progress_value = attrs.get("progress_value")
        mark_complete = attrs.get("mark_complete", False)

        if lesson_type == "video":
            if progress_value is None or not (0.0 <= progress_value <= 100.0):
                raise serializers.ValidationError(
                    {"progress_value": "For video lessons, progress_value must be between 0 and 100."}
                )
            if mark_complete:
                raise serializers.ValidationError(
                    {"mark_complete": "Manual completion is not allowed for video lessons."}
                )
        else:
            if progress_value is not None:
                raise serializers.ValidationError(
                    {"progress_value": "progress_value is not applicable for this lesson type."}
                )

        return attrs


    

# ============================================================
# ASSESSMENT ATTEMPTS & ANSWERS
# ============================================================

class AssessmentAttemptSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = AssessmentAttempt
        fields = ["id", "user", "assessment"]


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "attempt", "question", "selected_choice"]

    def validate(self, data):
        attempt = data["attempt"]
        question = data["question"]
        choice = data["selected_choice"]
        user = self.context["request"].user

        if question.assessment != attempt.assessment:
            raise serializers.ValidationError(
                "Question does not belong to this assessment."
            )

        if choice.question != question:
            raise serializers.ValidationError(
                "Choice does not belong to this question."
            )

        if attempt.user != user:
            raise serializers.ValidationError(
                "You cannot answer another user's attempt."
            )

        return data


# ============================================================
# REVIEWS
# ============================================================

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Review
        fields = ["id", "user", "course", "rating", "comment", "created_at"]
        read_only_fields = ["created_at"]

# ============================================================
# Dashboard SERIALIZERS
# ============================================================
class StatsSerializer(serializers.Serializer):
    total_courses = serializers.IntegerField()
    total_students = serializers.IntegerField()
    pending_reviews = serializers.IntegerField()
    active_assessments = serializers.IntegerField()
    
    
class EnrollmentTrendItemSerializer(serializers.Serializer):
    date = serializers.DateField()
    label = serializers.CharField()
    count = serializers.IntegerField(min_value=0)

class EnrollmentTrendSerializer(serializers.Serializer):
    range = serializers.CharField()
    growth_percentage = serializers.FloatField()
    data = EnrollmentTrendItemSerializer(many=True)


  

class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
  

    class Meta:
        model = ActivityLog
        fields = [
            "user_name",
            "action",
            "target_name",
            "created_at",
        ]
    
class DashboardSerializer(serializers.Serializer):
    stats = StatsSerializer()
    enrollment_trends = EnrollmentTrendSerializer()
    recent_activities = ActivityLogSerializer(many=True)

