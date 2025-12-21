from rest_framework.routers import DefaultRouter
from .views import SystemLogsViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'system-log', SystemLogsViewSet, basename='system-logs')

urlpatterns = [
    path('', include(router.urls)),
]
