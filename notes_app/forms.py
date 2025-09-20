from django.forms import CharField, ModelForm, TextInput

from .models import Tag


class TagForm(ModelForm):
    name = CharField(min_length=3, max_length=25, required=True, widget=TextInput())

    class Meta:
        model = Tag
        fields = ["name"]
