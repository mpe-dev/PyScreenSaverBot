from __future__ import annotations

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("telegram/", include("ingestion_app.urls")),
    path("", include("screensaver_app.urls")),
    # Serve media files via Django (no NGINX in this deployment).
    # If NGINX is added later, remove this pattern and let NGINX handle /media/.
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
