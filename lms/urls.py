from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    LessonViewSet,
    AssessmentViewSet,
    QuestionViewSet,
    ChoiceViewSet,
    EnrollmentViewSet,
    ReviewViewSet,    
    LessonProgressViewSet,
)

# Create a DRF router
router = DefaultRouter()

# Register all viewsets
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'assessments', AssessmentViewSet, basename='assessment')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'choices', ChoiceViewSet, basename='choice')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'lessonprogress',  LessonProgressViewSet, basename='lesson-progress')



# URL patterns
urlpatterns = [
    path("", include(router.urls)),
]

