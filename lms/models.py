# from django.db import models

# # Create your models here.
# from django.db import models
# from django.conf import settings
# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _
# from django.core.validators import MinValueValidator, MaxValueValidator


# #  course model
# #  enrollment model
# #  lesson model
# #  Priview model
# #  Badges model
# #  LessonProgress model
# # Assessment model


# class TimeStampedModel(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         abstract = True


# class UserStampedModel(models.Model):
#     created_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         related_name="created_%(class)s"
#     )
#     updated_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         related_name="updated_%(class)s"
#     )

#     class Meta:
#         abstract = True



# class Course(UserStampedModel, TimeStampedModel):
#     COURSE_TYPE_CHOICES = [
#         ('video', 'Video'),
#         ('pdf', 'PDF'),
#         ('audio', 'Audio'),
#         ('mixed', 'Mixed'),
#     ]

#     LEVEL_CHOICES = [
#         ('beginner', 'Beginner'),
#         ('intermediate', 'Intermediate'),
#         ('advanced', 'Advanced'),
#     ]

#     instructor = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='courses_administered'
#     )

#     title = models.CharField(max_length=255)
#     description = models.TextField()

#     course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES)
#     cover_image = models.ImageField(upload_to='course_covers/', null=True, blank=True)

#     skills = models.JSONField(default=list, help_text='Skills taught in this course')
#     requirements = models.JSONField(default=list, help_text='Prerequisites for this course')

#     level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
#     category = models.CharField(max_length=100)

#     duration = models.PositiveIntegerField(help_text='Total duration in minutes')

#     class Meta:
#         verbose_name = 'Course'
#         verbose_name_plural = 'Courses'
#         ordering = ['-created_at']

#     def __str__(self):
#         return self.title


# class Lesson(UserStampedModel, TimeStampedModel):
#     LESSON_TYPE_CHOICES = [
#         ('video', 'Video'),
#         ('pdf', 'PDF'),
#         ('audio', 'Audio'),
#     ]

#     course = models.ForeignKey(
#         Course,
#         on_delete=models.CASCADE,
#         related_name='lessons'
#     )

#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     lesson_type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES)

#     content_url = models.URLField()
#     order = models.PositiveIntegerField()
#     duration = models.IntegerField(help_text='Duration in minutes')

#     class Meta:
#         verbose_name = 'Lesson'
#         verbose_name_plural = 'Lessons'
#         ordering = ['course', 'order']
#         unique_together = ['course', 'order']

#     def __str__(self):
#         return f"{self.course.title} - {self.title}"


# class Enrollment(UserStampedModel, TimeStampedModel):
#     crew_member = models.ForeignKey(
#        settings.AUTH_USER_MODEL,    on_delete=models.CASCADE,
#         related_name='course_enrollments'
#     )

#     course = models.ForeignKey(
#         Course,
#         on_delete=models.CASCADE,
#         related_name='enrollments'
#     )

#     started_at = models.DateTimeField(auto_now_add=True)
#     completed_at = models.DateTimeField(null=True, blank=True)

#     overall_progress = models.IntegerField(
#         default=0,
#         validators=[MinValueValidator(0), MaxValueValidator(100)]
#     )

#     class Meta:
#         verbose_name = 'Enrollment'
#         verbose_name_plural = 'Enrollments'
#         unique_together = ['crew_member', 'course']

#     def __str__(self):
#         return f"{self.crew_member} enrolled in {self.course.title}"


# class LessonProgress(TimeStampedModel):
#     crew_member = models.ForeignKey(
#         settings.AUTH_USER_MODEL  ,    on_delete=models.CASCADE,
#          related_name='lesson_progress'
#     )

    
#     lesson = models.ForeignKey(
#         Lesson,
#         on_delete=models.CASCADE,
#         related_name='lesson_progress'
#     )
    

#     class Meta:
#         verbose_name = 'Lesson Progress'
#         verbose_name_plural = 'Lesson Progress'
#         unique_together = ['crew_member', 'lesson']

#     def __str__(self):
#         return f"{self.crew_member} - {self.lesson.title}"

