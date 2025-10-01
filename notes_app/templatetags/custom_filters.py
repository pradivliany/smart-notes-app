from django import template

register = template.Library()


def extract_tags(note_tags, limit=5):
    unique_tags = sorted(set(tag.name for tag in note_tags.all()))
    if limit == -1:
        return list(unique_tags)
    else:
        return list(name for name in unique_tags if len(name) <= 10)[:limit]


register.filter("extract_tags", extract_tags)
