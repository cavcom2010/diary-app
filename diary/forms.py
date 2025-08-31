# diary/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Note, NoteImage

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'is_public', 'is_draft']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter note title...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Write your note here...'
            }),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_draft': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class NoteImageForm(forms.ModelForm):
    class Meta:
        model = NoteImage
        fields = ['image', 'caption']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Image caption (optional)...'
            }),
        }

# Create a formset for handling multiple images
NoteImageFormSet = inlineformset_factory(
    Note, NoteImage,
    form=NoteImageForm,
    extra=3,  # Show 3 empty forms initially
    can_delete=True
)
