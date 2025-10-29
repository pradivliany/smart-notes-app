from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render


def index_view(request: HttpRequest) -> HttpResponse:
    """
    Main entry point for the application.

    Redirects authenticated users to the note list, otherwise renders the welcome page.
    """
    if request.user.is_authenticated:
        return redirect(to="notes_app:note_list")

    return render(request, "welcome.html")
