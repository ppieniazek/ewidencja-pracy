from django.urls import path

from . import views

urlpatterns = [
    path("", views.root_redirect, name="root_redirect"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
