# diary/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import Note, NoteImage

class CustomUserCreationform(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all form fields.
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user
    
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
    extra=1,  # Show 1 empty form initially
    can_delete=True
)
