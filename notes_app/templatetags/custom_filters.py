from django import template

register = template.Library()


def extract_tags(note_tags):
    return [tag.name for tag in note_tags.all() if len(tag.name) <= 10][:5]


register.filter("extract_tags", extract_tags)
