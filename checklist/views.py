"""
DRF ViewSets for checklist app with authentication, permissions, and comprehensive logging.
Follows REST best practices and includes custom actions with detailed documentation.
"""

import logging
from django.db import transaction
from django.db.models import Q, Count, Prefetch
from django.utils import timezone

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Role, ChecklistType, Checklist, Sections, ListItem, ChecklistProgress
from .serializers import (
    RoleListSerializer, RoleDetailSerializer, RoleCreateUpdateSerializer,
    ChecklistTypeListSerializer, ChecklistTypeDetailSerializer, ChecklistTypeCreateUpdateSerializer,
    ChecklistListSerializer, ChecklistDetailSerializer, ChecklistCreateUpdateSerializer, ChecklistCompositeSerializer,
    SectionBasicSerializer, SectionDetailSerializer, SectionCreateUpdateSerializer,
    ListItemBasicSerializer, ListItemDetailSerializer, ListItemCreateUpdateSerializer,
    ChecklistProgressListSerializer, ChecklistProgressDetailSerializer, 
    ChecklistProgressCreateUpdateSerializer, ChecklistProgressStatsSerializer,
    ChecklistStatsSerializer, UserProgressSummarySerializer
)
from .services import (
    RoleService, ChecklistTypeService, ChecklistService,
    SectionService, ListItemService, ChecklistProgressService
)

logger = logging.getLogger(__name__)


