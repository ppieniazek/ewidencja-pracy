from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class Brigade(models.Model):
    """Reprezentuje zespół pracowników."""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Niestandardowy model użytkownika z rolami i brygadą."""

    class Role(models.TextChoices):
        SZEF = "SZEF", "Szef"
        BRYGADZISTA = "BRYGADZISTA", "Brygadzista"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.BRYGADZISTA
    )
    brigade = models.ForeignKey(
        Brigade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Brygada zarządzana przez tego brygadzistę",
    )


class Worker(models.Model):
    """Reprezentuje pracownika."""

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    brigade = models.ManyToManyField(Brigade, related_name="workers")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TimeSheet(models.Model):
    """Reprezentuje godziny przepracowane przez pracownika w danym dniu."""

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    date = models.DateField()
    hours_worked = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("worker", "date")
        ordering = ["date", "worker"]

    def __str__(self):
        return f"{self.worker} - {self.date}: {self.hours_worked} godz."
