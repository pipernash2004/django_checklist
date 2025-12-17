"""
Business logic services for checklist app.
Extracted from views and serializers to follow clean architecture principles.
"""

import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, F

from .models import Role, ChecklistType, Checklist, Sections, ListItem, ChecklistProgress
from django.db import IntegrityError
from django.db import transaction

User = get_user_model()

logger = logging.getLogger(__name__)


# ============================================================
# ROLE SERVICES
# ============================================================

class RoleService:
    """Service for role-related business logic."""

    @staticmethod
    def create_role(user, name, description=None):
        """
        Create a new role.
        
        Args:
            user: User creating the role
            name: Name of the role
            description: Optional description
            
        Returns:
            Role instance
        """
        role = Role.objects.create(
            name=name,
            description=description or "",
            created_by=user,
            last_updated_by=user
        )
        logger.info(f"Role created by user {user.id}: {role.name}")
        return role

    @staticmethod
    def update_role(user, role_id, **kwargs):
        """
        Update a role.
        
        Args:
            user: User updating the role
            role_id: ID of the role to update
            **kwargs: Fields to update (name, description)
            
        Returns:
            Updated Role instance
        """
        try:
            role = Role.objects.get(id=role_id)
            allowed_fields = {'name', 'description'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            for field, value in update_fields.items():
                setattr(role, field, value)
            
            role.last_updated_by = user
            role.save()
            logger.info(f"Role {role_id} updated by user {user.id}")
            return role
        except Role.DoesNotExist:
            raise ValidationError(f"Role with id {role_id} does not exist")

    @staticmethod
    def delete_role(role_id):
        """
        Delete a role.
        
        Args:
            role_id: ID of the role to delete
        """
        try:
            role = Role.objects.get(id=role_id)
            role_name = role.name
            role.delete()
            logger.info(f"Role deleted: {role_name}")
        except Role.DoesNotExist:
            raise ValidationError(f"Role with id {role_id} does not exist")

    @staticmethod
    def get_all_roles():
        """Get all roles ordered by name."""
        return Role.objects.all().order_by('name')

    @staticmethod
    def get_role_by_name(name):
        """Get role by name (case-insensitive)."""
        return Role.objects.filter(name__iexact=name).first()

    @staticmethod
    def get_roles_for_checklist(checklist_id):
        """Get all roles assigned to a checklist."""
        try:
            checklist = Checklist.objects.get(id=checklist_id)
            return checklist.roles.all()
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")


# ============================================================
# CHECKLIST TYPE SERVICES
# ============================================================

class ChecklistTypeService:
    """Service for checklist type-related business logic."""

    @staticmethod
    def create_checklist_type(user, name, description=None):
        """
        Create a new checklist type.
        
        Args:
            user: User creating the checklist type
            name: Name of the checklist type
            description: Optional description
            
        Returns:
            ChecklistType instance
        """
        checklist_type = ChecklistType.objects.create(
            name=name,
            description=description or "",
            created_by=user,
            last_updated_by=user
        )
        logger.info(f"ChecklistType created by user {user.id}: {checklist_type.name}")
        return checklist_type

    @staticmethod
    def update_checklist_type(user, checklist_type_id, **kwargs):
        """
        Update a checklist type.
        
        Args:
            user: User updating the checklist type
            checklist_type_id: ID of the checklist type to update
            **kwargs: Fields to update (name, description)
            
        Returns:
            Updated ChecklistType instance
        """
        try:
            checklist_type = ChecklistType.objects.get(id=checklist_type_id)
            allowed_fields = {'name', 'description'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            for field, value in update_fields.items():
                setattr(checklist_type, field, value)
            
            checklist_type.last_updated_by = user
            checklist_type.save()
            logger.info(f"ChecklistType {checklist_type_id} updated by user {user.id}")
            return checklist_type
        except ChecklistType.DoesNotExist:
            raise ValidationError(f"ChecklistType with id {checklist_type_id} does not exist")

    @staticmethod
    def delete_checklist_type(checklist_type_id):
        """Delete a checklist type."""
        try:
            checklist_type = ChecklistType.objects.get(id=checklist_type_id)
            type_name = checklist_type.name
            checklist_type.delete()
            logger.info(f"ChecklistType deleted: {type_name}")
        except ChecklistType.DoesNotExist:
            raise ValidationError(f"ChecklistType with id {checklist_type_id} does not exist")

    @staticmethod
    def get_all_checklist_types():
        """Get all checklist types ordered by name."""
        return ChecklistType.objects.all().order_by('name')

    @staticmethod
    def get_checklist_type_by_name(name):
        """Get checklist type by name."""
        return ChecklistType.objects.filter(name__iexact=name).first()

    @staticmethod
    def get_checklist_type_stats(checklist_type_id):
        """Get statistics for a checklist type."""
        try:
            checklist_type = ChecklistType.objects.get(id=checklist_type_id)
            checklists = checklist_type.checklist_type_checklists.all()
            
            stats_data = {
                'total_checklists': checklists.count(),
                'sections_count': Sections.objects.filter(checklist_type=checklist_type).count(),
                'list_items_count': ListItem.objects.filter(section__checklist__checklist_type=checklist_type).count(),
            }
            logger.debug(f"Retrieved stats for ChecklistType {checklist_type_id}")
            return stats_data
        except ChecklistType.DoesNotExist:
            raise ValidationError(f"ChecklistType with id {checklist_type_id} does not exist")


# ============================================================
# CHECKLIST SERVICES
# ============================================================

class ChecklistService:
    """Service for checklist-related business logic."""

    @staticmethod
    def create_checklist(user, name, checklist_type_id, phase, roles=None, description=None, notes=None):
        """
        Create a new checklist.
        
        Args:
            user: User creating the checklist
            name: Name of the checklist
            checklist_type_id: ID of the checklist type
            phase: Phase of the checklist (pre-stream, on-stream, post-stream)
            roles: Optional list of role IDs
            description: Optional description
            notes: Optional notes
            
        Returns:
            Checklist instance
        """
        try:
            checklist_type = ChecklistType.objects.get(id=checklist_type_id)
        except ChecklistType.DoesNotExist:
            raise ValidationError(f"ChecklistType with id {checklist_type_id} does not exist")

        checklist = Checklist.objects.create(
            name=name,
            checklist_type=checklist_type,
            phase=phase,
            description=description or "",
            notes=notes or "",
            created_by=user,
            last_updated_by=user
        )

        if roles:
            checklist.roles.set(roles)

        logger.info(f"Checklist created by user {user.id}: {checklist.name}")
        return checklist

    @staticmethod
    @transaction.atomic
    def create_full_checklist(user, payload: dict):
        """Create a full checklist with nested checklist_type, roles, sections and list items.

        Payload keys expected:
        - name, description, phase, notes
        - checklist_type: {'id': int} or {'name': str}
        - roles: [int]
        - sections: [{name, description, order, items: [{name, description}]}]
        """
        try:
            checklist_type_data = payload.get('checklist_type')
            checklist_type = None
            if checklist_type_data:
                ct_id = checklist_type_data.get('id')
                ct_name = checklist_type_data.get('name')
                if ct_id:
                    checklist_type = ChecklistType.objects.filter(id=ct_id).first()
                    if not checklist_type:
                        raise ValidationError({'checklist_type': 'ChecklistType with provided id does not exist.'})
                elif ct_name:
                    try:
                        checklist_type, _ = ChecklistType.objects.get_or_create(
                            name=ct_name.strip(),
                            defaults={
                                'description': checklist_type_data.get('description', ''),
                                'created_by': user,
                                'last_updated_by': user
                            }
                        )
                    except IntegrityError:
                        checklist_type = ChecklistType.objects.filter(name=ct_name.strip()).first()
                        if not checklist_type:
                            raise ValidationError({'checklist_type': 'Could not create or find ChecklistType.'})

            checklist = Checklist.objects.create(
                name=payload.get('name'),
                description=payload.get('description', ''),
                phase=payload.get('phase'),
                notes=payload.get('notes', ''),
                checklist_type=checklist_type,
                created_by=user,
                last_updated_by=user,
            )

            # roles
            role_ids = payload.get('roles') or []
            if role_ids:
                roles_qs = Role.objects.filter(id__in=role_ids)
                if roles_qs.count() != len(role_ids):
                    missing = set(role_ids) - set(roles_qs.values_list('id', flat=True))
                    raise ValidationError({'roles': f'Roles not found: {sorted(list(missing))}'})
                checklist.roles.set(roles_qs)

            # sections and items
            sections_data = payload.get('sections') or []
            for sec in sections_data:
                items = sec.get('items') or []
                section = Sections.objects.create(
                    checklist=checklist,
                    name=sec.get('name'),
                    description=sec.get('description', ''),
                    order=sec.get('order', 0),
                    created_by=user,
                    last_updated_by=user,
                )
                # bulk create items for this section
                item_objs = []
                for it in items:
                    item_objs.append(ListItem(
                        section=section,
                        name=it.get('name'),
                        description=it.get('description', ''),
                        created_by=user,
                        last_updated_by=user,
                    ))
                if item_objs:
                    ListItem.objects.bulk_create(item_objs)

            return checklist
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error in create_full_checklist: {str(e)}", exc_info=True)
            raise

    @staticmethod
    @transaction.atomic
    def update_full_checklist(user, checklist_id: int, payload: dict):
        """Update checklist and its nested structures. If `sections` is provided it will fully replace existing sections.

        Similar payload as `create_full_checklist`.
        """
        try:
            checklist = Checklist.objects.get(pk=checklist_id)
        except Checklist.DoesNotExist:
            raise ValidationError({'checklist': 'Checklist does not exist.'})

        try:
            # simple fields
            for field in ('name', 'description', 'phase', 'notes'):
                if field in payload:
                    setattr(checklist, field, payload.get(field))

            # checklist_type
            ct_data = payload.get('checklist_type')
            if ct_data is not None:
                if ct_data.get('id'):
                    ct = ChecklistType.objects.filter(id=ct_data.get('id')).first()
                    if not ct:
                        raise ValidationError({'checklist_type': 'ChecklistType with provided id does not exist.'})
                    checklist.checklist_type = ct
                elif ct_data.get('name'):
                    try:
                        ct, _ = ChecklistType.objects.get_or_create(
                            name=ct_data.get('name').strip(),
                            defaults={'description': ct_data.get('description', ''), 'created_by': user, 'last_updated_by': user}
                        )
                        checklist.checklist_type = ct
                    except IntegrityError:
                        ct = ChecklistType.objects.filter(name=ct_data.get('name').strip()).first()
                        if not ct:
                            raise ValidationError({'checklist_type': 'Could not create or find ChecklistType.'})

            checklist.last_updated_by = user
            checklist.save()

            # roles
            if 'roles' in payload:
                role_ids = payload.get('roles') or []
                if role_ids:
                    roles_qs = Role.objects.filter(id__in=role_ids)
                    if roles_qs.count() != len(role_ids):
                        missing = set(role_ids) - set(roles_qs.values_list('id', flat=True))
                        raise ValidationError({'roles': f'Roles not found: {sorted(list(missing))}'})
                    checklist.roles.set(roles_qs)
                else:
                    checklist.roles.clear()

            # sections replacement
            if 'sections' in payload:
                # delete existing sections (cascade deletes listitems)
                checklist.sections.all().delete()
                sections_data = payload.get('sections') or []
                for sec in sections_data:
                    items = sec.get('items') or []
                    section = Sections.objects.create(
                        checklist=checklist,
                        name=sec.get('name'),
                        description=sec.get('description', ''),
                        order=sec.get('order', 0),
                        created_by=user,
                        last_updated_by=user,
                    )
                    item_objs = []
                    for it in items:
                        item_objs.append(ListItem(
                            section=section,
                            name=it.get('name'),
                            description=it.get('description', ''),
                            created_by=user,
                            last_updated_by=user,
                        ))
                    if item_objs:
                        ListItem.objects.bulk_create(item_objs)

            return checklist
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error in update_full_checklist: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def update_checklist(user, checklist_id, **kwargs):
        """
        Update a checklist.
        
        Args:
            user: User updating the checklist
            checklist_id: ID of the checklist to update
            **kwargs: Fields to update
            
        Returns:
            Updated Checklist instance
        """
        try:
            checklist = Checklist.objects.get(id=checklist_id)
            allowed_fields = {'name', 'description', 'phase', 'notes'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            for field, value in update_fields.items():
                setattr(checklist, field, value)
            
            checklist.last_updated_by = user
            checklist.save()
            logger.info(f"Checklist {checklist_id} updated by user {user.id}")
            return checklist
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")

    @staticmethod
    def add_roles_to_checklist(checklist_id, role_ids):
        """
        Add roles to a checklist.
        
        Args:
            checklist_id: ID of the checklist
            role_ids: List of role IDs to add
        """
        try:
            checklist = Checklist.objects.get(id=checklist_id)
            checklist.roles.add(*role_ids)
            logger.info(f"Added {len(role_ids)} roles to checklist {checklist_id}")
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")

    @staticmethod
    def remove_roles_from_checklist(checklist_id, role_ids):
        """
        Remove roles from a checklist.
        
        Args:
            checklist_id: ID of the checklist
            role_ids: List of role IDs to remove
        """
        try:
            checklist = Checklist.objects.get(id=checklist_id)
            checklist.roles.remove(*role_ids)
            logger.info(f"Removed {len(role_ids)} roles from checklist {checklist_id}")
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")

    @staticmethod
    def delete_checklist(checklist_id):
        """Delete a checklist and all associated data."""
        try:
            checklist = Checklist.objects.get(id=checklist_id)
            checklist_name = checklist.name
            checklist.delete()
            logger.info(f"Checklist deleted: {checklist_name}")
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")

    @staticmethod
    def get_all_checklists():
        """Get all checklists ordered by creation date."""
        return Checklist.objects.all().order_by('-created_at')

    @staticmethod
    def get_checklists_by_type(checklist_type_id):
        """Get all checklists for a specific type."""
        return Checklist.objects.filter(checklist_type_id=checklist_type_id).order_by('-created_at')

    @staticmethod
    def get_checklists_by_phase(phase):
        """Get all checklists for a specific phase."""
        valid_phases = ['pre-stream', 'on-stream', 'post-stream']
        if phase not in valid_phases:
            raise ValidationError(f"Invalid phase. Must be one of {valid_phases}")
        return Checklist.objects.filter(phase=phase).order_by('-created_at')

    @staticmethod
    def get_checklist_stats(checklist_id):
        """Get comprehensive statistics for a checklist."""
        try:
            checklist = Checklist.objects.get(id=checklist_id)
            
            sections = checklist.sections.all()
            total_sections = sections.count()
            
            list_items = ListItem.objects.filter(section__in=sections)
            total_items = list_items.count()
            
            progress_records = ChecklistProgress.objects.filter(checklist=checklist)
            total_progress = progress_records.count()
            
            progress_by_status = {
                'pending': progress_records.filter(status='pending').count(),
                'in_progress': progress_records.filter(status='in_progress').count(),
                'completed': progress_records.filter(status='completed').count(),
                'blocked': progress_records.filter(status='blocked').count(),
            }
            
            stats_data = {
                'total_sections': total_sections,
                'total_items': total_items,
                'total_progress_records': total_progress,
                'progress_by_status': progress_by_status,
                'roles_count': checklist.roles.count(),
            }
            logger.debug(f"Retrieved stats for checklist {checklist_id}")
            return stats_data
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")

    @staticmethod
    def get_checklist_sections(checklist_id):
        """Get all sections for a checklist ordered by order field."""
        try:
            Checklist.objects.get(id=checklist_id)
            return Sections.objects.filter(checklist_id=checklist_id).order_by('order')
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")


# ============================================================
# SECTION SERVICES
# ============================================================

class SectionService:
    """Service for section-related business logic."""

    @staticmethod
    def create_section(user, checklist_id, name, checklist_type_id=None, order=0, description=None):
        """
        Create a new section.
        
        Args:
            user: User creating the section
            checklist_id: ID of the parent checklist
            name: Name of the section
            checklist_type_id: Optional checklist type ID
            order: Order of the section (default: 0)
            description: Optional description
            
        Returns:
            Sections instance
        """
        try:
            checklist = Checklist.objects.get(id=checklist_id)
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")

        checklist_type = None
        if checklist_type_id:
            try:
                checklist_type = ChecklistType.objects.get(id=checklist_type_id)
            except ChecklistType.DoesNotExist:
                raise ValidationError(f"ChecklistType with id {checklist_type_id} does not exist")

        section = Sections.objects.create(
            name=name,
            description=description or "",
            checklist=checklist,
            checklist_type=checklist_type,
            order=order,
            created_by=user,
            last_updated_by=user
        )
        logger.info(f"Section created by user {user.id}: {section.name}")
        return section

    @staticmethod
    def update_section(user, section_id, **kwargs):
        """
        Update a section.
        
        Args:
            user: User updating the section
            section_id: ID of the section to update
            **kwargs: Fields to update
            
        Returns:
            Updated Sections instance
        """
        try:
            section = Sections.objects.get(id=section_id)
            allowed_fields = {'name', 'description', 'order'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            for field, value in update_fields.items():
                setattr(section, field, value)
            
            section.last_updated_by = user
            section.save()
            logger.info(f"Section {section_id} updated by user {user.id}")
            return section
        except Sections.DoesNotExist:
            raise ValidationError(f"Section with id {section_id} does not exist")

    @staticmethod
    def delete_section(section_id):
        """Delete a section and all associated list items."""
        try:
            section = Sections.objects.get(id=section_id)
            section_name = section.name
            section.delete()
            logger.info(f"Section deleted: {section_name}")
        except Sections.DoesNotExist:
            raise ValidationError(f"Section with id {section_id} does not exist")

    @staticmethod
    def get_section_items(section_id):
        """Get all list items for a section."""
        try:
            Sections.objects.get(id=section_id)
            return ListItem.objects.filter(section_id=section_id).order_by('-created_at')
        except Sections.DoesNotExist:
            raise ValidationError(f"Section with id {section_id} does not exist")

    @staticmethod
    def reorder_sections(checklist_id, section_orders):
        """
        Reorder sections for a checklist.
        
        Args:
            checklist_id: ID of the checklist
            section_orders: List of tuples (section_id, new_order)
        """
        try:
            checklist = Checklist.objects.get(id=checklist_id)
            with transaction.atomic():
                for section_id, order in section_orders:
                    try:
                        section = Sections.objects.get(id=section_id, checklist=checklist)
                        section.order = order
                        section.save()
                    except Sections.DoesNotExist:
                        logger.warning(f"Section {section_id} not found in checklist {checklist_id}")
                logger.info(f"Sections reordered in checklist {checklist_id}")
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")


# ============================================================
# LIST ITEM SERVICES
# ============================================================

class ListItemService:
    """Service for list item-related business logic."""

    @staticmethod
    def create_list_item(user, section_id, name, description=None):
        """
        Create a new list item.
        
        Args:
            user: User creating the list item
            section_id: ID of the parent section
            name: Name of the list item
            description: Optional description
            
        Returns:
            ListItem instance
        """
        try:
            section = Sections.objects.get(id=section_id)
        except Sections.DoesNotExist:
            raise ValidationError(f"Section with id {section_id} does not exist")

        list_item = ListItem.objects.create(
            name=name,
            description=description or "",
            section=section,
            created_by=user,
            last_updated_by=user
        )
        logger.info(f"ListItem created by user {user.id}: {list_item.name}")
        return list_item

    @staticmethod
    def update_list_item(user, list_item_id, **kwargs):
        """
        Update a list item.
        
        Args:
            user: User updating the list item
            list_item_id: ID of the list item to update
            **kwargs: Fields to update (name, description)
            
        Returns:
            Updated ListItem instance
        """
        try:
            list_item = ListItem.objects.get(id=list_item_id)
            allowed_fields = {'name', 'description'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            for field, value in update_fields.items():
                setattr(list_item, field, value)
            
            list_item.last_updated_by = user
            list_item.save()
            logger.info(f"ListItem {list_item_id} updated by user {user.id}")
            return list_item
        except ListItem.DoesNotExist:
            raise ValidationError(f"ListItem with id {list_item_id} does not exist")

    @staticmethod
    def delete_list_item(list_item_id):
        """Delete a list item."""
        try:
            list_item = ListItem.objects.get(id=list_item_id)
            item_name = list_item.name
            list_item.delete()
            logger.info(f"ListItem deleted: {item_name}")
        except ListItem.DoesNotExist:
            raise ValidationError(f"ListItem with id {list_item_id} does not exist")

    @staticmethod
    def get_list_items_by_section(section_id):
        """Get all list items for a section."""
        try:
            Sections.objects.get(id=section_id)
            return ListItem.objects.filter(section_id=section_id).order_by('-created_at')
        except Sections.DoesNotExist:
            raise ValidationError(f"Section with id {section_id} does not exist")

    @staticmethod
    def get_list_item_progress(list_item_id):
        """Get all progress records for a list item."""
        try:
            ListItem.objects.get(id=list_item_id)
            return ChecklistProgress.objects.filter(items_id=list_item_id)
        except ListItem.DoesNotExist:
            raise ValidationError(f"ListItem with id {list_item_id} does not exist")


# ============================================================
# CHECKLIST PROGRESS SERVICES
# ============================================================

class ChecklistProgressService:
    """Service for checklist progress-related business logic."""

    @staticmethod
    def create_progress(user, checklist_id, list_item_id=None, status='pending'):
        """
        Create a new progress record.
        
        Args:
            user: User creating the progress record
            checklist_id: ID of the checklist
            list_item_id: Optional list item ID
            status: Status of the progress (default: pending)
            
        Returns:
            ChecklistProgress instance
        """
        try:
            checklist = Checklist.objects.get(id=checklist_id)
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")

        list_item = None
        if list_item_id:
            try:
                list_item = ListItem.objects.get(id=list_item_id)
            except ListItem.DoesNotExist:
                raise ValidationError(f"ListItem with id {list_item_id} does not exist")

        progress = ChecklistProgress.objects.create(
            checklist=checklist,
            items=list_item,
            status=status,
            user=user
        )
        logger.info(f"ChecklistProgress created for user {user.id} on checklist {checklist_id}")
        return progress

    @staticmethod
    def update_progress_status(progress_id, status):
        """
        Update progress status.
        
        Args:
            progress_id: ID of the progress record
            status: New status (pending, in_progress, completed, blocked)
            
        Returns:
            Updated ChecklistProgress instance
        """
        valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status. Must be one of {valid_statuses}")

        try:
            progress = ChecklistProgress.objects.get(id=progress_id)
            progress.status = status
            progress.save(update_fields=['status', 'updated_at'])
            logger.info(f"ChecklistProgress {progress_id} status updated to {status}")
            return progress
        except ChecklistProgress.DoesNotExist:
            raise ValidationError(f"ChecklistProgress with id {progress_id} does not exist")

    @staticmethod
    def get_user_checklist_progress(user_id, checklist_id):
        """
        Get all progress records for a user on a specific checklist.
        
        Args:
            user_id: ID of the user
            checklist_id: ID of the checklist
            
        Returns:
            QuerySet of ChecklistProgress instances
        """
        return ChecklistProgress.objects.filter(
            user_id=user_id,
            checklist_id=checklist_id
        ).order_by('-updated_at')

    @staticmethod
    def get_user_all_progress(user_id):
        """Get all progress records for a user."""
        return ChecklistProgress.objects.filter(user_id=user_id).order_by('-updated_at')

    @staticmethod
    def get_checklist_progress_stats(checklist_id):
        """
        Get progress statistics for a checklist.
        
        Args:
            checklist_id: ID of the checklist
            
        Returns:
            Dictionary with progress statistics
        """
        try:
            checklist = Checklist.objects.get(id=checklist_id)
            progress_records = ChecklistProgress.objects.filter(checklist=checklist)
            
            total_progress = progress_records.count()
            users_count = progress_records.values('user_id').distinct().count()
            
            stats_data = {
                'total_progress_records': total_progress,
                'total_unique_users': users_count,
                'pending': progress_records.filter(status='pending').count(),
                'in_progress': progress_records.filter(status='in_progress').count(),
                'completed': progress_records.filter(status='completed').count(),
                'blocked': progress_records.filter(status='blocked').count(),
                'completion_percentage': (
                    (progress_records.filter(status='completed').count() / total_progress * 100)
                    if total_progress > 0 else 0
                ),
            }
            logger.debug(f"Retrieved progress stats for checklist {checklist_id}")
            return stats_data
        except Checklist.DoesNotExist:
            raise ValidationError(f"Checklist with id {checklist_id} does not exist")

    @staticmethod
    def get_user_progress_summary(user_id):
        """
        Get a summary of all progress for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with progress summary
        """
        user_progress = ChecklistProgress.objects.filter(user_id=user_id)
        
        summary_data = {
            'total_checklists': user_progress.values('checklist_id').distinct().count(),
            'total_items': user_progress.count(),
            'pending': user_progress.filter(status='pending').count(),
            'in_progress': user_progress.filter(status='in_progress').count(),
            'completed': user_progress.filter(status='completed').count(),
            'blocked': user_progress.filter(status='blocked').count(),
        }
        logger.debug(f"Retrieved progress summary for user {user_id}")
        return summary_data

    @staticmethod
    def delete_progress(progress_id):
        """Delete a progress record."""
        try:
            progress = ChecklistProgress.objects.get(id=progress_id)
            progress.delete()
            logger.info(f"ChecklistProgress {progress_id} deleted")
        except ChecklistProgress.DoesNotExist:
            raise ValidationError(f"ChecklistProgress with id {progress_id} does not exist")

    @staticmethod
    @transaction.atomic
    def bulk_update_progress_status(progress_ids, status):
        """
        Bulk update status for multiple progress records.
        
        Args:
            progress_ids: List of progress IDs
            status: New status for all records
            
        Returns:
            Number of records updated
        """
        valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status. Must be one of {valid_statuses}")

        updated_count = ChecklistProgress.objects.filter(
            id__in=progress_ids
        ).update(status=status, updated_at=timezone.now())
        
        logger.info(f"Bulk updated {updated_count} progress records to status {status}")
        return updated_count
