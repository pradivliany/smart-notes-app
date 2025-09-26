from django.shortcuts import redirect, render


def index_view(request):
    if request.user.is_authenticated:
        return redirect(to="notes_app:note_list")

    return render(request, "welcome.html")
