from django.urls import path

from . import views

urlpatterns = [
    path("", views.root_redirect, name="root_redirect"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # HTMX
    path(
        "get-edit-form/<int:worker_id>/<int:year>/<int:month>/<int:day>/",
        views.get_edit_form,
        name="get_edit_form",
    ),
    path("save-hours/<int:worker_id>/", views.save_hours, name="save_hours"),
    path("bulk-save-hours/", views.bulk_save_hours, name="bulk_save_hours"),
    path(
        "get-bulk-edit-form/<int:day>/",
        views.get_bulk_edit_form,
        name="get_bulk_edit_form",
    ),
]
