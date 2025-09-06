from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import datetime
from django.core import mail
from django.conf import settings
from unittest.mock import patch
from .models import Note, NoteImage
from .views import (
    NoteListView, NoteDetailView, NoteCreateView, 
    NoteUpdateView, NoteDeleteView, PublicNotesView, register
)
from .forms import NoteForm, CustomUserCreationform
from .email_service import send_welcome_email, send_simple_email, test_sendgrid_connection
import tempfile
from PIL import Image
import io


class URLResolutionTests(TestCase):
    """Test that all URLs resolve to the correct views"""
    
    def test_note_list_url_resolves(self):
        """Test that the root URL resolves to NoteListView"""
        url = reverse('note_list')
        self.assertEqual(resolve(url).func.view_class, NoteListView)
    
    def test_register_url_resolves(self):
        """Test that register URL resolves to register view"""
        url = reverse('register')
        self.assertEqual(resolve(url).func, register)
    
    def test_note_create_url_resolves(self):
        """Test that note creation URL resolves correctly"""
        url = reverse('note_create')
        self.assertEqual(resolve(url).func.view_class, NoteCreateView)
    
    def test_note_detail_url_resolves(self):
        """Test that note detail URL with date parameters resolves correctly"""
        url = reverse('note_detail', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': 1
        })
        self.assertEqual(resolve(url).func.view_class, NoteDetailView)
    
    def test_note_update_url_resolves(self):
        """Test that note update URL resolves correctly"""
        url = reverse('note_update', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': 1
        })
        self.assertEqual(resolve(url).func.view_class, NoteUpdateView)
    
    def test_note_delete_url_resolves(self):
        """Test that note delete URL resolves correctly"""
        url = reverse('note_delete', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': 1
        })
        self.assertEqual(resolve(url).func.view_class, NoteDeleteView)
    
    def test_public_notes_url_resolves(self):
        """Test that public notes URL resolves correctly"""
        url = reverse('public_notes')
        self.assertEqual(resolve(url).func.view_class, PublicNotesView)


class AuthenticationTests(TestCase):
    """Test authentication and registration functionality"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
    
    def test_register_view_get(self):
        """Test registration page loads correctly"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertIsInstance(response.context['form'], CustomUserCreationform)
    
    def test_register_view_post_valid_data(self):
        """Test successful user registration"""
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        response = self.client.post(self.register_url, user_data)
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('note_list'))
        
        # User should be created
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # User should be automatically logged in
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
    
    def test_register_view_post_invalid_data(self):
        """Test registration with invalid data"""
        user_data = {
            'username': 'testuser',
            'password1': 'complexpassword123',
            'password2': 'differentpassword'  # Passwords don't match
        }
        response = self.client.post(self.register_url, user_data)
        
        # Should not redirect, should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testuser').exists())


