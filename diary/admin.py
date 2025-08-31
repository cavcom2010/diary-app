# diary/admin.py
from django.contrib import admin
from .models import Note, NoteImage

class NoteImageInline(admin.TabularInline):
    model = NoteImage
    extra = 1

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'date_created', 'is_public', 'is_draft']
    list_filter = ['is_public', 'is_draft', 'date_created', 'author']
    search_fields = ['title', 'content']
    inlines = [NoteImageInline]
    
@admin.register(NoteImage)
class NoteImageAdmin(admin.ModelAdmin):
    list_display = ['note', 'caption', 'uploaded_at']
