# diary/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.NoteListView.as_view(), name='note_list'),
    path('note/new/', views.NoteCreateView.as_view(), name='note_create'),
    path('note/<int:year>/<int:month>/<int:day>/<int:pk>/', 
         views.NoteDetailView.as_view(), name='note_detail'),
    path('note/<int:year>/<int:month>/<int:day>/<int:pk>/edit/', 
         views.NoteUpdateView.as_view(), name='note_update'),
    path('note/<int:year>/<int:month>/<int:day>/<int:pk>/delete/', 
         views.NoteDeleteView.as_view(), name='note_delete'),
    path('public/', views.PublicNotesView.as_view(), name='public_notes'),
]
