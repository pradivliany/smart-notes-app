from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import profile_confirmed_required
from .forms import NoteForm, NoteTodoForm, TagForm
from .models import Note, Tag

# TAGS


@login_required
def tag_list(request: HttpRequest) -> HttpResponse:
    """
    Displays all tags created by the current user.
    """
    tags = Tag.objects.filter(user=request.user)
    return render(request, "notes_app/tag_list.html", {"tags": tags})


@login_required
@profile_confirmed_required
def tag_create(request: HttpRequest) -> HttpResponse:
    """
    Handles the creation of a new Tag object.

    The view requires the user to be logged in and to have a confirmed profile.

    On a POST request:
    1. Validates the submitted data using TagForm.
    2. Associates the new Tag with the current user.
    3. Handles the 'save' and 'save_and_add' actions, redirecting accordingly.
    4. Catches IntegrityError if the user already has a tag with the same name.

    On a GET request:
    Renders an empty Tag creation form.
    """
    form: TagForm

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
            except IntegrityError:
                form.add_error("name", "You already have a tag with this name.")
                return render(request, "notes_app/tag_create.html", {"form": form})

    else:
        form = TagForm()

    return render(request, "notes_app/tag_create.html", {"form": form})


@login_required
def tag_delete(request: HttpRequest, tag_id: int) -> HttpResponse:
    """
    Deletes a tag belonging to the current user. Only accepts POST requests.
    """
    if request.method == "POST":
        tag = get_object_or_404(Tag, pk=tag_id, user=request.user)
        if Note.objects.filter(tags=tag).exists():
            messages.error(
                request, "Cannot delete tag: it's used by at least one note."
            )
            return redirect(to="notes_app:tag_list")

        tag.delete()
        messages.success(request, "Tag was deleted")
        return redirect(to="notes_app:tag_list")

    return redirect(to="notes_app:tag_list")


# NOTES


@login_required
def note_list(request: HttpRequest) -> HttpResponse:
    """
    Renders the list of notes for the authenticated user, including pagination.

    Fetches all notes owned by the current user, orders them by ID (newest first),
    and paginates the results, showing 9 notes per page.
    """
    all_notes = Note.objects.filter(user=request.user).order_by("-id")

    paginator = Paginator(all_notes, 9)
    page_number = request.GET.get("page", 1)
    notes = paginator.get_page(page_number)

    return render(request, "notes_app/note_list.html", {"notes": notes})


@login_required
def note_detail(request: HttpRequest, note_id: int) -> HttpResponse:
    """
    Renders the detailed view of a specific note.

    Fetches the Note object by its ID, ensuring it belongs to the currently
    authenticated user. Raises Http404 if the note is not found or does not
    belong to the user.
    """
    note = get_object_or_404(Note, pk=note_id, user=request.user)
    return render(request, "notes_app/note_detail.html", {"note": note})


@login_required
def note_toggle_status(request: HttpRequest, note_id: int) -> HttpResponse:
    """
    Toggles the 'done' status of a specific note.

    This view only accepts POST requests for security.
    If the request method is POST:
    1. Flips the 'done' status.
    2. If the note was a 'To_do' task, it automatically removes the 'is_todo' status
       and clears the 'deadline' to maintain data consistency.
    3. Redirects to the note list with a success message.

    Any other methods (GET, etc.) are safely redirected to the note detail page.
    """
    note = get_object_or_404(Note, pk=note_id, user=request.user)

    if request.method == "POST":
        note.done = not note.done
        if note.is_todo:
            note.is_todo = False
            note.deadline = None
        note.save()
        messages.success(request, "Note status was changed")
        return redirect(to="notes_app:note_list")

    messages.info(request, "Status change allowed only via POST")
    return redirect(to="notes_app:note_detail", note_id=note.pk)


