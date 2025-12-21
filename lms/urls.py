# ============================================================
# LEARNING MANAGEMENT SYSTEM - URL CONFIGURATION
# ============================================================
# This module configures URL routing for all LMS API endpoints.
# 
# API Endpoints Generated:
# 
# COURSES (with nested lessons & assessments):
# - GET    /api/courses/                    - List all courses
# - POST   /api/courses/                    - Create new course (with nested content)
# - GET    /api/courses/{id}/               - Retrieve course detail
# - PUT    /api/courses/{id}/               - Full update (replace all nested)
# - PATCH  /api/courses/{id}/               - Partial update (selective updates)
# - DELETE /api/courses/{id}/               - Delete course
# 
# LESSONS:
# - GET    /api/lessons/                    - List all lessons
# - POST   /api/lessons/                    - Create new lesson
# - GET    /api/lessons/{id}/               - Retrieve lesson detail
# - PUT    /api/lessons/{id}/               - Full update
# - PATCH  /api/lessons/{id}/               - Partial update
# - DELETE /api/lessons/{id}/               - Delete lesson
# 
# ASSESSMENTS (with nested questions & choices):
# - GET    /api/assessments/                - List all assessments
# - POST   /api/assessments/                - Create new assessment
# - GET    /api/assessments/{id}/           - Retrieve assessment detail
# - PUT    /api/assessments/{id}/           - Full update
# - PATCH  /api/assessments/{id}/           - Partial update
# - DELETE /api/assessments/{id}/           - Delete assessment
# 
# ============================================================

# Third-party imports
from rest_framework.routers import DefaultRouter

# Local imports
from .views import CourseViewSet, LessonViewSet, AssessmentViewSet

# ============================================================
# ROUTER CONFIGURATION
# ============================================================

# Create DefaultRouter instance
# DefaultRouter provides both:
# - API endpoint listing at /api/
# - Browsable API interface for testing
router = DefaultRouter()

# Register viewsets with router
# This automatically generates all CRUD endpoints and custom actions
router.register(
    prefix='courses',
    viewset=CourseViewSet,
    basename='course'
)
router.register(
    prefix='lessons',
    viewset=LessonViewSet,
    basename='lesson'
)
router.register(
    prefix='assessments',
    viewset=AssessmentViewSet,
    basename='assessment'
)

# ============================================================
# URL PATTERNS
# ============================================================

# Export router URLs
# These will be included in the main Django project urls.py as:
# path('api/', include('lms.urls'))
urlpatterns = router.urls
