import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.admin.models import LogEntry
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
# Assume the following imports are available in your project
from .serializers import LogEntrySerializer
from lms.management.StandardResultsSetPagination  import StandardResultsSetPagination  # Assuming this is defined similarly to the BookingViewSet

logger = logging.getLogger(__name__)

class SystemLogsViewSet(viewsets.ModelViewSet):
    queryset = LogEntry.objects.all().select_related('user', 'content_type')
    serializer_class = LogEntrySerializer
    ordering_fields = '__all__'
    ordering = ['-action_time']
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['change_message', 'object_repr', 'user__email']
    filterset_fields = ['user', 'action_flag', 'content_type']

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Assuming CustomUser has a 'role' field as per the user form data
        if user.role != 'Admin':
            logger.warning(f"User {user} lacks permission to access system logs")
            return LogEntry.objects.none()

        try:
            user_company = user.company
            if user_company:
                logger.debug(f"Filtering system logs for user {user} with company {user_company}")
                # Filter logs by users in the same company (assuming CustomUser has 'company' field)
                queryset = queryset.filter(user__company=user_company)
            else:
                logger.debug(f"User {user} has no company, fetching all system logs")
        except AttributeError:
            logger.error(f"User model {user} does not have a 'company' attribute")
            return LogEntry.objects.none()

        return queryset