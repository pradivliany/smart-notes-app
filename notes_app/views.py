from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NoteForm, TagForm
from .models import Note, Tag


# ------------------------
# TAGS
# ------------------------
@login_required
def tag_list(request):
    tags = Tag.objects.filter(user=request.user)
    return render(request, "notes_app/tag_list.html", {"tags": tags})


@login_required
def tag_create(request):
    if request.method == "POST":
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.user = request.user
            try:
                tag.save()
                if "save" in request.POST:
                    messages.success(request, "Tag was successfully created")
                    return redirect(to="notes_app:tag_list")
                elif "save_and_add" in request.POST:
                    messages.success(
                        request, "Tag was saved. Now you can add another one"
                    )
                    return redirect(to="notes_app:tag_create")
            except IntegrityError as err:
                form.add_error("name", "You already have a tag with this name.")
                return render(request, "notes_app/tag_create.html", {"form": form})

    else:
        form = TagForm()  # request.method == "GET"

    return render(request, "notes_app/tag_create.html", {"form": form})


@login_required
def tag_delete(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id, user=request.user)
    tag.delete()
    messages.success(request, "Tag was deleted")
    return redirect(to="notes_app:tag_list")


# ------------------------
# NOTES
# ------------------------
@login_required
def note_list(request):
    notes = Note.objects.filter(user=request.user).order_by("-id")
    return render(request, "notes_app/note_list.html", {"notes": notes})


@login_required
def note_detail(request, note_id):
    note = get_object_or_404(Note, pk=note_id, user=request.user)
    return render(request, "notes_app/note_detail.html", {"note": note})


@login_required
def note_toggle_status(request, note_id):
    note = get_object_or_404(Note, pk=note_id, user=request.user)

    if request.method == "POST":
        note.done = not note.done
        note.save()
        messages.success(request, "Note status was changed")
        return redirect(to="notes_app:note_list")

    messages.info(request, "Status change allowed only via POST")
    return redirect(to="notes_app:note_detail", note_id=note.pk)


@login_required
def note_create(request):
    tags = Tag.objects.filter(user=request.user)

    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            new_note = form.save(commit=False)
            choice_tags = Tag.objects.filter(name__in=request.POST.getlist("tags"))
            new_note.user = request.user
            new_note.save()
            new_note.tags.set(choice_tags)
            messages.success(request, "Note was created!")
            return redirect(to="notes_app:note_list")
    else:
        form = NoteForm()

    return render(
        request,
        "notes_app/note_form.html",
        {"form": form, "tags": tags, "is_edit": False},
    )


@login_required
def note_edit(request, note_id):
    note = get_object_or_404(Note, pk=note_id, user=request.user)
    tags = Tag.objects.filter(user=request.user)

    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            choice_tags = Tag.objects.filter(name__in=request.POST.getlist("tags"))
            note.tags.set(choice_tags)
            messages.success(request, "Note was edited!")
            return redirect(to="notes_app:note_list")
    else:
        form = NoteForm(instance=note)

    return render(
        request,
        "notes_app/note_form.html",
        {"form": form, "tags": tags, "is_edit": True},
    )


@login_required
def note_delete(request, note_id):
    if request.method == "POST":
        note = get_object_or_404(Note, pk=note_id, user=request.user)
        note.delete()
        messages.success(request, "Note was deleted!")
        return redirect(to="notes_app:note_list")

    return redirect(to="notes_app:note_list")
