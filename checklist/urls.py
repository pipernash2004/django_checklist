"""
URL Configuration for checklist app.
Registers all ViewSets with DefaultRouter for automatic CRUD endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RoleViewSet,
    ChecklistTypeViewSet,
    ChecklistViewSet,
    SectionViewSet,
    ListItemViewSet,
    ChecklistProgressViewSet,
)

# Initialize router
router = DefaultRouter()

# Register viewsets
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'checklist-types', ChecklistTypeViewSet, basename='checklist-type')
router.register(r'checklists', ChecklistViewSet, basename='checklist')
router.register(r'sections', SectionViewSet, basename='section')
router.register(r'list-items', ListItemViewSet, basename='list-item')
router.register(r'progress', ChecklistProgressViewSet, basename='checklist-progress')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]