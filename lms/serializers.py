from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from .models import (
    Course, Lesson, Enrollment, LessonProgress,
    Choice, Question, Assessment, Review,
    Answer, AssessmentAttempt
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
    class Meta:
        model = LessonProgress
        fields = "__all__"
        read_only_fields = ["completed_at"]

    def validate(self, attrs):
        user = self.context["request"].user
        if not Enrollment.objects.filter(
            user=user, course=attrs["lesson"].course
        ).exists():
            raise serializers.ValidationError(
                "User is not enrolled in this course."
            )
        return attrs

    def update(self, instance, validated_data):
        if validated_data.get("is_completed") and not instance.completed_at:
            instance.completed_at = timezone.now()
        return super().update(instance, validated_data)


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
class DashboardCourseSerializer(serializers.Serializer):
    enrollments_count = serializers.IntegerField()
    average_rating = serializers.FloatField()

    class Meta:
        model = Course
        fields = [
        
            "title",
            "instructor",
            "enrollments_count",
            "average_rating",
        ]