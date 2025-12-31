from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


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

# course model 

class Course(UserStampedModel,TimeStampedModel):
    LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
    ]
    PAID_CHOICES = [
        ('free', 'Free'),
        ('paid', 'Paid'),
      
    ]
    CONTENT_TYPES = [
        ('course', 'Course'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('article', 'Article'),
        ('book', 'Book'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    title = models.CharField(max_length=255)
    skills = models.JSONField(default=list, help_text='Skills taught in this course')
    requirements = models.JSONField(default=list, help_text='Prerequisites for this course')
    outcomes = models.JSONField(default=list, help_text='Learning outcomes of this course')
  
    description = models.TextField(blank=True)
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="beginner"
    )
    course_type = models.CharField(max_length=20, choices=PAID_CHOICES)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    duration_weeks = models.PositiveIntegerField(default=1)
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='instructed_courses')
    thumbnail = models.ImageField(
        upload_to="course_thumbnails/",
    blank=True,
    null=True
)
  

    def __str__(self):
        return self.title

# lesson model

class Lesson(TimeStampedModel,UserStampedModel):
    course = models.ForeignKey(
        Course,
        related_name="lessons",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.CharField(max_length= 255)
    order = models.PositiveIntegerField()
    content_url = models.URLField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=5)
    

    class Meta:
        ordering = ["order"]
        unique_together = ("course", "order")

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# continue learning process

class Enrollment(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user} → {self.course}"
    


class LessonProgress(TimeStampedModel):
    """
    Tracks the progress of a user in a specific lesson. 
    Designed to handle different lesson types: video links, articles, pdfs
    """
    user = models.ForeignKey(Enrollment.course.user, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_value = models.FloatField(default=0.0, help_text="Progress percentage (0.0 to 100.0)")
    session_data  = models.JSONField(default=dict, help_text="Stores optional metadata like video seconds watched, PDF time spent, scroll %")

    class Meta:
        unique_together = ("user", "lesson")
        ordering = ["lesson"]
    def __str__(self):
        return f"{self.user} - {self.lesson.title} - {'Completed' if self.is_completed else 'In Progress'})"
    

    def mark_completed(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
    

    def update_progress(self, progress_value: float, session_data: dict = None):
        """
        Updates progress for measurable lessons (e.g., videos).
        If progress reaches 100%, mark lesson as completed.
        """
        self.progress_value = min(max(progress_value, 0), 100)  # Ensure 0-100%  
        if session_data:
            self.session_data = session_data

        if self.progress_value >= 100:
            self.mark_completed()
        else:
            self.save()

class Review(TimeStampedModel,UserStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course,
        related_name="reviews",
        on_delete=models.CASCADE
    )
    rating = models.PositiveSmallIntegerField()  # 1–5
    comment = models.TextField(blank=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.course} - {self.rating}"
    

class Assessment(UserStampedModel,TimeStampedModel):
        course = models.ForeignKey(
            Course,
            related_name="assessments",
            on_delete=models.CASCADE
        )
        title = models.CharField(max_length=255)
        description = models.TextField(blank=True)
        pass_mark = models.PositiveIntegerField(default=50)  # %
        is_published = models.BooleanField(default=False)

        def __str__(self):
            return f"{self.course.title} - {self.title}"
        

class AssessmentAttempt(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    assessment = models.ForeignKey(
        Assessment,
        related_name="attempts",
        on_delete=models.CASCADE
    )
    score = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
       

    class Meta:
        unique_together = ("user", "assessment")

    def __str__(self):
        return f"{self.user} - {self.assessment}"
        
class Question(UserStampedModel,TimeStampedModel):
    QUESTION_TYPE_CHOICES = [
        ("mcq", "Multiple Choice"),
    ]

    assessment = models.ForeignKey(
        Assessment,
        related_name="questions",
        on_delete=models.CASCADE
    )
    text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default="mcq"
    )
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text[:50]

class Choice(UserStampedModel,TimeStampedModel):
    question = models.ForeignKey(
        Question,
        related_name="choices",
        on_delete=models.CASCADE
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text
    
class Answer(TimeStampedModel):
    attempt = models.ForeignKey(
        AssessmentAttempt,
        related_name="answers",
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )


    
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("attempt", "question")



class ActivityLog(UserStampedModel, TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities"
    )

    action = models.CharField(
        max_length=50,
        choices=(
            ("enrolled", "Enrolled"),
            ("completed", "Completed"),
            ("submitted_review", "Submitted Review"),
            ("uploaded", "Uploaded"),
            ("created", "Created"),
        )
    )

    
    target_type = models.CharField(
        max_length=100,
        help_text="Model name of the target (e.g. Course, Lesson, Assessment)"
    )

    target_id = models.PositiveIntegerField(
        help_text="Primary key of the target object"
    )

    target_name = models.CharField(
        max_length=255,
        help_text="Human-readable name for fast display"
    )



    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["action"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self):
        return f"{self.user} {self.action} {self.target_name}"
