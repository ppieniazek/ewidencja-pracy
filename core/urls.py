from django.urls import path

from . import views

urlpatterns = [
    path("", views.root_redirect, name="root_redirect"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "dashboard/<int:year>/<int:month>/", views.dashboard, name="dashboard_by_date"
    ),
    # HTMX
    path(
        "get-edit-form/<int:worker_id>/<int:year>/<int:month>/<int:day>/",
        views.get_edit_form,
        name="get_edit_form",
    ),
    path("save-hours/<int:worker_id>/", views.save_hours, name="save_hours"),
    path(
        "bulk-save-hours/<int:year>/<int:month>",
        views.bulk_save_hours,
        name="bulk_save_hours",
    ),
    path(
        "get-bulk-edit-form/<int:year>/<int:month>/<int:day>/",
        views.get_bulk_edit_form,
        name="get_bulk_edit_form",
    ),
]
