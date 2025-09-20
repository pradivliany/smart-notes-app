from django.urls import path

from . import views

app_name = "notes_app"

urlpatterns = [
    path("", views.note_list, name="note_list"),
    path("<int:note_id>/", views.note_detail, name="note_detail"),
    path("<int:note_id>/edit/", views.note_edit, name="note_edit"),
    path("<int:note_id>/delete/", views.note_delete, name="note_delete"),
    path("tags/", views.tag_list, name="tag_list"),
    path("tags/create/", views.tag_create, name="tag_create"),
    path("tags/<int:tag_id>/delete/", views.tag_delete, name="tag_delete"),
]
