from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import WorkerForm
from .models import Worker


def is_szef(user):
    return user.is_superuser


@login_required
def home(request):
    return render(request, "home.html")


@login_required
@user_passes_test(is_szef)
@require_http_methods(["GET", "POST"])
def worker_management(request):
    pass
