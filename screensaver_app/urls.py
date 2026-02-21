from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/previews", views.api_previews, name="api_previews"),
]
