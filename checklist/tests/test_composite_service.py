from django.test import TestCase
from django.contrib.auth import get_user_model

from checklist.services import ChecklistService
from checklist.models import Checklist, Sections, ListItem, Role, ChecklistType

User = get_user_model()

class CompositeServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        # create some roles
        self.role1 = Role.objects.create(name='ROLE_A')
        self.role2 = Role.objects.create(name='ROLE_B')

    def test_create_full_checklist(self):
        payload = {
            'name': 'Pre-stream Safety Checklist',
            'phase': 'pre-stream',
            'description': 'Safety checks before going live',
            'checklist_type': {'name': 'Safety'},
            'roles': [self.role1.id, self.role2.id],
            'sections': [
                {'name': 'Audio', 'order': 1, 'items': [
                    {'name': 'Microphone connected'},
                    {'name': 'Levels balanced'}
                ]},
                {'name': 'Video', 'order': 2, 'items': [
                    {'name': 'Camera focus ok'}
                ]}
            ]
        }

        checklist = ChecklistService.create_full_checklist(self.user, payload)
        self.assertIsInstance(checklist, Checklist)
        self.assertEqual(checklist.sections.count(), 2)
        total_items = ListItem.objects.filter(section__checklist=checklist).count()
        self.assertEqual(total_items, 3)
        self.assertEqual(checklist.roles.count(), 2)

    def test_update_full_checklist(self):
        # create initial checklist via service
        payload = {
            'name': 'Initial',
            'phase': 'pre-stream',
            'checklist_type': {'name': 'InitialType'},
        }
        checklist = ChecklistService.create_full_checklist(self.user, payload)
        # now update
        update = {
            'name': 'Updated Name',
            'roles': [self.role1.id],
            'sections': [
                {'name': 'Only', 'order': 1, 'items': [{'name': 'One item'}]}
            ]
        }
        updated = ChecklistService.update_full_checklist(self.user, checklist.id, update)
        self.assertEqual(updated.name, 'Updated Name')
        self.assertEqual(updated.sections.count(), 1)
        self.assertEqual(ListItem.objects.filter(section__checklist=updated).count(), 1)
        self.assertEqual(updated.roles.count(), 1)
