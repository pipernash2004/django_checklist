from rest_framework import serializers
from django.db import transaction
from .models import (
    Course, Lesson, Assessment, Choice, Question,
    Enrollment, LessonProgress, Review, AssessmentAttempt, Answer
)


# ============================================================
# LESSON SERIALIZERS
# ============================================================

class LessonListSerializer(serializers.ModelSerializer):
    """List view of lessons - basic info only."""
    
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order', 'duration_minutes', 'course']
        read_only_fields = ['id']


class LessonDetailSerializer(serializers.ModelSerializer):
    """Detailed lesson view."""
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'order', 'duration_minutes',
            'content_url', 'course', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    """For creating/updating lessons."""
    
    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'order', 'duration_minutes',
            'content_url', 'course'
        ]


# ============================================================
# CHOICE SERIALIZERS
# ============================================================

class ChoiceListSerializer(serializers.ModelSerializer):
    """List view of choices."""
    
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct', 'question']
        read_only_fields = ['id']


class ChoiceDetailSerializer(serializers.ModelSerializer):
    """Detailed choice view."""
    
    class Meta:
        model = Choice
        fields = [
            'id', 'text', 'is_correct', 'question',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ChoiceCreateUpdateSerializer(serializers.ModelSerializer):
    """For creating/updating choices."""
    
    class Meta:
        model = Choice
        fields = ['text', 'is_correct', 'question']


# ============================================================
# QUESTION SERIALIZERS
# ============================================================

class QuestionListSerializer(serializers.ModelSerializer):
    """List view of questions."""
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'order', 'question_type', 'assessment']
        read_only_fields = ['id']


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Detailed question view with choices."""
    choices = ChoiceListSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'order', 'question_type', 'assessment',
            'choices', 'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    """For creating/updating questions."""
    
    class Meta:
        model = Question
        fields = ['text', 'order', 'question_type', 'assessment']


# ============================================================
# ASSESSMENT SERIALIZERS
# ============================================================

class AssessmentListSerializer(serializers.ModelSerializer):
    """List view of assessments."""
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'course', 'pass_mark', 'is_published',
            'question_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_question_count(self, obj):
        """Return number of questions in assessment."""
        return obj.questions.count()


class AssessmentDetailSerializer(serializers.ModelSerializer):
    """Detailed assessment view with questions."""
    questions = QuestionDetailSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'description', 'course', 'pass_mark',
            'is_published', 'questions', 'question_count',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_question_count(self, obj):
        """Return number of questions in assessment."""
        return obj.questions.count()


class AssessmentCreateUpdateSerializer(serializers.ModelSerializer):
    """For creating/updating assessments."""
    
    class Meta:
        model = Assessment
        fields = [
            'title', 'description', 'course', 'pass_mark', 'is_published'
        ]


# ============================================================
# COURSE SERIALIZERS
# ============================================================

class CourseListSerializer(serializers.ModelSerializer):
    """List view of courses - essential fields only."""
    lesson_count = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'level', 'status', 'course_type',
            'duration_weeks', 'instructor', 'lesson_count',
            'enrollment_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_lesson_count(self, obj):
        return obj.lessons.count()
    
    def get_enrollment_count(self, obj):
        return obj.enrollments.count()


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed course view with lessons and assessments."""
    lessons = LessonListSerializer(many=True, read_only=True)
    assessments = AssessmentListSerializer(many=True, read_only=True)
    lesson_count = serializers.SerializerMethodField()
    assessment_count = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'level', 'status', 'course_type',
            'content_type', 'duration_weeks', 'instructor', 'thumbnail',
            'skills', 'requirements', 'outcomes',
            'lessons', 'assessments', 'lesson_count', 'assessment_count',
            'enrollment_count', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_lesson_count(self, obj):
        return obj.lessons.count()
    
    def get_assessment_count(self, obj):
        return obj.assessments.count()
    
    def get_enrollment_count(self, obj):
        return obj.enrollments.count()


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """For creating/updating courses."""
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'level', 'status', 'course_type',
            'content_type', 'duration_weeks', 'instructor', 'thumbnail',
            'skills', 'requirements', 'outcomes'
        ]


# ============================================================
# ENROLLMENT SERIALIZERS
# ============================================================

class EnrollmentListSerializer(serializers.ModelSerializer):
    """List view of enrollments."""
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'user', 'user_name', 'course', 'course_title', 'enrolled_at'
        ]
        read_only_fields = ['id', 'enrolled_at']


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """Detailed enrollment view."""
    course = CourseListSerializer(read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'user', 'user_name', 'course', 'enrolled_at'
        ]
        read_only_fields = ['id', 'enrolled_at']


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """For creating enrollments."""
    
    class Meta:
        model = Enrollment
        fields = ['user', 'course']


