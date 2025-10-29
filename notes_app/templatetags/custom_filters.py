from django import template

register = template.Library()


def extract_tags(note_tags, limit: int = 5) -> list[str]:
    """
    Extracts, sorts and filters a list of unique tag names.

    """
    unique_tags: list[str] = sorted(set(tag.name for tag in note_tags.all()))
    if limit == -1:
        return list(unique_tags)
    else:
        return list(name for name in unique_tags if len(name) <= 10)[:limit]


register.filter("extract_tags", extract_tags)