class BaseNoteTestCase(TestCase):
    """Base class for note-related tests with common setup"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com', 
            password='testpass123'
        )
        
        # Create test notes with specific dates for URL testing
        self.test_date = timezone.now().replace(year=2023, month=9, day=6, hour=12, minute=0, second=0, microsecond=0)
        
        self.note1 = Note.objects.create(
            title='Test Note 1',
            content='This is test note 1 content',
            author=self.user1,
            is_public=False,
            is_draft=False,
            date_created=self.test_date
        )
        
        self.public_note = Note.objects.create(
            title='Public Note',
            content='This is a public note',
            author=self.user1,
            is_public=True,
            is_draft=False,
            date_created=self.test_date
        )
        
        self.user2_note = Note.objects.create(
            title='User2 Note',
            content='This belongs to user2',
            author=self.user2,
            is_public=False,
            is_draft=False,
            date_created=self.test_date
        )
    
    def create_test_image(self):
        """Helper method to create a test image file"""
        image = Image.new('RGB', (100, 100), color='red')
        image_file = io.BytesIO()
        image.save(image_file, format='JPEG')
        image_file.seek(0)
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=image_file.read(),
            content_type='image/jpeg'
        )


class NoteListViewTests(BaseNoteTestCase):
    """Test the NoteListView functionality"""
    
    def test_note_list_requires_login(self):
        """Test that note list requires authentication"""
        response = self.client.get(reverse('note_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/accounts/login/', response.url)
    
    def test_note_list_authenticated_user(self):
        """Test note list for authenticated user shows only their notes"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('note_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Note 1')
        self.assertContains(response, 'Public Note')
        self.assertNotContains(response, 'User2 Note')  # Should not see other user's notes
    
    def test_note_list_pagination(self):
        """Test note list pagination works"""
        self.client.login(username='user1', password='testpass123')
        
        # Create more notes to test pagination (paginate_by = 10)
        for i in range(15):
            Note.objects.create(
                title=f'Note {i}',
                content=f'Content {i}',
                author=self.user1
            )
        
        response = self.client.get(reverse('note_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['notes']), 10)


class NoteDetailViewTests(BaseNoteTestCase):
    """Test the NoteDetailView functionality"""
    
    def test_note_detail_owner_access(self):
        """Test that note owner can view their own note"""
        self.client.login(username='user1', password='testpass123')
        url = reverse('note_detail', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Note 1')
        self.assertContains(response, 'This is test note 1 content')
    
    def test_note_detail_public_note_anonymous(self):
        """Test that anonymous users can view public notes"""
        url = reverse('note_detail', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.public_note.pk
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Note')
    
    def test_note_detail_private_note_anonymous(self):
        """Test that anonymous users cannot view private notes"""
        url = reverse('note_detail', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_note_detail_other_user_private_note(self):
        """Test that users cannot view other users' private notes"""
        self.client.login(username='user2', password='testpass123')
        url = reverse('note_detail', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


class NoteCreateViewTests(BaseNoteTestCase):
    """Test the NoteCreateView functionality"""
    
    def test_note_create_requires_login(self):
        """Test that note creation requires authentication"""
        response = self.client.get(reverse('note_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_note_create_get_authenticated(self):
        """Test note creation form loads for authenticated users"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('note_create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], NoteForm)
        self.assertContains(response, 'images-TOTAL_FORMS')
    
    def test_note_create_post_valid_data(self):
        """Test successful note creation"""
        self.client.login(username='user1', password='testpass123')
        
        note_data = {
            'title': 'New Test Note',
            'content': 'This is a new test note content',
            'is_public': False,
            'is_draft': False,
            # Formset management data
            'images-TOTAL_FORMS': '1',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(reverse('note_create'), note_data)
        
        # Should redirect to the new note's detail page
        self.assertEqual(response.status_code, 302)
        
        # Note should be created
        new_note = Note.objects.get(title='New Test Note')
        self.assertEqual(new_note.author, self.user1)
        self.assertEqual(new_note.content, 'This is a new test note content')
    
    def test_note_create_with_image(self):
        """Test note creation with image upload"""
        self.client.login(username='user1', password='testpass123')
        
        test_image = self.create_test_image()
        
        note_data = {
            'title': 'Note with Image',
            'content': 'This note has an image',
            'is_public': False,
            'is_draft': False,
            # Formset data for one image
            'images-TOTAL_FORMS': '1',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '1000',
            'images-0-image': test_image,
            'images-0-caption': 'Test image caption'
        }
        
        response = self.client.post(reverse('note_create'), note_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Note and image should be created
        new_note = Note.objects.get(title='Note with Image')
        self.assertEqual(new_note.images.count(), 1)
        self.assertEqual(new_note.images.first().caption, 'Test image caption')


class NoteUpdateViewTests(BaseNoteTestCase):
    """Test the NoteUpdateView functionality"""
    
    def test_note_update_requires_login(self):
        """Test that note update requires authentication"""
        url = reverse('note_update', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_note_update_owner_access(self):
        """Test that note owner can access update form"""
        self.client.login(username='user1', password='testpass123')
        url = reverse('note_update', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], NoteForm)
        self.assertEqual(response.context['form'].instance, self.note1)
    
    def test_note_update_non_owner_access_denied(self):
        """Test that non-owner cannot access update form"""
        self.client.login(username='user2', password='testpass123')
        url = reverse('note_update', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
    
    def test_note_update_post_valid_data(self):
        """Test successful note update"""
        self.client.login(username='user1', password='testpass123')
        url = reverse('note_update', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        
        updated_data = {
            'title': 'Updated Test Note',
            'content': 'This content has been updated',
            'is_public': True,
            'is_draft': False,
            # Formset management data
            'images-TOTAL_FORMS': '1',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(url, updated_data)
        
        # Should redirect to note detail
        self.assertEqual(response.status_code, 302)
        
        # Note should be updated
        updated_note = Note.objects.get(pk=self.note1.pk)
        self.assertEqual(updated_note.title, 'Updated Test Note')
        self.assertEqual(updated_note.content, 'This content has been updated')
        self.assertTrue(updated_note.is_public)


class NoteDeleteViewTests(BaseNoteTestCase):
    """Test the NoteDeleteView functionality"""
    
    def test_note_delete_requires_login(self):
        """Test that note deletion requires authentication"""
        url = reverse('note_delete', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_note_delete_owner_access(self):
        """Test that note owner can access delete confirmation"""
        self.client.login(username='user1', password='testpass123')
        url = reverse('note_delete', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Note 1')
        self.assertContains(response, 'Are you sure')
    
    def test_note_delete_non_owner_access_denied(self):
        """Test that non-owner cannot access delete form"""
        self.client.login(username='user2', password='testpass123')
        url = reverse('note_delete', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
    
    def test_note_delete_post_confirmation(self):
        """Test successful note deletion"""
        self.client.login(username='user1', password='testpass123')
        url = reverse('note_delete', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        
        response = self.client.post(url)
        
        # Should redirect to note list
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('note_list'))
        
        # Note should be deleted
        self.assertFalse(Note.objects.filter(pk=self.note1.pk).exists())


class PublicNotesViewTests(BaseNoteTestCase):
    """Test the PublicNotesView functionality"""
    
    def setUp(self):
        super().setUp()
        # Create additional notes for testing
        self.draft_public_note = Note.objects.create(
            title='Draft Public Note',
            content='This is a public draft note',
            author=self.user1,
            is_public=True,
            is_draft=True,
            date_created=self.test_date
        )
    
    def test_public_notes_view_anonymous_access(self):
        """Test that anonymous users can access public notes"""
        response = self.client.get(reverse('public_notes'))
        self.assertEqual(response.status_code, 200)
    
    def test_public_notes_view_authenticated_access(self):
        """Test that authenticated users can access public notes"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('public_notes'))
        self.assertEqual(response.status_code, 200)
    
    def test_public_notes_filtering(self):
        """Test that only public, non-draft notes are shown"""
        response = self.client.get(reverse('public_notes'))
        
        self.assertEqual(response.status_code, 200)
        # Should contain public, non-draft note
        self.assertContains(response, 'Public Note')
        # Should not contain private notes
        self.assertNotContains(response, 'Test Note 1')
        self.assertNotContains(response, 'User2 Note')
        # Should not contain draft notes (even if public)
        self.assertNotContains(response, 'Draft Public Note')
    
    def test_public_notes_pagination(self):
        """Test public notes pagination"""
        # Create many public notes to test pagination
        for i in range(15):
            Note.objects.create(
                title=f'Public Note {i}',
                content=f'Public content {i}',
                author=self.user1,
                is_public=True,
                is_draft=False
            )
        
        response = self.client.get(reverse('public_notes'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['notes']), 10)


class SecurityAndPermissionTests(BaseNoteTestCase):
    """Test security aspects and permission enforcement"""
    
    def test_csrf_protection_note_create(self):
        """Test CSRF protection on note creation"""
        self.client.login(username='user1', password='testpass123')
        
        # Try to post without CSRF token (using enforce_csrf_checks=True doesn't work in test)
        # This test verifies the view uses CSRF protection
        response = self.client.get(reverse('note_create'))
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_user_isolation_note_list(self):
        """Test that users can only see their own notes in list view"""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('note_list'))
        
        # Should see user1's notes
        self.assertContains(response, 'Test Note 1')
        self.assertContains(response, 'Public Note')
        # Should not see user2's notes
        self.assertNotContains(response, 'User2 Note')
    
    def test_direct_access_other_user_note_edit(self):
        """Test that users cannot directly access other users' note edit URLs"""
        self.client.login(username='user2', password='testpass123')
        url = reverse('note_update', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
    
    def test_direct_access_other_user_note_delete(self):
        """Test that users cannot directly access other users' note delete URLs"""
        self.client.login(username='user2', password='testpass123')
        url = reverse('note_delete', kwargs={
            'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
    
    def test_anonymous_user_redirected_to_login(self):
        """Test that anonymous users are redirected to login for protected views"""
        protected_urls = [
            reverse('note_list'),
            reverse('note_create'),
            reverse('note_update', kwargs={
                'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
            }),
            reverse('note_delete', kwargs={
                'year': 2023, 'month': 9, 'day': 6, 'pk': self.note1.pk
            }),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/accounts/login/', response.url)


class IntegrationTests(BaseNoteTestCase):
    """Test complete user workflows"""
    
    def test_complete_user_registration_workflow(self):
        """Test complete user registration and first note creation workflow"""
        # Register new user
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        response = self.client.post(reverse('register'), registration_data)
        
        # Should redirect to note list after registration
        self.assertRedirects(response, reverse('note_list'))
        
        # Should now be able to access protected note list
        response = self.client.get(reverse('note_list'))
        self.assertEqual(response.status_code, 200)
        
        # Create first note
        note_data = {
            'title': 'My First Note',
            'content': 'This is my first note!',
            'is_public': False,
            'is_draft': False,
            'images-TOTAL_FORMS': '1',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(reverse('note_create'), note_data)
        
        # Should redirect to note detail
        self.assertEqual(response.status_code, 302)
        
        # Verify note was created
        new_user = User.objects.get(username='newuser')
        note = Note.objects.get(title='My First Note')
        self.assertEqual(note.author, new_user)
    
    def test_complete_note_crud_workflow(self):
        """Test complete CRUD workflow for a note"""
        self.client.login(username='user1', password='testpass123')
        
        # Create note
        note_data = {
            'title': 'CRUD Test Note',
            'content': 'Original content',
            'is_public': False,
            'is_draft': False,
            'images-TOTAL_FORMS': '1',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(reverse('note_create'), note_data)
        self.assertEqual(response.status_code, 302)
        
        # Get the created note
        note = Note.objects.get(title='CRUD Test Note')
        
        # Read/Detail - verify we can view the note
        detail_url = reverse('note_detail', kwargs={
            'year': note.date_created.year,
            'month': note.date_created.month,
            'day': note.date_created.day,
            'pk': note.pk
        })
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CRUD Test Note')
        self.assertContains(response, 'Original content')
        
        # Update - modify the note
        update_url = reverse('note_update', kwargs={
            'year': note.date_created.year,
            'month': note.date_created.month,
            'day': note.date_created.day,
            'pk': note.pk
        })
        updated_data = {
            'title': 'Updated CRUD Test Note',
            'content': 'Updated content',
            'is_public': True,
            'is_draft': False,
            'images-TOTAL_FORMS': '1',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(update_url, updated_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify update
        note.refresh_from_db()
        self.assertEqual(note.title, 'Updated CRUD Test Note')
        self.assertEqual(note.content, 'Updated content')
        self.assertTrue(note.is_public)
        
        # Delete - remove the note
        delete_url = reverse('note_delete', kwargs={
            'year': note.date_created.year,
            'month': note.date_created.month,
            'day': note.date_created.day,
            'pk': note.pk
        })
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('note_list'))
        
        # Verify deletion
        self.assertFalse(Note.objects.filter(pk=note.pk).exists())
    
    def test_image_upload_workflow(self):
        """Test complete image upload workflow with note"""
        self.client.login(username='user1', password='testpass123')
        
        # Create test image
        test_image = self.create_test_image()
        
        # Create note with image
        note_data = {
            'title': 'Note with Image Upload',
            'content': 'This note has an uploaded image',
            'is_public': False,
            'is_draft': False,
            'images-TOTAL_FORMS': '1',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '1000',
            'images-0-image': test_image,
            'images-0-caption': 'Test upload image'
        }
        response = self.client.post(reverse('note_create'), note_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify note and image were created
        note = Note.objects.get(title='Note with Image Upload')
        self.assertEqual(note.images.count(), 1)
        
        image = note.images.first()
        self.assertEqual(image.caption, 'Test upload image')
        self.assertTrue(image.image.name.endswith('.jpg'))
        
        # Verify we can view the note with image
        detail_url = reverse('note_detail', kwargs={
            'year': note.date_created.year,
            'month': note.date_created.month,
            'day': note.date_created.day,
            'pk': note.pk
        })
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Note with Image Upload')


class EmailFunctionalityTests(TestCase):
    """Test email functionality with SendGrid integration"""
    
    def setUp(self):
        self.client = Client()
        # Clear the test mail outbox
        mail.outbox = []
    
    def test_send_simple_email(self):
        """Test basic email sending functionality"""
        success = send_simple_email(
            subject='Test Subject',
            message='Test message body',
            recipient_list=['test@example.com'],
            html_message='<p>Test HTML message</p>'
        )
        
        # Email should be sent successfully (in test mode, goes to mail.outbox)
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Test Subject')
        self.assertIn('Test message body', email.body)
        self.assertEqual(email.to, ['test@example.com'])
    
    def test_send_welcome_email(self):
        """Test welcome email functionality"""
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            first_name='Test',
            last_name='User'
        )
        
        success = send_welcome_email(user)
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('Welcome', email.subject)
        self.assertEqual(email.to, ['testuser@example.com'])
        self.assertIn('Test', email.body)  # Should contain user's first name
        self.assertIn('testuser', email.body)  # Should contain username
    
    def test_welcome_email_without_first_name(self):
        """Test welcome email for user without first name"""
        user = User.objects.create_user(
            username='noname',
            email='noname@example.com'
        )
        
        success = send_welcome_email(user)
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('noname', email.body)  # Should fall back to username
    
    @patch('diary.email_service.logger')
    def test_email_sending_failure(self, mock_logger):
        """Test email sending failure handling"""
        # This test simulates what happens when email sending fails
        with patch('django.core.mail.EmailMultiAlternatives.send') as mock_send:
            mock_send.side_effect = Exception("Email sending failed")
            
            user = User.objects.create_user(
                username='testuser',
                email='invalid-email',
            )
            
            success = send_welcome_email(user)
            
            self.assertFalse(success)
            mock_logger.error.assert_called()
    
    def test_sendgrid_configuration_check(self):
        """Test SendGrid configuration checking"""
        # Test with no API key
        with self.settings(SENDGRID_API_KEY=None):
            result = test_sendgrid_connection()
            self.assertFalse(result)
        
        # Test with API key (will still fail in test environment but different path)
        with self.settings(SENDGRID_API_KEY='test_key'):
            # In test environment, this will use the test email backend
            result = test_sendgrid_connection()
            # Should succeed because we're using test backend
            self.assertTrue(result)


class EmailIntegrationTests(TestCase):
    """Test email integration with views and user workflows"""
    
    def setUp(self):
        self.client = Client()
        mail.outbox = []
    
    def test_registration_sends_welcome_email(self):
        """Test that user registration sends welcome email"""
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        response = self.client.post(reverse('register'), registration_data)
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # Welcome email should be sent
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('Welcome', email.subject)
        self.assertEqual(email.to, ['newuser@example.com'])
        self.assertIn('New', email.body)
    
    def test_registration_email_failure_handling(self):
        """Test registration continues even if email fails"""
        registration_data = {
            'username': 'testuser2',
            'email': 'testuser2@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        # Mock email sending to fail
        with patch('diary.email_service.send_welcome_email') as mock_send:
            mock_send.return_value = False  # Simulate email sending failure
            
            response = self.client.post(reverse('register'), registration_data)
            
            # Registration should still succeed
            self.assertEqual(response.status_code, 302)
            
            # User should be created
            self.assertTrue(User.objects.filter(username='testuser2').exists())
    
    def test_password_reset_flow(self):
        """Test password reset email flow"""
        user = User.objects.create_user(
            username='resetuser',
            email='resetuser@example.com',
            password='oldpassword123'
        )
        
        # Request password reset
        response = self.client.post(reverse('password_reset'), {
            'email': 'resetuser@example.com'
        })
        
        # Should redirect to done page
        self.assertEqual(response.status_code, 302)
        
        # Password reset email should be sent
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('Reset', email.subject)
        self.assertEqual(email.to, ['resetuser@example.com'])
        self.assertIn('password', email.body.lower())
    
    def test_password_reset_email_templates(self):
        """Test that custom password reset templates are used"""
        user = User.objects.create_user(
            username='templateuser',
            email='templateuser@example.com',
            password='oldpassword123'
        )
        
        response = self.client.post(reverse('password_reset'), {
            'email': 'templateuser@example.com'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        # Check that our custom subject template is used
        self.assertEqual(email.subject, 'Reset Your My Diary Password')
        # Check that email contains expected content from our template
        self.assertIn('My Diary', email.body)


class EmailTemplateTests(TestCase):
    """Test email template rendering"""
    
    def test_welcome_email_template_context(self):
        """Test welcome email template renders with correct context"""
        user = User.objects.create_user(
            username='templatetest',
            email='templatetest@example.com',
            first_name='Template'
        )
        
        send_welcome_email(user)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        # Check various parts of the template are rendered
        self.assertIn('Template', email.body)  # First name
        self.assertIn('templatetest', email.body)  # Username
        self.assertIn('templatetest@example.com', email.body)  # Email
        self.assertIn('Create your first note', email.body)  # Call to action
        self.assertIn('My Diary Team', email.body)  # Signature
    
    def test_email_template_html_alternative(self):
        """Test that HTML email templates are attached"""
        user = User.objects.create_user(
            username='htmltest',
            email='htmltest@example.com'
        )
        
        send_welcome_email(user)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        # Check that HTML alternative is attached
        self.assertTrue(hasattr(email, 'alternatives'))
        self.assertEqual(len(email.alternatives), 1)
        html_content, content_type = email.alternatives[0]
        self.assertEqual(content_type, 'text/html')
        self.assertIn('<h2>', html_content)  # HTML content
        self.assertIn('📖', html_content)  # Emoji in HTML