# ============================================================
# LESSON PROGRESS SERIALIZERS
# ============================================================

class LessonProgressListSerializer(serializers.ModelSerializer):
    """List view of lesson progress."""
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    course_title = serializers.CharField(source='lesson.course.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'user', 'user_name', 'lesson', 'lesson_title',
            'course_title', 'is_completed', 'completed_at'
        ]
        read_only_fields = ['id']


class LessonProgressDetailSerializer(serializers.ModelSerializer):
    """Detailed progress view."""
    lesson = LessonListSerializer(read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'user', 'user_name', 'lesson', 'is_completed',
            'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LessonProgressCreateUpdateSerializer(serializers.ModelSerializer):
    """For creating/updating lesson progress."""
    
    class Meta:
        model = LessonProgress
        fields = ['user', 'lesson', 'is_completed', 'completed_at']


# ============================================================
# REVIEW SERIALIZERS
# ============================================================

class ReviewListSerializer(serializers.ModelSerializer):
    """List view of reviews."""
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_name', 'course', 'course_title',
            'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ReviewDetailSerializer(serializers.ModelSerializer):
    """Detailed review view."""
    course = CourseListSerializer(read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_name', 'course', 'rating', 'comment',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """For creating/updating reviews."""
    
    class Meta:
        model = Review
        fields = ['user', 'course', 'rating', 'comment']


# ============================================================
# ASSESSMENT ATTEMPT SERIALIZERS
# ============================================================

class AssessmentAttemptListSerializer(serializers.ModelSerializer):
    """List view of assessment attempts."""
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = AssessmentAttempt
        fields = [
            'id', 'user', 'user_name', 'assessment', 'assessment_title',
            'score', 'passed', 'completed_at'
        ]
        read_only_fields = ['id']


class AssessmentAttemptDetailSerializer(serializers.ModelSerializer):
    """Detailed attempt view."""
    assessment = AssessmentListSerializer(read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = AssessmentAttempt
        fields = [
            'id', 'user', 'user_name', 'assessment', 'score', 'passed',
            'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AssessmentAttemptCreateSerializer(serializers.ModelSerializer):
    """For creating assessment attempts."""
    
    class Meta:
        model = AssessmentAttempt
        fields = ['user', 'assessment', 'score', 'passed', 'completed_at']


# ============================================================
# ANSWER SERIALIZERS
# ============================================================

class AnswerListSerializer(serializers.ModelSerializer):
    """List view of answers."""
    question_text = serializers.CharField(source='question.text', read_only=True)
    choice_text = serializers.CharField(source='selected_choice.text', read_only=True)
    
    class Meta:
        model = Answer
        fields = [
            'id', 'attempt', 'question', 'question_text',
            'selected_choice', 'choice_text', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AnswerDetailSerializer(serializers.ModelSerializer):
    """Detailed answer view."""
    question = QuestionListSerializer(read_only=True)
    selected_choice = ChoiceListSerializer(read_only=True)
    
    class Meta:
        model = Answer
        fields = [
            'id', 'attempt', 'question', 'selected_choice', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AnswerCreateUpdateSerializer(serializers.ModelSerializer):
    """For creating/updating answers."""
    
    class Meta:
        model = Answer
        fields = ['attempt', 'question', 'selected_choice']


# ============================================================
# NESTED FULL SERIALIZERS (Course with all nested content)
# ============================================================

class NestedChoiceSerializer(serializers.ModelSerializer):
    """Nested choice serializer for question creation."""
    
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']


class NestedQuestionSerializer(serializers.ModelSerializer):
    """Nested question serializer with choices for assessment creation."""
    choices = NestedChoiceSerializer(many=True, required=False)
    
    class Meta:
        model = Question
        fields = ['text', 'order', 'question_type', 'choices']
    
    def create(self, validated_data):
        """Create question with nested choices."""
        choices_data = validated_data.pop('choices', [])
        question = Question.objects.create(**validated_data)
        
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        
        return question
    
    def update(self, instance, validated_data):
        """Update question and its choices."""
        choices_data = validated_data.pop('choices', None)
        
        # Update question fields
        instance.text = validated_data.get('text', instance.text)
        instance.order = validated_data.get('order', instance.order)
        instance.question_type = validated_data.get('question_type', instance.question_type)
        instance.save()
        
        # Replace choices if provided
        if choices_data is not None:
            instance.choices.all().delete()
            for choice_data in choices_data:
                Choice.objects.create(question=instance, **choice_data)
        
        return instance


class NestedAssessmentSerializer(serializers.ModelSerializer):
    """Nested assessment serializer with questions and choices."""
    questions = NestedQuestionSerializer(many=True, required=False)
    
    class Meta:
        model = Assessment
        fields = ['title', 'description', 'pass_mark', 'is_published', 'questions']
    
    def create(self, validated_data):
        """Create assessment with nested questions and choices."""
        questions_data = validated_data.pop('questions', [])
        assessment = Assessment.objects.create(**validated_data)
        
        for question_data in questions_data:
            choices_data = question_data.pop('choices', [])
            question = Question.objects.create(assessment=assessment, **question_data)
            
            for choice_data in choices_data:
                Choice.objects.create(question=question, **choice_data)
        
        return assessment
    
    def update(self, instance, validated_data):
        """Update assessment and its nested questions and choices."""
        questions_data = validated_data.pop('questions', None)
        
        # Update assessment fields
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.pass_mark = validated_data.get('pass_mark', instance.pass_mark)
        instance.is_published = validated_data.get('is_published', instance.is_published)
        instance.save()
        
        # Replace questions if provided
        if questions_data is not None:
            instance.questions.all().delete()
            for question_data in questions_data:
                choices_data = question_data.pop('choices', [])
                question = Question.objects.create(assessment=instance, **question_data)
                
                for choice_data in choices_data:
                    Choice.objects.create(question=question, **choice_data)
        
        return instance


class NestedLessonSerializer(serializers.ModelSerializer):
    """Nested lesson serializer for course creation."""
    
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'order', 'duration_minutes', 'content_url']
    
    def create(self, validated_data):
        """Create lesson."""
        return Lesson.objects.create(**validated_data)


class CourseFullCreateSerializer(serializers.ModelSerializer):
    """
    Full course creation serializer with nested lessons and assessments.
    
    Allows creating a complete course structure in one request:
    - Course
    - Lessons (with all lesson details)
    - Assessments (with questions and choices)
    
    Example:
    POST /api/courses/full-create/
    {
        "title": "Python 101",
        "description": "Learn Python basics",
        "level": "beginner",
        "status": "draft",
        "course_type": "free",
        "content_type": "video",
        "duration_weeks": 4,
        "instructor": 1,
        "skills": ["Python", "Programming"],
        "requirements": ["Basic Math"],
        "outcomes": ["Write Python code", "Understand OOP"],
        "thumbnail": null,
        "lessons": [
            {
                "title": "Introduction",
                "description": "Course overview",
                "order": 1,
                "duration_minutes": 30,
                "content_url": "https://example.com/video1"
            },
            {
                "title": "Variables",
                "description": "Learn variables",
                "order": 2,
                "duration_minutes": 45,
                "content_url": "https://example.com/video2"
            }
        ],
        "assessments": [
            {
                "title": "Quiz 1",
                "description": "Chapter 1 Quiz",
                "pass_mark": 70,
                "is_published": false,
                "questions": [
                    {
                        "text": "What is a variable?",
                        "order": 1,
                        "question_type": "mcq",
                        "choices": [
                            {"text": "A container for data", "is_correct": true},
                            {"text": "A function", "is_correct": false},
                            {"text": "A class", "is_correct": false}
                        ]
                    }
                ]
            }
        ]
    }
    """
    lessons = NestedLessonSerializer(many=True, required=False)
    assessments = NestedAssessmentSerializer(many=True, required=False)
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'level', 'status', 'course_type',
            'content_type', 'duration_weeks', 'instructor', 'thumbnail',
            'skills', 'requirements', 'outcomes', 'lessons', 'assessments'
        ]
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Create course with nested lessons and assessments.
        Uses transaction.atomic to ensure all-or-nothing behavior.
        """
        request = self.context.get('request')
        lessons_data = validated_data.pop('lessons', [])
        assessments_data = validated_data.pop('assessments', [])
        
        # Create course
        course = Course.objects.create(
            **validated_data,
            # created_by=request.user if request else None,
            # updated_by=request.user if request else None
        )
        
        # Create lessons
        for lesson_data in lessons_data:
            lesson_data['course'] = course
            lesson_data['created_by'] = request.user if request else None
            lesson_data['updated_by'] = request.user if request else None
            Lesson.objects.create(**lesson_data)
        
        # Create assessments with nested questions and choices
        for assessment_data in assessments_data:
            assessment_data['course'] = course
            assessment_data['created_by'] = request.user if request else None
            assessment_data['updated_by'] = request.user if request else None
            
            # Use serializer to handle nested creation
            nested_serializer = NestedAssessmentSerializer(
                data=assessment_data,
                context=self.context
            )
            if nested_serializer.is_valid(raise_exception=True):
                nested_serializer.save(**{
                    'course': course,
                    'created_by': request.user if request else None,
                    'updated_by': request.user if request else None
                })
        
        return course


class CourseFullDetailSerializer(serializers.ModelSerializer):
    """
    Full course detail serializer with all nested content.
    Used for GET requests to return complete course structure.
    """
    lessons = LessonDetailSerializer(many=True, read_only=True)
    assessments = AssessmentDetailSerializer(many=True, read_only=True)
    lesson_count = serializers.SerializerMethodField()
    assessment_count = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'level', 'status', 'course_type',
            'content_type', 'duration_weeks', 'instructor', 'thumbnail',
            'skills', 'requirements', 'outcomes', 'lessons', 'assessments',
            'lesson_count', 'assessment_count', 'enrollment_count',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_lesson_count(self, obj):
        return obj.lessons.count()
    
    def get_assessment_count(self, obj):
        return obj.assessments.count()
    
    def get_enrollment_count(self, obj):
        return obj.enrollments.count()


class CourseFullUpdateSerializer(serializers.ModelSerializer):
    """
    Full course update serializer for PUT requests.
    Allows updating course and replacing all nested lessons and assessments.
    """
    lessons = NestedLessonSerializer(many=True, required=False)
    assessments = NestedAssessmentSerializer(many=True, required=False)
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'level', 'status', 'course_type',
            'content_type', 'duration_weeks', 'instructor', 'thumbnail',
            'skills', 'requirements', 'outcomes', 'lessons', 'assessments'
        ]
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update course and replace all nested lessons and assessments.
        """
        request = self.context.get('request')
        lessons_data = validated_data.pop('lessons', None)
        assessments_data = validated_data.pop('assessments', None)
        
        # Update course fields
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.level = validated_data.get('level', instance.level)
        instance.status = validated_data.get('status', instance.status)
        instance.course_type = validated_data.get('course_type', instance.course_type)
        instance.content_type = validated_data.get('content_type', instance.content_type)
        instance.duration_weeks = validated_data.get('duration_weeks', instance.duration_weeks)
        instance.instructor = validated_data.get('instructor', instance.instructor)
        instance.thumbnail = validated_data.get('thumbnail', instance.thumbnail)
        instance.skills = validated_data.get('skills', instance.skills)
        instance.requirements = validated_data.get('requirements', instance.requirements)
        instance.outcomes = validated_data.get('outcomes', instance.outcomes)
        instance.updated_by = request.user if request else instance.updated_by
        instance.save()
        
        # Replace lessons if provided
        if lessons_data is not None:
            instance.lessons.all().delete()
            for lesson_data in lessons_data:
                lesson_data['course'] = instance
                lesson_data['created_by'] = request.user if request else None
                lesson_data['updated_by'] = request.user if request else None
                Lesson.objects.create(**lesson_data)
        
        # Replace assessments if provided
        if assessments_data is not None:
            instance.assessments.all().delete()
            for assessment_data in assessments_data:
                assessment_data['course'] = instance
                assessment_data['created_by'] = request.user if request else None
                assessment_data['updated_by'] = request.user if request else None
                
                nested_serializer = NestedAssessmentSerializer(
                    data=assessment_data,
                    context=self.context
                )
                if nested_serializer.is_valid(raise_exception=True):
                    nested_serializer.save(**{
                        'course': instance,
                        'created_by': request.user if request else None,
                        'updated_by': request.user if request else None
                    })
        
        return instance


class CourseFullPatchSerializer(serializers.ModelSerializer):
    """
    Full course patch serializer for PATCH requests.
    Allows partial updates including selectively updating nested content.
    """
    lessons = NestedLessonSerializer(many=True, required=False)
    assessments = NestedAssessmentSerializer(many=True, required=False)
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'level', 'status', 'course_type',
            'content_type', 'duration_weeks', 'instructor', 'thumbnail',
            'skills', 'requirements', 'outcomes', 'lessons', 'assessments'
        ]
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Partially update course and optionally update nested content.
        Only provided fields are updated; others remain unchanged.
        """
        request = self.context.get('request')
        lessons_data = validated_data.pop('lessons', None)
        assessments_data = validated_data.pop('assessments', None)
        
        # Update only provided course fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_by = request.user if request else instance.updated_by
        instance.save()
        
        # Update lessons only if provided
        if lessons_data is not None:
            instance.lessons.all().delete()
            for lesson_data in lessons_data:
                lesson_data['course'] = instance
                lesson_data['created_by'] = request.user if request else None
                lesson_data['updated_by'] = request.user if request else None
                Lesson.objects.create(**lesson_data)
        
        # Update assessments only if provided
        if assessments_data is not None:
            instance.assessments.all().delete()
            for assessment_data in assessments_data:
                assessment_data['course'] = instance
                assessment_data['created_by'] = request.user if request else None
                assessment_data['updated_by'] = request.user if request else None
                
                nested_serializer = NestedAssessmentSerializer(
                    data=assessment_data,
                    context=self.context
                )
                if nested_serializer.is_valid(raise_exception=True):
                    nested_serializer.save(**{
                        'course': instance,
                        'created_by': request.user if request else None,
                        'updated_by': request.user if request else None
                    })
        
        return instance
    