@login_required
@profile_confirmed_required
def note_create(request: HttpRequest) -> HttpResponse:
    """
    Handles the creation of a new Note object for the authenticated user with confirmed profile.

    CRITICAL LOGIC: The view requires the user to have at least one Tag
    before allowing the creation of a note. If no tags exist, the user is redirected
    to the tag creation page with a warning message.

    On POST:
    1. Validates the input data using NoteForm.
    2. Associates the new Note with the current user and selected Tags.
    3. Redirects to the notes list with a success message.

    On GET:
    Renders the Note creation form.
    """
    tags = Tag.objects.filter(user=request.user)

    if not tags.exists():
        messages.warning(
            request,
            "You must create at least one tag before creating a note. Please create a tag now.",
        )
        return redirect(to="notes_app:tag_create")

    form: NoteForm

    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            new_note = form.save(commit=False)
            choice_tags = Tag.objects.filter(
                name__in=request.POST.getlist("tags"), user=request.user
            )
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
def note_edit(request: HttpRequest, note_id: int) -> HttpResponse:
    """
    Handles the editing of an existing Note object for the authenticated user.

    Fetches the Note instance by ID, ensuring it belongs to the current user (security).

    On POST:
    1. Validates input data using NoteForm, bound to the existing Note instance.
    2. Saves the Note changes.
    3. Updates the Note's associated Tags. ( + Tags are filtered by ownership).
    4. Redirects to the notes list with a success message.

    On GET:
    Renders the Note edit form, pre-filled with the Note's current data.
    """
    note = get_object_or_404(Note, pk=note_id, user=request.user)
    tags = Tag.objects.filter(user=request.user)

    form: NoteForm

    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            choice_tags = Tag.objects.filter(
                name__in=request.POST.getlist("tags"), user=request.user
            )
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
def note_delete(request: HttpRequest, note_id: int) -> HttpResponse:
    """
    Handles deletion of a Note. Requires POST method and user to be authenticated.

    On POST: Deletes the user's Note and redirects to the list.
    On GET: Safely redirects to the note list.
    """
    if request.method == "POST":
        note = get_object_or_404(Note, pk=note_id, user=request.user)
        note.delete()
        messages.success(request, "Note was deleted!")
        return redirect(to="notes_app:note_list")

    return redirect(to="notes_app:note_list")


@login_required
def note_toggle_todo(request: HttpRequest, note_id: int) -> HttpResponse:
    """
    Handles the To-Do toggle for a note.

    If is_todo=False (GET): Redirects to the deadline setting.
    If is_todo=True (POST): Safely disables To-Do mode by clearing the deadline.
    """
    note = get_object_or_404(Note, pk=note_id, user=request.user)

    if not note.is_todo:
        return redirect(to="notes_app:note_set_deadline", note_id=note.pk)

    if request.method == "POST":
        note.deadline = None
        note.is_todo = False
        note.save()
        messages.success(request, "Note is no longer in To-Do mode")

    else:
        messages.error(request, "ToDo mode can be disabled only via POST request.")

    return redirect(to="notes_app:note_list")


@login_required
def note_set_deadline(request: HttpRequest, note_id: int) -> HttpResponse:
    """
    Handles the form for setting a deadline, activating To_Do mode (is_todo=True),
    and unmarking the note as done (done=False) if necessary.

    GET: Displays the NoteTodoForm for setting the deadline.
    POST: Processes the form data. Validates that the chosen deadline is in the future
            relative to the current local time. Upon successful save:
          - Sets note.is_todo = True.
          - Sets note.done = False.
          - Redirects to the note list.
    """
    note = get_object_or_404(Note, pk=note_id, user=request.user)
    curr_time = timezone.localtime()

    form: NoteTodoForm

    if request.method == "POST":
        form = NoteTodoForm(request.POST, instance=note)
        if form.is_valid():
            if form.cleaned_data["deadline"] < curr_time:
                messages.warning(request, "Choose datetime in the future.")
                return redirect(to="notes_app:note_set_deadline", note_id=note.pk)
            note = form.save(commit=False)
            note.is_todo = True
            note.done = False
            note.save()
            messages.success(
                request, f'"{note.name}" is now a To-Do with deadline set!'
            )
            return redirect(to="notes_app:note_list")
        else:
            messages.error(request, "Please choose a valid date and time.")
    else:
        form = NoteTodoForm(instance=note)
    return render(request, "notes_app/set_deadline.html", {"form": form, "note": note})
