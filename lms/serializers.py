from rest_framework import serializers
from .models import Course, Lesson, Enrollment,LessonProgress,Choice,Question,Assessment,Review,Answer,AssessmentAttempt
from django.utils import timezone



class LessonNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id',
            'title',
            'description',
            'order',
            'content_url',
            'duration_minutes',
        ]  

class CourseListSerializer(serializers.ModelSerializer):
    instructor = serializers.StringRelatedField()
     
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
        ]
class CourseDetailSerializer(serializers.ModelSerializer):
    instructor = serializers.StringRelatedField()
    lessons = LessonNestedSerializer(many=True, read_only=True)
    assessments = serializers.StringRelatedField(many=True)
     
    class Meta:
        model = Course
        fields ="__all__"

class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    skills = serializers.ListField(child=serializers.CharField(max_length=50))
    outcomes = serializers.ListField(child=serializers.CharField(max_length=100))
    requirements = serializers.ListField(child=serializers.CharField(max_length=100))

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
        ]
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
        validated_data['skills'] = validated_data.get('skills', [])
        validated_data['outcomes'] = validated_data.get('outcomes', [])
        validated_data['requirements'] = validated_data.get('requirements', []) 
        # overwriting the create method to handle JSONFields
        return super().create(validated_data)
    def update(self, instance, validated_data):
        user = self.context['request'].user
        validated_data['updated_by'] = user
        validated_data['skills'] = validated_data.get('skills', instance.skills)
        validated_data['outcomes'] = validated_data.get('outcomes', instance.outcomes)
        validated_data['requirements'] = validated_data.get('requirements', instance.requirements) 
        # overwriting the update method to handle JSONFields
        return super().update(instance, validated_data)
    

class LessonSerializer(serializers.ModelSerializer):


    class Meta:
        model = Lesson
        fields = "__all__"

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
        user = self.context['request'].user

        if  not Enrollment.objects.filter(user=user, course=attrs['lesson'].course).exists():
            raise serializers.ValidationError("User is not enrolled in the course for this lesson.")
        return attrs
    
    def update(self, instance, validated_data):

        if validated_data.get('is_completed', instance.is_completed) and not instance.completed_at:
            instance.completed_at = timezone.now()
        return super().update(instance, validated_data)
    

class ChoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Choice
        fields = ["id", "text"]

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "question_type", "order", "choices"]

class AssessmentSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "title",
            "course",
            "description",
            "pass_mark",
            "is_published",
            "questions",
        ]

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
                attempt = data.get("attempt")
                question = data.get("question")
                choice = data.get("selected_choice")
                user = self.context['request'].user
                #  rule 1: Ensure question belongs to the assessment of the attempt
                if question.assessment != attempt.assessment:
                    raise serializers.ValidationError(
                        "Question does not belong to the assessment of this attempt."
                    )
                # rule 2: Ensure choice belongs to the question
                if choice.question != question:
                    raise serializers.ValidationError(
                        "Selected choice does not belong to the question."
                    )
                # Rule 3: Choice belongs to question
                if attempt.user != user:
                    raise serializers.ValidationError("You cannot answer another user's attempt.")

                return data
    

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Review
        fields = ["id", "user", "course", "rating", "comment", "created_at"]
        read_only_fields = ["created_at"]
