# diary/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Note, NoteImage
from .forms import NoteForm, NoteImageFormSet

class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = 'diary/note_list.html'
    context_object_name = 'notes'
    paginate_by = 10
    
    def get_queryset(self):
        return Note.objects.filter(author=self.request.user)

class NoteDetailView(DetailView):
    model = Note
    template_name = 'diary/note_detail.html'
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            # Authenticated users can see their own notes (public or private)
            return Note.objects.filter(author=self.request.user)
        else:
            # Anonymous users can only see public notes
            return Note.objects.filter(is_public=True)

class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    form_class = NoteForm
    template_name = 'diary/note_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = NoteImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['image_formset'] = NoteImageFormSet()
        return context
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if form.is_valid() and image_formset.is_valid():
            self.object = form.save()
            image_formset.instance = self.object
            image_formset.save()
            messages.success(self.request, 'Note created successfully!')
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

class NoteUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Note
    form_class = NoteForm
    template_name = 'diary/note_form.html'
    
    def test_func(self):
        note = self.get_object()
        return self.request.user == note.author
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = NoteImageFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            context['image_formset'] = NoteImageFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if form.is_valid() and image_formset.is_valid():
            self.object = form.save()
            image_formset.save()
            messages.success(self.request, 'Note updated successfully!')
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

class NoteDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Note
    template_name = 'diary/note_confirm_delete.html'
    success_url = reverse_lazy('note_list')
    
    def test_func(self):
        note = self.get_object()
        return self.request.user == note.author

class PublicNotesView(ListView):
    model = Note
    template_name = 'diary/public_notes.html'
    context_object_name = 'notes'
    paginate_by = 10
    
    def get_queryset(self):
        return Note.objects.filter(is_public=True, is_draft=False)
