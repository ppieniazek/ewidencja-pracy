from django.urls import path

from . import views

urlpatterns = [
    # main page
    path("", views.home, name="home"),
    path("workers/", views.worker_management, name="worker_management"),
]