# ============================================================
# PERMISSION CLASSES
# ============================================================

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Allow read access to anyone.
    Only staff users can write/modify data.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsCreatorOrStaff(permissions.BasePermission):
    """
    Allow creators and staff to modify objects.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            hasattr(obj, 'created_by') and obj.created_by == request.user
        ) or request.user.is_staff


# ============================================================
# ROLE VIEWSET
# ============================================================

class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing roles.
    
    Permissions:
    - list, retrieve: Authenticated users
    - create, update, destroy: Staff only
    
    Actions:
    - list: Get all roles with optional filtering
    - retrieve: Get specific role details
    - create: Create new role (staff only)
    - update/partial_update: Update role (staff only)
    - destroy: Delete role (staff only)
    - checklists: Get checklists using this role
    """
    queryset = Role.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    pagination_class = None

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return RoleDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RoleCreateUpdateSerializer
        return RoleListSerializer

    def get_queryset(self):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.select_related('created_by', 'last_updated_by')
        return queryset

    def perform_create(self, serializer):
        """Create role with current user as creator."""
        try:
            logger.debug(f"User {self.request.user.id} creating role")
            role = serializer.save()
            RoleService.create_role(self.request.user, role.name, role.description)
            logger.info(f"Role created: {role.name} by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error creating role: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
        """Update role with current user as updater."""
        try:
            logger.debug(f"User {self.request.user.id} updating role")
            role = serializer.save()
            logger.info(f"Role {role.id} updated by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error updating role: {str(e)}", exc_info=True)
            raise

    def perform_destroy(self, instance):
        """Delete role."""
        try:
            logger.debug(f"User {self.request.user.id} deleting role {instance.id}")
            RoleService.delete_role(instance.id)
            logger.info(f"Role {instance.id} deleted by user {self.request.user.id}")
        except ValidationError as e:
            logger.warning(f"Delete role validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error deleting role: {str(e)}", exc_info=True)
            raise

    def list(self, request, *args, **kwargs):
        """List all roles with optional search and filtering."""
        try:
            logger.debug(f"User {request.user.id} listing roles")
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            logger.info(f"Retrieved {len(queryset)} roles")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing roles: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to retrieve roles'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """Get role details."""
        try:
            instance = self.get_object()
            logger.debug(f"User {request.user.id} retrieving role {instance.id}")
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving role: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to retrieve role'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get all checklists using this role",
        responses={200: ChecklistListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def checklists(self, request, pk=None):
        """Get all checklists using this role."""
        try:
            role = self.get_object()
            logger.debug(f"User {request.user.id} retrieving checklists for role {role.id}")
            checklists = role.checklists_roles.all().order_by('-created_at')
            serializer = ChecklistListSerializer(checklists, many=True)
            logger.info(f"Retrieved {len(checklists)} checklists for role {role.id}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving checklists for role: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to retrieve checklists'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================
# CHECKLIST TYPE VIEWSET
# ============================================================

class ChecklistTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing checklist types.
    
    Permissions:
    - list, retrieve: Authenticated users
    - create, update, destroy: Staff only
    
    Actions:
    - list: Get all checklist types
    - retrieve: Get specific type details
    - create: Create new type (staff only)
    - update/partial_update: Update type (staff only)
    - destroy: Delete type (staff only)
    - stats: Get type statistics
    """
    queryset = ChecklistType.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    pagination_class = None

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ChecklistTypeDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ChecklistTypeCreateUpdateSerializer
        return ChecklistTypeListSerializer

    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('created_by', 'last_updated_by')

    def perform_create(self, serializer):
        """Create checklist type."""
        try:
            logger.debug(f"User {self.request.user.id} creating checklist type")
            ChecklistTypeService.create_checklist_type(
                self.request.user,
                serializer.validated_data['name'],
                serializer.validated_data.get('description')
            )
            logger.info(f"ChecklistType created: {serializer.validated_data['name']}")
        except Exception as e:
            logger.error(f"Error creating checklist type: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
        """Update checklist type."""
        try:
            logger.debug(f"User {self.request.user.id} updating checklist type")
            ChecklistTypeService.update_checklist_type(
                self.request.user,
                self.get_object().id,
                **serializer.validated_data
            )
            logger.info(f"ChecklistType updated by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error updating checklist type: {str(e)}", exc_info=True)
            raise

    def perform_destroy(self, instance):
        """Delete checklist type."""
        try:
            logger.debug(f"User {self.request.user.id} deleting checklist type {instance.id}")
            ChecklistTypeService.delete_checklist_type(instance.id)
            logger.info(f"ChecklistType deleted by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error deleting checklist type: {str(e)}", exc_info=True)
            raise

    @extend_schema(
        description="Get statistics for this checklist type",
        responses={200: ChecklistStatsSerializer()}
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def stats(self, request, pk=None):
        """Get checklist type statistics."""
        try:
            checklist_type = self.get_object()
            logger.debug(f"User {request.user.id} retrieving stats for checklist type {checklist_type.id}")
            stats_data = ChecklistTypeService.get_checklist_type_stats(checklist_type.id)
            serializer = ChecklistStatsSerializer(stats_data)
            logger.info(f"Retrieved stats for checklist type {checklist_type.id}")
            return Response(serializer.data)
        except ValidationError as e:
            logger.warning(f"Stats validation error: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error retrieving stats: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to retrieve statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================
# CHECKLIST VIEWSET
# ============================================================

class ChecklistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing checklists.
    
    Permissions:
    - list, retrieve: Authenticated users
    - create, update, destroy: Staff only
    
    Actions:
    - list: Get all checklists with filtering
    - retrieve: Get specific checklist
    - create: Create new checklist
    - update/partial_update: Update checklist
    - destroy: Delete checklist
    - sections: Get sections in checklist
    - stats: Get checklist statistics
    """
    queryset = Checklist.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'notes']
    filterset_fields = ['phase', 'checklist_type']
    ordering_fields = ['name', 'created_at', 'phase']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ChecklistDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            # Accept full nested payload for create/update
            return ChecklistCompositeSerializer
        return ChecklistListSerializer

    def get_queryset(self):
        """Optimize queryset with prefetching."""
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'sections',
                'roles',
                'checklist_progress'
            ).select_related('checklist_type', 'created_by', 'last_updated_by')
        elif self.action == 'list':
            queryset = queryset.select_related('checklist_type', 'created_by')
        return queryset

    def perform_create(self, serializer):
        """Create checklist."""
        try:
            logger.debug(f"User {self.request.user.id} creating checklist")
            # Composite serializer handles nested creation when used for create
            checklist = serializer.save()
            logger.info(f"Checklist created: {checklist.name} (id={checklist.id}) by user {self.request.user.id}")
        except ValidationError as e:
            logger.warning(f"Checklist creation validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating checklist: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
        """Update checklist."""
        try:
            logger.debug(f"User {self.request.user.id} updating checklist")
            instance = serializer.save()
            logger.info(f"Checklist {instance.id} updated by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error updating checklist: {str(e)}", exc_info=True)
            raise

    def perform_destroy(self, instance):
        """Delete checklist."""
        try:
            logger.debug(f"User {self.request.user.id} deleting checklist {instance.id}")
            ChecklistService.delete_checklist(instance.id)
            logger.info(f"Checklist deleted by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error deleting checklist: {str(e)}", exc_info=True)
            raise

    @extend_schema(
        description="Get all sections in this checklist",
        responses={200: SectionBasicSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def sections(self, request, pk=None):
        """Get all sections in this checklist."""
        try:
            checklist = self.get_object()
            logger.debug(f"User {request.user.id} retrieving sections for checklist {checklist.id}")
            sections = ChecklistService.get_checklist_sections(checklist.id)
            serializer = SectionBasicSerializer(sections, many=True)
            logger.info(f"Retrieved {len(sections)} sections for checklist {checklist.id}")
            return Response(serializer.data)
        except ValidationError as e:
            logger.warning(f"Sections retrieval error: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error retrieving sections: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to retrieve sections'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get statistics for this checklist",
        responses={200: ChecklistStatsSerializer()}
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def stats(self, request, pk=None):
        """Get checklist statistics."""
        try:
            checklist = self.get_object()
            logger.debug(f"User {request.user.id} retrieving stats for checklist {checklist.id}")
            stats_data = ChecklistService.get_checklist_stats(checklist.id)
            serializer = ChecklistStatsSerializer(stats_data)
            logger.info(f"Retrieved stats for checklist {checklist.id}")
            return Response(serializer.data)
        except ValidationError as e:
            logger.warning(f"Stats retrieval error: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error retrieving stats: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to retrieve statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================
# SECTION VIEWSET
# ============================================================

class SectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sections.
    
    Permissions:
    - list, retrieve: Authenticated users
    - create, update, destroy: Staff only
    
    Actions:
    - list: Get sections (filterable by checklist)
    - retrieve: Get section details
    - create: Create new section
    - update/partial_update: Update section
    - destroy: Delete section
    - items: Get list items in section
    """
    queryset = Sections.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['checklist', 'checklist_type']
    ordering_fields = ['order', 'created_at', 'name']
    ordering = ['order']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return SectionDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SectionCreateUpdateSerializer
        return SectionBasicSerializer

    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.select_related('checklist', 'checklist_type', 'created_by', 'last_updated_by')
        elif self.action == 'list':
            queryset = queryset.select_related('checklist', 'checklist_type')
        return queryset.order_by('order')

    def perform_create(self, serializer):
        """Create section."""
        try:
            logger.debug(f"User {self.request.user.id} creating section")
            data = serializer.validated_data
            SectionService.create_section(
                self.request.user,
                data['checklist_id'],
                data['name'],
                data.get('checklist_type_id'),
                data.get('order', 0),
                data.get('description')
            )
            logger.info(f"Section created: {data['name']} by user {self.request.user.id}")
        except ValidationError as e:
            logger.warning(f"Section creation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating section: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
        """Update section."""
        try:
            logger.debug(f"User {self.request.user.id} updating section")
            SectionService.update_section(
                self.request.user,
                self.get_object().id,
                **serializer.validated_data
            )
            logger.info(f"Section updated by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error updating section: {str(e)}", exc_info=True)
            raise

    def perform_destroy(self, instance):
        """Delete section."""
        try:
            logger.debug(f"User {self.request.user.id} deleting section {instance.id}")
            SectionService.delete_section(instance.id)
            logger.info(f"Section deleted by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error deleting section: {str(e)}", exc_info=True)
            raise

    @extend_schema(
        description="Get all list items in this section",
        responses={200: ListItemBasicSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def items(self, request, pk=None):
        """Get all list items in this section."""
        try:
            section = self.get_object()
            logger.debug(f"User {request.user.id} retrieving items for section {section.id}")
            items = SectionService.get_section_items(section.id)
            serializer = ListItemBasicSerializer(items, many=True)
            logger.info(f"Retrieved {len(items)} items for section {section.id}")
            return Response(serializer.data)
        except ValidationError as e:
            logger.warning(f"Items retrieval error: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error retrieving items: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to retrieve items'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================
# LIST ITEM VIEWSET
# ============================================================

class ListItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing list items.
    
    Permissions:
    - list, retrieve: Authenticated users
    - create, update, destroy: Staff only
    
    Actions:
    - list: Get list items (filterable by section)
    - retrieve: Get item details
    - create: Create new item
    - update/partial_update: Update item
    - destroy: Delete item
    """
    queryset = ListItem.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['section']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ListItemDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ListItemCreateUpdateSerializer
        return ListItemBasicSerializer

    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.select_related('section', 'created_by', 'last_updated_by')
        elif self.action == 'list':
            queryset = queryset.select_related('section')
        return queryset

    def perform_create(self, serializer):
        """Create list item."""
        try:
            logger.debug(f"User {self.request.user.id} creating list item")
            data = serializer.validated_data
            ListItemService.create_list_item(
                self.request.user,
                data['section_id'],
                data['name'],
                data.get('description')
            )
            logger.info(f"ListItem created: {data['name']} by user {self.request.user.id}")
        except ValidationError as e:
            logger.warning(f"ListItem creation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating list item: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
        """Update list item."""
        try:
            logger.debug(f"User {self.request.user.id} updating list item")
            ListItemService.update_list_item(
                self.request.user,
                self.get_object().id,
                **serializer.validated_data
            )
            logger.info(f"ListItem updated by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error updating list item: {str(e)}", exc_info=True)
            raise

    def perform_destroy(self, instance):
        """Delete list item."""
        try:
            logger.debug(f"User {self.request.user.id} deleting list item {instance.id}")
            ListItemService.delete_list_item(instance.id)
            logger.info(f"ListItem deleted by user {self.request.user.id}")
        except Exception as e:
            logger.error(f"Error deleting list item: {str(e)}", exc_info=True)
            raise


# ============================================================
# CHECKLIST PROGRESS VIEWSET
# ============================================================

class ChecklistProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing checklist progress.
    
    Permissions:
    - list, retrieve: Authenticated users
    - create, update: Authenticated users (own records)
    - destroy: Authenticated users (own records) or staff
    
    Actions:
    - list: Get progress records (filterable by checklist/user)
    - retrieve: Get progress details
    - create: Create progress record
    - update/partial_update: Update progress
    - destroy: Delete progress
    - my_progress: Get current user's progress
    - stats: Get progress statistics
    - summary: Get user's progress summary
    """
    queryset = ChecklistProgress.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['checklist', 'user', 'status']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ChecklistProgressDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ChecklistProgressCreateUpdateSerializer
        return ChecklistProgressListSerializer

    def get_queryset(self):
        """Filter based on permissions."""
        queryset = super().get_queryset()
        
        # Staff can see all, regular users see only their own
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        if self.action == 'retrieve':
            queryset = queryset.select_related('checklist', 'items', 'user')
        elif self.action == 'list':
            queryset = queryset.select_related('checklist', 'items', 'user')
        
        return queryset

    def perform_create(self, serializer):
        """Create progress record."""
        try:
            logger.debug(f"User {self.request.user.id} creating progress record")
            data = serializer.validated_data
            ChecklistProgressService.create_progress(
                self.request.user,
                data['checklist_id'],
                data.get('list_item_id'),
                data.get('status', 'pending')
            )
            logger.info(f"Progress created for checklist {data['checklist_id']} by user {self.request.user.id}")
        except ValidationError as e:
            logger.warning(f"Progress creation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating progress: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
        """Update progress record."""
        try:
            logger.debug(f"User {self.request.user.id} updating progress record")
            instance = self.get_object()
            
            # Check permission
            if instance.user != self.request.user and not self.request.user.is_staff:
                raise PermissionDenied("You can only update your own progress records.")
            
            ChecklistProgressService.update_progress_status(
                instance.id,
                serializer.validated_data.get('status', instance.status)
            )
            logger.info(f"Progress {instance.id} updated by user {self.request.user.id}")
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}", exc_info=True)
            raise

    def perform_destroy(self, instance):
        """Delete progress record."""
        try:
            if instance.user != self.request.user and not self.request.user.is_staff:
                raise PermissionDenied("You can only delete your own progress records.")
            
            logger.debug(f"User {self.request.user.id} deleting progress record {instance.id}")
            ChecklistProgressService.delete_progress(instance.id)
            logger.info(f"Progress deleted by user {self.request.user.id}")
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Error deleting progress: {str(e)}", exc_info=True)
            raise

    @extend_schema(
        description="Get current user's progress records",
        responses={200: ChecklistProgressListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_progress(self, request):
        """Get current user's progress records."""
        try:
            logger.debug(f"User {request.user.id} retrieving own progress")
            progress = ChecklistProgressService.get_user_all_progress(request.user.id)
            serializer = self.get_serializer(progress, many=True)
            logger.info(f"Retrieved {len(progress)} progress records for user {request.user.id}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving user progress: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to retrieve progress'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get progress statistics for a checklist",
        responses={200: ChecklistProgressStatsSerializer()}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def stats(self, request):
        """Get progress statistics."""
        try:
            checklist_id = request.query_params.get('checklist_id')
            if not checklist_id:
                return Response(
                    {'detail': 'checklist_id query parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.debug(f"User {request.user.id} retrieving stats for checklist {checklist_id}")
            stats_data = ChecklistProgressService.get_checklist_progress_stats(int(checklist_id))
            serializer = ChecklistProgressStatsSerializer(stats_data)
            logger.info(f"Retrieved stats for checklist {checklist_id}")
            return Response(serializer.data)
        except ValidationError as e:
            logger.warning(f"Stats retrieval error: {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            logger.warning(f"Invalid checklist_id: {str(e)}")
            return Response(
                {'detail': 'Invalid checklist_id parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error retrieving stats: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to retrieve statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get user's progress summary across all checklists",
        responses={200: UserProgressSummarySerializer()}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def summary(self, request):
        """Get user's progress summary."""
        try:
            logger.debug(f"User {request.user.id} retrieving progress summary")
            summary_data = ChecklistProgressService.get_user_progress_summary(request.user.id)
            serializer = UserProgressSummarySerializer(summary_data)
            logger.info(f"Retrieved progress summary for user {request.user.id}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving summary: {str(e)}", exc_info=True)
            return Response(
                {'detail': 'Failed to retrieve summary'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
