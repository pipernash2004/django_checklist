from django.contrib import admin
from .models import Course, Lesson, Enrollment, LessonProgress, Review, Achievement


# ============================================================
# COURSE ADMIN
# ============================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'level', 'category', 'course_type', 'duration', 'created_at']
    list_filter = ['level', 'category', 'course_type', 'created_at']
    search_fields = ['title', 'description', 'instructor__username']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Course Information', {
            'fields': ('title', 'description', 'instructor', 'course_type')
        }),
        ('Metadata', {
            'fields': ('level', 'category', 'duration', 'cover_image')
        }),
        ('Learning Content', {
            'fields': ('skills', 'requirements')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by/updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# LESSON ADMIN
# ============================================================

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'lesson_type', 'duration', 'created_at']
    list_filter = ['course', 'lesson_type', 'created_at']
    search_fields = ['title', 'description', 'course__title']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Lesson Information', {
            'fields': ('course', 'title', 'description', 'order')
        }),
        ('Content', {
            'fields': ('lesson_type', 'content_url', 'duration')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by/updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# ENROLLMENT ADMIN
# ============================================================

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['crew_member', 'course', 'overall_progress', 'started_at', 'completed_at']
    list_filter = ['course', 'started_at', 'completed_at']
    search_fields = ['crew_member__name', 'course__title']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'started_at']
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('crew_member', 'course', 'overall_progress')
        }),
        ('Timeline', {
            'fields': ('started_at', 'completed_at')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by/updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# LESSON PROGRESS ADMIN
# ============================================================

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['crew_member', 'lesson', 'course_name', 'created_at']
    list_filter = ['lesson__course', 'created_at']
    search_fields = ['crew_member__name', 'lesson__title', 'lesson__course__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Progress Information', {
            'fields': ('crew_member', 'lesson')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def course_name(self, obj):
        """Display course name for easier navigation."""
        return obj.lesson.course.title
    course_name.short_description = 'Course'


# ============================================================
# REVIEW ADMIN
# ============================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['crew_member', 'course', 'rating', 'created_at']
    list_filter = ['course', 'rating', 'created_at']
    search_fields = ['crew_member__name', 'course__title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('crew_member', 'course', 'rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================
# ACHIEVEMENT ADMIN
# ============================================================

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'crew_member', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description', 'crew_member__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Achievement Information', {
            'fields': ('crew_member', 'title', 'description', 'icon')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
