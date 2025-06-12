import calendar
from datetime import date

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.models import TimeSheet, Worker


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    else:
        return redirect("login")


def custom_logout_view(request):
    logout(request)

    response = HttpResponse()
    response["HX-Redirect"] = reverse("login")
    return response


def _get_timesheet_context(user):
    context = {}
    today = date.today()
    month_translation = {
        "January": "Styczeń",
        "February": "Luty",
        "March": "Marzec",
        "April": "Kwiecień",
        "May": "Maj",
        "June": "Czerwiec",
        "July": "Lipiec",
        "August": "Sierpień",
        "September": "Wrzesień",
        "October": "Październik",
        "November": "Listopad",
        "December": "Grudzień",
    }

    workers = user.brigade.workers.all().order_by("last_name", "first_name")
    timesheet_entries = TimeSheet.objects.filter(
        worker__in=workers, date__year=today.year, date__month=today.month
    )

    hours_map = {}
    for entry in timesheet_entries:
        if entry.worker.id not in hours_map:
            hours_map[entry.worker.id] = {}
        hours_map[entry.worker.id][entry.date.day] = entry.hours_worked

    num_days = calendar.monthrange(today.year, today.month)[1]

    context.update(
        {
            "workers": workers,
            "days": list(range(1, num_days + 1)),
            "hours_map": hours_map,
            "current_month": today.month,
            "current_year": today.year,
            "current_month_name": month_translation.get(today.strftime("%B")),
        }
    )
    return context


@login_required
def dashboard(request):
    context = {}
    user = request.user

    if user.role == "BRYGADZISTA" and user.brigade:
        context.update(_get_timesheet_context(user))

    return render(request, "core/dashboard.html", context)


@login_required
def get_edit_form(request, worker_id, year, month, day):
    worker = get_object_or_404(Worker, pk=worker_id)
    current_date = date(year, month, day)

    timesheet_entry = TimeSheet.objects.filter(worker=worker, date=current_date).first()
    hours = timesheet_entry.hours_worked if timesheet_entry else ""

    context = {"worker": worker, "date_str": current_date.isoformat(), "hours": hours}

    return render(request, "partials/edit_hours_form.html", context)


@login_required
def save_hours(request, worker_id):
    if request.method == "POST":
        worker = get_object_or_404(Worker, pk=worker_id)
        entry_date_str = request.POST.get("date")
        hours_str = request.POST.get("hours")

        entry_date = date.fromisoformat(entry_date_str)

        if hours_str and hours_str.strip():
            try:
                hours = int(hours_str)
                obj, created = TimeSheet.objects.update_or_create(
                    worker=worker, date=entry_date, defaults={"hours_worked": hours}
                )
            except (ValueError, TypeError):
                obj = TimeSheet.objects.filter(worker=worker, date=entry_date).first()
        else:
            TimeSheet.objects.filter(worker=worker, date=entry_date).delete()
            obj = None

        context = {
            "worker": worker,
            "day": entry_date.day,
            "current_month": entry_date.month,
            "current_year": entry_date.year,
            "hours": obj.hours_worked if obj and obj.hours_worked > 0 else "-",
        }
        return render(request, "partials/timesheet_cell.html", context)

    return HttpResponse(status=405)


@login_required
def get_bulk_edit_form(request, day):
    context = {"day": day}
    return render(request, "partials/bulk_edit_form.html", context)


@login_required
def bulk_save_hours(request):
    if not (request.method == "POST" and request.htmx):
        return HttpResponse(status=400)

    user = request.user
    if not (user.role == "BRYGADZISTA" and user.brigade):
        return HttpResponse("Brak brygady lub roli", status=403)

    day = int(request.POST.get("day"))
    hours_str = request.POST.get(f"hours_{day}")

    today = date.today()
    entry_date = date(today.year, today.month, day)

    if hours_str and hours_str.strip():
        try:
            hours_to_apply = int(hours_str)
            if hours_to_apply >= 0:
                brigade = user.brigade

                workers_without_entry = brigade.workers.exclude(
                    timesheet__date=entry_date
                )

                new_entries = [
                    TimeSheet(
                        worker=worker, date=entry_date, hours_worked=hours_to_apply
                    )
                    for worker in workers_without_entry
                ]

                if new_entries:
                    TimeSheet.objects.bulk_create(new_entries, ignore_conflicts=True)

        except (ValueError, TypeError):
            pass

    context = _get_timesheet_context(user)
    context["day"] = day

    return render(request, "partials/bulk_update_response.html", context)
