import calendar
from datetime import date

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse


# Create your views here.
def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    else:
        return redirect("login")


@login_required
def dashboard(request):
    context = {}
    user = request.user

    if user.role == "BRYGADZISTA" and user.brigade:
        workers = user.brigade.workers.all()
        context["workers"] = workers

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

        today = date.today()
        num_days = calendar.monthrange(today.year, today.month)[1]
        days = [i for i in range(1, num_days + 1)]
        context["days"] = days
        context["current_month_name"] = month_translation.get(today.strftime("%B"))
        context["current_year"] = today.year

    return render(request, "core/dashboard.html", context)


def custom_logout_view(request):
    logout(request)

    response = HttpResponse()
    response["HX-Redirect"] = reverse("login")
    return response
