from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'lessons', views.LessonViewSet, basename='lesson')
router.register(r'enrollments', views.EnrollmentViewSet, basename='enrollment')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'achievements', views.AchievementViewSet, basename='achievement')
router.register(r'dashboard', views.DashboardViewSet, basename='dashboard')



urlpatterns = [
    path('', include(router.urls)),
]
