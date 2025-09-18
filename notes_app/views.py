from django.shortcuts import HttpResponse, render


def note_list(request):
    return HttpResponse("Welcome to notes list")


def note_detail(request, note_id):
    return HttpResponse(f"Welcome to note detail {note_id}")


def note_edit(request, note_id):
    return HttpResponse(f"Welcome to note edit {note_id}")


def note_delete(request, note_id):
    return HttpResponse(f"Welcome to note delete {note_id}")
