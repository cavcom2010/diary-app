# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based diary/note-taking application with user authentication and image upload capabilities. The application allows users to create personal notes with images, manage privacy settings, and optionally share notes publicly.

## Key Architecture Components

### Core Django Structure
- **Project name**: `django_project` 
- **Main app**: `diary`
- **Django version**: 5.2.5
- **Database**: SQLite3 (development)
- **Python management**: Virtual environment in `.venv/`

### Models Architecture
The application centers around two main models:

**Note Model** (`diary/models.py:7`):
- User-owned notes with title, content, and timestamps
- Privacy controls (`is_public`, `is_draft`)
- Date-based URL routing using creation date
- Related to Django's built-in User model via ForeignKey

**NoteImage Model** (`diary/models.py:39`):
- One-to-many relationship with Notes
- Image uploads stored in `media/note_images/%Y/%m/%d/`
- Optional captions for images

### Views and URL Structure
The application uses Django's class-based views:
- **Authentication**: Built-in Django auth with custom registration
- **CRUD Operations**: Full Create, Read, Update, Delete for notes
- **Access Control**: LoginRequiredMixin and UserPassesTestMixin for security
- **URL Pattern**: Notes use date-based URLs: `/note/YYYY/MM/DD/PK/`

### Authentication System
- Custom registration form with email field (`diary/forms.py:8`)
- Login/logout handled by Django's built-in auth views
- Redirects: Login → note list, Logout → login page
- User registration automatically logs in new users

### Media and Static Files
- **Static files**: Collected in `staticfiles/` directory
- **Media files**: User uploads stored in `media/` directory  
- **Development**: Both served by Django when `DEBUG=True`

## Development Commands

### Basic Django Operations
```bash
# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files (for production)
python manage.py collectstatic
```

### Virtual Environment
```bash
# Activate virtual environment
source .venv/bin/activate

# Deactivate
deactivate
```

## Key Configuration

### Settings (`django_project/settings.py`)
- **Secret Key**: Uses insecure development key (line 24)
- **Debug Mode**: Enabled for development (line 27)
- **Media Settings**: MEDIA_ROOT and MEDIA_URL configured for file uploads
- **Templates**: Located in project-level `templates/` directory
- **Authentication**: Login redirects and email backend configured

### URL Configuration
- **Main URLs**: `django_project/urls.py` includes diary app and auth URLs
- **Diary URLs**: `diary/urls.py` defines date-based note routing
- **Auth URLs**: Uses Django's built-in authentication URLs at `/accounts/`

## Database Schema

The application uses Django's default SQLite database with two custom tables:
- `diary_note`: Main note storage with user relationships
- `diary_noteimage`: Image attachments linked to notes

## Template Structure

Templates are organized in `templates/` with:
- `base.html`: Main template with Bootstrap styling
- `diary/`: App-specific templates for CRUD operations
- `registration/`: Authentication templates (login, register)

## Security Considerations

- User isolation: Notes are filtered by author in all views
- Permission checks: Users can only edit/delete their own notes
- CSRF protection: Enabled by default
- Media file serving: Only enabled in development mode