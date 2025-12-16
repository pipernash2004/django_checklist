from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.core.exceptions import ValidationError



# ------------------------------------------------------
# ABSTRACT MODELS
# ------------------------------------------------------

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserStampedModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_%(class)s"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="updated_%(class)s"
    )

    class Meta:
        abstract = True


# ------------------------------------------------------
# COURSE + LESSON STRUCTURE
# ------------------------------------------------------

class Course(UserStampedModel, TimeStampedModel):
    COURSE_TYPE_CHOICES = [
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('audio', 'Audio'),
        ('mixed', 'Mixed'),
    ]

    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_administered'
    )

    title = models.CharField(max_length=255)
    description = models.TextField()

    course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES)
    cover_image = models.ImageField(upload_to='course_covers/', null=True, blank=True)

    skills = models.JSONField(default=list, help_text='Skills taught in this course')
    requirements = models.JSONField(default=list, help_text='Prerequisites for this course')
    outcomes = models.JSONField(default=list, help_text='Learning outcomes of this course')

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    category = models.CharField(max_length=100)

    duration = models.PositiveIntegerField(help_text='Total duration in minutes')

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']
        

    def __str__(self):
        return self.title

    # ----------------------------
    # MODEL VALIDATION
    # ----------------------------
    def clean(self):
        super().clean()
        for field_name in ['skills', 'requirements']:
            value = getattr(self, field_name)
            if not isinstance(value, list):
                raise ValidationError({field_name: "Must be a list of strings."})
            if not all(isinstance(item, str) for item in value):
                raise ValidationError({field_name: "All items must be strings."})
            if len(value) > 50:  # Optional: maximum 50 skills/requirements
                raise ValidationError({field_name: "Cannot have more than 50 items."})




class Lesson(UserStampedModel, TimeStampedModel):
    LESSON_TYPE_CHOICES = [
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('audio', 'Audio'),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons'
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES)

    content_url = models.URLField()
    order = models.PositiveIntegerField()
    duration = models.PositiveIntegerField(help_text='Duration in minutes')

    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# ------------------------------------------------------
# ENROLLMENT + PROGRESS
# ------------------------------------------------------

class Enrollment(UserStampedModel, TimeStampedModel):
    crew_member = models.ForeignKey(
       settings.AUTH_USER_MODEL ,    on_delete=models.CASCADE,
        related_name='course_enrollments'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    overall_progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        unique_together = ['crew_member', 'course']

    def __str__(self):
        
        user = self.crew_member.username if self.crew_member else "No Type"
        return f"{user} enrolled in {self.course.title}"


class LessonProgress(TimeStampedModel):
    crew_member = models.ForeignKey(
        settings.AUTH_USER_MODEL   ,    on_delete=models.CASCADE,
         related_name='lesson_progress'
    )

    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='lesson_progress'
    )
    

    class Meta:
        verbose_name = 'Lesson Progress'
        verbose_name_plural = 'Lesson Progress'
        unique_together = ['crew_member', 'lesson']

    def __str__(self):
        return f"{self.crew_member.name} - {self.lesson.title}"




# ------------------------------------------------------
# REVIEW + ACHIEVEMENTS
# ------------------------------------------------------

class Review(TimeStampedModel):
    crew_member = models.ForeignKey(
        settings.AUTH_USER_MODEL   ,
        on_delete=models.CASCADE,
        related_name='course_reviews'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    comment = models.TextField()
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['crew_member', 'course']

    def __str__(self):
        return f"{self.crew_member.name} - {self.course.title}"


class Achievement(TimeStampedModel):
    crew_member = models.ForeignKey(
       settings.AUTH_USER_MODEL   ,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    icon = models.ImageField(upload_to='achievement_icons/', null=True, blank=True)

    class Meta:
        verbose_name = 'Achievement'
        verbose_name_plural = 'Achievements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.crew_member.name} - {self.title}"

        
        