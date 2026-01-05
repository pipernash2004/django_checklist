from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Course, Lesson, Enrollment, LessonProgress, Review, Answer,
    Assessment, AssessmentAttempt, Choice, Question, ActivityLog
)


# ============================================================
# INLINE ADMINS (Nested Resources)
# ============================================================

class ChoiceInline(admin.TabularInline):
    """
    Inline admin for Choice within Question.
    Allows selection of correct answer while editing question.
    """
    model = Choice
    extra = 1
    fields = ['text', 'is_correct']


class ChoiceInlineForQuestion(admin.TabularInline):
    """
    Inline admin for Choice within Question (nested inside Assessment).
    Allows selection of correct answer while editing question inline.
    """
    model = Choice
    extra = 1
    fields = ['text', 'is_correct']


class QuestionInline(admin.TabularInline):
    """
    Inline admin for Question within Assessment.
    Allows course creators to add questions while editing assessments.
    """
    model = Question
    extra = 1
    fields = ['text', 'question_type', 'order']
    ordering = ['order']
    inlines = [ChoiceInline]


class QuestionInlineForAssessment(admin.TabularInline):
    """
    Inline admin for Question within Assessment (nested inside Course).
    Allows adding questions directly while editing assessment.
    """
    model = Question
    extra = 1
    fields = ['text', 'question_type', 'order']
    ordering = ['order']
    inlines = [ChoiceInlineForQuestion]


class LessonInline(admin.TabularInline):
    """
    Inline admin for Lesson within Course.
    Allows instructors to add/edit lessons directly from course page.
    """
    model = Lesson
    extra = 1
    fields = ['title', 'order', 'duration_minutes', 'content_url']
    ordering = ['order']


class AssessmentInline(admin.TabularInline):
    """
    Inline admin for Assessment within Course.
    Allows instructors to create assessments/quizzes directly from course page.
    """
    model = Assessment
    extra = 1
    fields = ['title', 'pass_mark', 'is_published']
    inlines = [QuestionInline, ChoiceInline]


class AnswerInline(admin.TabularInline):
    """
    Inline admin for Answer within AssessmentAttempt.
    Shows student's selected choices for each question.
    """
    model = Answer
    extra = 0
    fields = ['question', 'selected_choice']
    readonly_fields = ['question', 'selected_choice']
    can_delete = False


# ============================================================
# COURSE ADMIN
# ============================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Admin interface for Course management.
    
    Features:
    - Group by status (draft, published, scheduled)
    - Filter by level, course_type, content_type
    - Search by title and description
    - Inline lesson management
    - Automatic timestamp and user tracking
    """
    
    list_display = [
        'title', 'status_badge', 'level', 'course_type', 'instructor',
        'duration_weeks', 'lesson_count', 'enrollment_count', 'created_at'
    ]
    list_filter = ['status', 'level', 'course_type', 'content_type', 'created_at']
    search_fields = ['title', 'description', 'instructor__username']
    
    fieldsets = (
        ('Course Information', {
            'fields': ('title', 'description', 'status', 'thumbnail')
        }),
        ('Course Details', {
            'fields': ('level', 'course_type', 'content_type', 'duration_weeks', 'instructor')
        }),
        ('Learning Content', {
            'fields': ('skills', 'requirements', 'outcomes'),
            'classes': ('collapse',),
            'description': 'Define skills taught, prerequisites, and expected outcomes'
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Auto-managed system fields'
        })
    )
    
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [LessonInline, AssessmentInline]
    ordering = ['-created_at']
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'draft': '#CCCCCC',
            'published': '#90EE90',
            'scheduled': '#FFD700'
        }
        return format_html(
            '<span style="background-color: {}; padding: 5px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#CCCCCC'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def lesson_count(self, obj):
        """Show number of lessons in course."""
        return obj.lessons.count()
    lesson_count.short_description = 'Lessons'
    
    def enrollment_count(self, obj):
        """Show number of student enrollments."""
        return obj.enrollments.count()
    enrollment_count.short_description = 'Enrollments'
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by and updated_by."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# LESSON ADMIN
# ============================================================

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """
    Admin interface for Lesson management.
    
    Features:
    - View lessons by course
    - Filter by course
    - Search by title and description
    - Order lessons by sequence
    """
    
    list_display = ['title', 'course', 'order', 'duration_minutes', 'content_url', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['title', 'description', 'course__title']
    ordering = ['course', 'order']
    
    fieldsets = (
        ('Lesson Information', {
            'fields': ('course', 'title', 'description', 'order')
        }),
        ('Lesson Content', {
            'fields': ('content_url', 'duration_minutes'),
            'description': 'URL to lesson content and duration in minutes'
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by and updated_by."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# ENROLLMENT ADMIN
# ============================================================

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Enrollment tracking.
    
    Features:
    - View student enrollments
    - Filter by course and enrollment date
    - Search by student username/name and course title
    - Read-only fields (enrollment is immutable after creation)
    """
    
    list_display = ['user', 'course', 'enrolled_at', 'progress_percentage']
    list_filter = ['course', 'enrolled_at']
    search_fields = ['user__username', 'user__first_name', 'course__title']
    readonly_fields = ['enrolled_at']
    ordering = ['-enrolled_at']
    
    fieldsets = (
        ('Enrollment Details', {
            'fields': ('user', 'course', 'enrolled_at')
        }),
    )
    
    def progress_percentage(self, obj):
        """Calculate student's progress in course."""
        lessons = obj.course.lessons.count()
        if lessons == 0:
            return "0%"
        completed = LessonProgress.objects.filter(
            user=obj.user,
            lesson__course=obj.course,
            is_completed=True
        ).count()
        percentage = (completed / lessons) * 100
        color = '#90EE90' if percentage >= 70 else '#FFD700' if percentage >= 50 else '#FF6B6B'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            percentage
        )
    progress_percentage.short_description = 'Progress'


