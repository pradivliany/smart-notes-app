from django.contrib import admin

from .models import Note, Tag

admin.site.register(Tag)
admin.site.register(Note)
