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
                raise ValidationError({field_name: "Must be a list of string."})
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
    duration = models.IntegerField(help_text='Duration in minutes')

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
       settings.AUTH_USER_MODEL,    on_delete=models.CASCADE,
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
        return f"{self.crew_member} enrolled in {self.course.title}"


class LessonProgress(TimeStampedModel):
    crew_member = models.ForeignKey(
        settings.AUTH_USER_MODEL  ,    on_delete=models.CASCADE,
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
        return f"{self.crew_member} - {self.lesson.title}"




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

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['crew_member', 'course']

    def __str__(self):
        return f"{self.crew_member} - {self.course.title}"

   
class Achievement(TimeStampedModel):
    crew_member = models.ForeignKey(
        settings.AUTH_USER_MODEL
              ,
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
        return f"{self.crew_member} - {self.title}"


class Assessment(UserStampedModel, TimeStampedModel):

    title = models.CharField(max_length=255)
    lesson = models.ForeignKey(Lesson , on_delete =models.CASCADE, related_name = "assessments")
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
                raise ValidationError({field_name: "Must be a list of string."})
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
    duration = models.IntegerField(help_text='Duration in minutes')

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
       settings.AUTH_USER_MODEL,    on_delete=models.CASCADE,
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
        return f"{self.crew_member} enrolled in {self.course.title}"


class LessonProgress(TimeStampedModel):
    crew_member = models.ForeignKey(
        settings.AUTH_USER_MODEL  ,    on_delete=models.CASCADE,
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
        return f"{self.crew_member} - {self.lesson.title}"




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

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['crew_member', 'course']

    def __str__(self):
        return f"{self.crew_member} - {self.course.title}"

   
class Achievement(TimeStampedModel):
    crew_member = models.ForeignKey(
        settings.AUTH_USER_MODEL
              ,
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
        return f"{self.crew_member} - {self.title}"


class Assessment(UserStampedModel, TimeStampedModel):

    title = models.CharField(max_length=255)
    lesson = models.ForeignKey(Lesson , on_delete =models.CASCADE, related_name = "assessments")

    passing_score = models.IntegerField(
    default=70,
    validators=[MinValueValidator(0), MaxValueValidator(100)])

    time_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Time limit in minutes (null = no limit)')
    
    ramdomize_questions = models.BooleanField(
        default= True
    )
    is_active = models.BooleanField(default= True)

    class Meta:
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'
        ordering = ['lesson', 'created_at']

      

        indexes = [
            models.Index(fields=['lesson', 'is_active'])
        ]

    pass

class Question(UserStampedModel, TimeStampedModel):
    """Individual question within an assessment"""
    
    
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='questions',
        db_index=True
    )
    
    question_type = models.CharField(
        max_length=10
    )
    
    question_text = models.TextField()
    
    # For MCQ 
    choices = models.JSONField(
        default=list,
        blank=True,
        help_text='List of answer choices for MCQ: [{"id": "a", "text": "Answer A"}, ...]'
    )
    
    correct_answer = models.CharField(
        max_length=255,
        help_text='Correct answer (choice ID for MCQ, text for short answer)'
    )
    
  
    
    points = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['assessment', 'order']
        unique_together = ['assessment', 'order']
        indexes = [
            models.Index(fields=['assessment', 'order']),
        ]
    
    def __str__(self):
        return f"{self.assessment.title} - Q{self.order}"

    


class Attempt(UserStampedModel, TimeStampedModel):
    """Student's attempt at an assessment"""
    
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        SUBMITTED = 'submitted', 'Submitted'
        GRADED = 'graded', 'Graded'
    
    crew_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessment_attempts',
        db_index=True
    )
    
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='attempts',
        db_index=True
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS
    )
    
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Scoring
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    points_earned = models.PositiveIntegerField(default=0)
    total_points = models.PositiveIntegerField(default=0)
    
    passed = models.BooleanField(default=False)
    
    # Track attempt number
    attempt_number = models.PositiveIntegerField(default=1)
    
    class Meta:
        verbose_name = 'Attempt'
        verbose_name_plural = 'Attempts'
        ordering = ['-started_at']
        unique_together = ['crew_member', 'assessment', 'attempt_number']
        indexes = [
            models.Index(fields=['crew_member', 'assessment']),
            models.Index(fields=['status', 'submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.crew_member} - {self.assessment.title} (Attempt {self.attempt_number})"

class Answer(TimeStampedModel):
    """Individual answer within an attempt"""
    
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name='answers',
        db_index=True
    )
    
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    
    answer_text = models.TextField(
        help_text='Student\'s answer (choice ID for MCQ, text for others)'
    )
    
    is_correct = models.BooleanField(default=False)
    
    # For manual grading
    points_awarded = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Points awarded (for essay/short answer)'
    )
    
    feedback = models.TextField(
        blank=True,
        help_text='Instructor feedback on this answer'
    )
    
    class Meta:
        verbose_name = 'Answer'
        verbose_name_plural = 'Answers'
        unique_together = ['attempt', 'question']
        indexes = [
            models.Index(fields=['attempt', 'question']),
        ]
    
    def __str__(self):
        return f"{self.attempt} - {self.question}"
    
    def save(self, *args, **kwargs):
        # Auto-grade MCQ 
        if self.question.question_type == 'mcq':
            self.is_correct = (
                self.answer_text.strip().lower() == 
                self.question.correct_answer.strip().lower()
            )
        super().save(*args, **kwargs)