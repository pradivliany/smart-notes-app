from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index_view, name="welcome"),
    path("admin/", admin.site.urls),
    path("users/", include("users_app.urls")),
    path("notes/", include("notes_app.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
