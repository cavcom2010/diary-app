# diary/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class Note(models.Model):
    # Connect each note to a user
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    
    # Basic note fields
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Date fields
    date_created = models.DateTimeField(default=timezone.now)
    date_modified = models.DateTimeField(auto_now=True)
    
    # Privacy and draft settings
    is_public = models.BooleanField(default=False)
    # is_private = models.BooleanField(default=False)
    # is_unlisted = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date_created']  # Most recent first
    
    def __str__(self):
        return f"{self.title} - {self.date_created.strftime('%Y-%m-%d')}"
    
    def get_absolute_url(self):
        return reverse('note_detail', kwargs={
            'year': self.date_created.year,
            'month': self.date_created.month,
            'day': self.date_created.day,
            'pk': self.pk
        })

class NoteImage(models.Model):
    """Separate model for unlimited images per note"""
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='note_images/%Y/%m/%d/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"Image for {self.note.title}"
