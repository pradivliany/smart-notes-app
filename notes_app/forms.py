from django.forms import CharField, ModelForm, TextInput
from django.forms.widgets import Textarea

from .models import Note, Tag


class TagForm(ModelForm):
    name = CharField(
        min_length=3,
        max_length=25,
        required=True,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Tag name"}),
    )

    class Meta:
        model = Tag
        fields = ["name"]


class NoteForm(ModelForm):
    name = CharField(
        min_length=4,
        max_length=50,
        required=True,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Note name"}),
    )
    description = CharField(
        min_length=4,
        max_length=150,
        required=True,
        widget=Textarea(
            attrs={"class": "form-control", "placeholder": "Description", "rows": 5}
        ),
    )

    class Meta:
        model = Note
        fields = ["name", "description"]
        exclude = ["tags"]
