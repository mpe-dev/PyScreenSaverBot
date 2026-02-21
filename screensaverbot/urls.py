from __future__ import annotations

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("telegram/", include("ingestion_app.urls")),
    path("", include("screensaver_app.urls")),
]

# Serve media files in development (DEBUG=True).
# In production, delegate to NGINX or the Docker bind-mount.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
