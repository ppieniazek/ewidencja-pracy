import calendar
from datetime import date, timedelta

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


def _get_timesheet_context(user, target_date: date):
    context = {}
    polish_months = [
        (1, "Styczeń"),
        (2, "Luty"),
        (3, "Marzec"),
        (4, "Kwiecień"),
        (5, "Maj"),
        (6, "Czerwiec"),
        (7, "Lipiec"),
        (8, "Sierpień"),
        (9, "Wrzesień"),
        (10, "Październik"),
        (11, "Listopad"),
        (12, "Grudzień"),
    ]

    workers = user.brigade.workers.all().order_by("last_name", "first_name")
    timesheet_entries = TimeSheet.objects.filter(
        worker__in=workers, date__year=target_date.year, date__month=target_date.month
    )

    hours_map = {}
    for entry in timesheet_entries:
        if entry.worker.id not in hours_map:
            hours_map[entry.worker.id] = {}
        hours_map[entry.worker.id][entry.date.day] = entry.hours_worked

    num_days = calendar.monthrange(target_date.year, target_date.month)[1]

    # Prev and next months
    first_day_of_month = target_date.replace(day=1)
    prev_month_date = first_day_of_month - timedelta(days=1)
    next_month_date = first_day_of_month + timedelta(days=num_days)

    context.update(
        {
            "workers": workers,
            "days": list(range(1, num_days + 1)),
            "hours_map": hours_map,
            "current_month": target_date.month,
            "current_month_name": polish_months[target_date.month - 1][1],
            "current_year": target_date.year,
            "prev_month": prev_month_date.month,
            "prev_year": prev_month_date.year,
            "next_month": next_month_date.month,
            "next_year": next_month_date.year,
            "months_list": polish_months,
        }
    )
    return context


@login_required
def dashboard(request, year=None, month=None):
    context = {}
    user = request.user

    if user.role == "SZEF":
        # TODO szef
        context["brigades"] = [
            {"id": 1, "name": "Brygada A (Test)"},
            {"id": 2, "name": "Brygada B (Przykładowa)"},
        ]
        pass

    if user.role == "BRYGADZISTA" and user.brigade:
        target_date = None
        if year and month:
            target_date = date(year, month, 1)
        elif request.GET.get("year") and request.GET.get("month"):
            q_year = request.GET.get("year")
            q_month = request.GET.get("month")
            if q_year.isdigit() and q_month.isdigit():
                target_date = date(int(q_year), int(q_month), 1)
        if target_date is None:
            target_date = date.today()

        context.update(_get_timesheet_context(user, target_date))

    if request.htmx:
        return render(request, "partials/timesheet_wrapper.html", context)
    else:
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
def get_bulk_edit_form(request, day, year, month):
    context = {"day": day, "year": year, "month": month}
    return render(request, "partials/bulk_edit_form.html", context)


@login_required
def bulk_save_hours(request, year, month):
    if not (request.method == "POST" and request.htmx):
        return HttpResponse(status=400)

    user = request.user
    if not (user.role == "BRYGADZISTA" and user.brigade):
        return HttpResponse("Brak brygady lub roli", status=403)

    day = int(request.POST.get("day"))
    hours_str = request.POST.get(f"hours_{day}")

    entry_date = date(year, month, day)

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

    target_date = date(year, month, 1)
    context = _get_timesheet_context(user, target_date)
    context["day"] = day

    return render(request, "partials/bulk_update_response.html", context)

    # TODO placeholder views


@login_required
def szef_dashboard_view(request):
    """
    Renders the main navigation dashboard for the Szef.
    """
    dummy_context = {
        "brigades": [
            {"id": 1, "name": "Brygada A (Test)"},
            {"id": 2, "name": "Brygada B (Przykładowa)"},
        ]
    }
    return render(request, "szef/szef_dashboard.html", dummy_context)


@login_required
def manage_workers_view(request):
    """Placeholder view for Szef to manage all workers."""
    dummy_context = {
        "workers": [
            {"id": 1, "name": "Jan Kowalski", "rate": 25.00},
            {"id": 2, "name": "Adam Nowak", "rate": 30.00},
            {"id": 3, "name": "Piotr Zając (Test)", "rate": 28.50},
        ]
    }
    return render(request, "szef/manage_workers.html", dummy_context)


@login_required
def manage_foremen_view(request):
    """Placeholder view for Szef to manage foremen and brigades."""
    dummy_context = {
        "foremen": [
            {"id": 1, "name": "Marek Brygadzista", "brigade": "Brygada A (Test)"},
            {
                "id": 2,
                "name": "Krzysztof Kierownik",
                "brigade": "Brygada B (Przykładowa)",
            },
        ]
    }
    return render(request, "szef/manage_foremen.html", dummy_context)


@login_required
def assign_workers_view(request, brigade_id):
    """Placeholder view for Szef to assign workers to a brigade."""
    dummy_context = {
        "brigade_name": f"Brygada A (Test) - ID: {brigade_id}",
        "assigned_workers": [{"name": "Jan Kowalski"}, {"name": "Adam Nowak"}],
        "unassigned_workers": [{"name": "Piotr Zając (Test)"}],
    }
    return render(request, "szef/assign_workers.html", dummy_context)


@login_required
def financial_ledger_view(request):
    """Placeholder view for Szef to see all financials."""
    dummy_context = {
        "unpaid_items": [
            {
                "type": "Zaliczka",
                "date": "2025-06-12",
                "details": "dla Jan Kowalski",
                "amount": 200.00,
            },
            {
                "type": "Wydatek",
                "date": "2025-06-10",
                "details": "Paliwo do piły (Marek B.)",
                "amount": 150.00,
            },
        ],
        "paid_items": [
            {
                "type": "Wydatek",
                "date": "2025-06-05",
                "details": "Rękawice robocze (Marek B.)",
                "amount": 80.50,
            },
        ],
    }
    return render(request, "szef/financial_ledger.html", dummy_context)


@login_required
def report_brigade_summary_view(request):
    """Placeholder view for brigade summary report."""
    return render(request, "szef/report_brigade_summary.html")


@login_required
def report_worker_payroll_view(request):
    """Placeholder view for individual worker payroll report."""
    return render(request, "szef/report_worker_payroll.html")