# ============================================================
# LESSON PROGRESS ADMIN
# ============================================================

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    """
    Admin interface for tracking lesson completion.
    
    Features:
    - View student's lesson completion status
    - Filter by completion status and date
    - Search by student and lesson title
    - Track completion timestamps
    """
    
    list_display = ['user', 'lesson_title', 'course_title', 'progress_value','completion_status', 'completed_at']
    list_filter = ['is_completed', 'created_at', 'completed_at']
    search_fields = ['user__username', 'lesson__title', 'lesson__course__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-completed_at']
    
    fieldsets = (
        ('Progress Information', {
            'fields': ('user', 'lesson', 'is_completed', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def lesson_title(self, obj):
        """Display lesson title."""
        return obj.lesson.title
    lesson_title.short_description = 'Lesson'
    
    def course_title(self, obj):
        """Display course title for easier navigation."""
        return obj.lesson.course.title
    course_title.short_description = 'Course'
    
    def completion_status(self, obj):
        """Display completion status as badge."""
        if obj.is_completed:
            return format_html(
                '<span style="background-color: #90EE90; padding: 5px 10px; border-radius: 3px;">✓ Completed</span>'
            )
        return format_html(
            '<span style="background-color: #FFD700; padding: 5px 10px; border-radius: 3px;">In Progress</span>'
        )
    completion_status.short_description = 'Status'


# ============================================================
# REVIEW ADMIN
# ============================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Course Reviews.
    
    Features:
    - View student reviews by course
    - Filter by rating
    - Search by student name and course title
    - Display review details with star rating
    """
    
    list_display = ['user', 'course', 'star_rating', 'comment_preview', 'created_at']
    list_filter = ['rating', 'created_at', 'course']
    search_fields = ['user__username', 'course__title', 'comment']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'course', 'rating', 'comment')
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def star_rating(self, obj):
        """Display rating as stars."""
        stars =  obj.rating
        return format_html('{} ({})', stars, obj.rating)
    star_rating.short_description = 'Rating'
    
    def comment_preview(self, obj):
        """Show truncated comment."""
        return obj.comment[:60] + '...' if len(obj.comment) > 60 else obj.comment
    comment_preview.short_description = 'Comment'
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by and updated_by."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# ASSESSMENT ADMIN
# ============================================================

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Assessment/Quiz management.
    
    Features:
    - Create assessments per course
    - Manage passing criteria
    - Publish/unpublish assessments
    - Inline question management
    - View attempt statistics
    """
    
    list_display = ['title', 'course', 'question_count', 'pass_mark', 'publication_status', 'attempt_count', 'created_at']
    list_filter = ['is_published', 'course', 'created_at']
    search_fields = ['title', 'description', 'course__title']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Assessment Information', {
            'fields': ('course', 'title', 'description')
        }),
        ('Assessment Settings', {
            'fields': ('pass_mark', 'is_published'),
            'description': 'Set passing percentage and publish when ready'
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [QuestionInline]
    
    def question_count(self, obj):
        """Show number of questions in assessment."""
        return obj.questions.count()
    question_count.short_description = 'Questions'
    
    def publication_status(self, obj):
        """Display publication status."""
        if obj.is_published:
            return format_html(
                '<span style="background-color: #90EE90; padding: 5px 10px; border-radius: 3px;">Published</span>'
            )
        return format_html(
            '<span style="background-color: #CCCCCC; padding: 5px 10px; border-radius: 3px;">Draft</span>'
        )
    publication_status.short_description = 'Status'
    
    def attempt_count(self, obj):
        """Show number of attempts."""
        return obj.attempts.count()
    attempt_count.short_description = 'Attempts'
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by and updated_by."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# QUESTION ADMIN
# ============================================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Admin interface for Assessment Questions.
    
    Features:
    - View questions by assessment
    - Manage question order/sequence
    - Inline choice management
    - Question type selection
    """
    
    list_display = ['text_preview', 'assessment', 'question_type', 'order', 'choice_count']
    list_filter = ['assessment', 'question_type', 'created_at']
    search_fields = ['text', 'assessment__title']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    ordering = ['assessment', 'order']
    
    fieldsets = (
        ('Question Information', {
            'fields': ('assessment', 'text', 'question_type', 'order')
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ChoiceInline]
    
    def text_preview(self, obj):
        """Show truncated question text."""
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_preview.short_description = 'Question'
    
    def choice_count(self, obj):
        """Show number of answer choices."""
        return obj.choices.count()
    choice_count.short_description = 'Choices'
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by and updated_by."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)



# ============================================================
# Activity ADMIN
# ============================================================
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "action",
        "target_type",
        "target_name",
        "created_at",
    )
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("target_name", "user__username")
    ordering = ("-created_at",)



# ============================================================
# CHOICE ADMIN
# ============================================================
@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    """
    Admin interface for Question Choices.
    
    Features:
    - View answer choices by question
    - Mark correct answer
    - Search by choice text and question
    """
    
    list_display = ['text', 'question_text', 'assessment_title', 'is_correct_badge', 'created_at']
    list_filter = ['is_correct', 'created_at', 'question__assessment']
    search_fields = ['text', 'question__text', 'question__assessment__title']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Choice Information', {
            'fields': ('question', 'text', 'is_correct'),
            'description': 'Mark the correct answer with is_correct checkbox'
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def question_text(self, obj):
        """Show associated question."""
        return obj.question.text[:50] + '...' if len(obj.question.text) > 50 else obj.question.text
    question_text.short_description = 'Question'
    
    def assessment_title(self, obj):
        """Show assessment for easier navigation."""
        return obj.question.assessment.title
    assessment_title.short_description = 'Assessment'
    
    def is_correct_badge(self, obj):
        """Display correct answer indicator."""
        if obj.is_correct:
            return format_html(
                '<span style="background-color: #90EE90; padding: 5px 10px; border-radius: 3px;">✓ Correct</span>'
            )
        return format_html(
            '<span style="background-color: #FFD700; padding: 5px 10px; border-radius: 3px;">Incorrect</span>'
        )
    is_correct_badge.short_description = 'Answer'
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by and updated_by."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# ASSESSMENT ATTEMPT ADMIN
# ============================================================

@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    """
    Admin interface for tracking student assessment attempts.
    
    Features:
    - View student attempts and scores
    - Filter by pass/fail status
    - Search by student and assessment
    - Show completion timestamps
    - Inline answer review
    """
    
    list_display = ['user', 'assessment', 'score_percentage', 'pass_status', 'completed_at', 'created_at']
    list_filter = ['passed', 'completed_at', 'assessment', 'created_at']
    search_fields = ['user__username', 'assessment__title']
    readonly_fields = ['created_at', 'score', 'passed']
    ordering = ['-completed_at']
    
    fieldsets = (
        ('Attempt Information', {
            'fields': ('user', 'assessment', 'completed_at')
        }),
        ('Results', {
            'fields': ('score', 'passed'),
            'description': 'Auto-calculated based on answers'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    inlines = [AnswerInline]
    
    def score_percentage(self, obj):
        """Display score as percentage with color."""
        pass_mark = obj.assessment.pass_mark
        color = '#90EE90' if obj.score >= pass_mark else '#FF6B6B'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            obj.score
        )
    score_percentage.short_description = 'Score'
    
    def pass_status(self, obj):
        """Display pass/fail status."""
        if obj.passed:
            return format_html(
                '<span style="background-color: #90EE90; padding: 5px 10px; border-radius: 3px;">✓ Passed</span>'
            )
        return format_html(
            '<span style="background-color: #FF6B6B; padding: 5px 10px; border-radius: 3px;">✗ Failed</span>'
        )
    pass_status.short_description = 'Status'


# ============================================================
# ANSWER ADMIN
# ============================================================

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """
    Admin interface for individual student answers.
    
    Features:
    - Review student answers per assessment attempt
    - View correct vs selected choices
    - Filter by attempt and correctness
    - Search by student and question
    """
    
    list_display = ['student_name', 'question_text', 'selected_choice', 'correctness_indicator', 'attempt_assessment']
    list_filter = ['attempt__user', 'attempt__assessment', 'created_at']
    search_fields = ['attempt__user__username', 'question__text']
    readonly_fields = ['attempt', 'question', 'selected_choice', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Answer Information', {
            'fields': ('attempt', 'question', 'selected_choice')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def student_name(self, obj):
        """Display student name."""
        return obj.attempt.user.get_full_name() or obj.attempt.user.username
    student_name.short_description = 'Student'
    
    def question_text(self, obj):
        """Show question text truncated."""
        return obj.question.text[:50] + '...' if len(obj.question.text) > 50 else obj.question.text
    question_text.short_description = 'Question'
    
    def correctness_indicator(self, obj):
        """Display if answer is correct."""
        if obj.selected_choice.is_correct:
            return format_html(
                '<span style="background-color: #90EE90; padding: 5px 10px; border-radius: 3px;">✓ Correct</span>'
            )
        return format_html(
            '<span style="background-color: #FF6B6B; padding: 5px 10px; border-radius: 3px;">✗ Incorrect</span>'
        )
    correctness_indicator.short_description = 'Correctness'
    
    def attempt_assessment(self, obj):
        """Show assessment title."""
        return obj.attempt.assessment.title
    attempt_assessment.short_description = 'Assessment'
