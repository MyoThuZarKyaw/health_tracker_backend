from django.db import models
from django.conf import settings


class Workout(models.Model):
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    WORKOUT_TYPE_CHOICES = [
        ("cardio", "Cardio"),
        ("strength", "Strength"),
        ("yoga", "Yoga"),
        ("pilates", "Pilates"),
        ("sports", "Sports"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workouts"
    )
    date = models.DateField()
    workout_type = models.CharField(max_length=20, choices=WORKOUT_TYPE_CHOICES)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    calories_burned = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        unique_together = [
            "user",
            "date",
            "workout_type",
            "created_at",
        ]  # Prevent duplicate entries

    def __str__(self):
        return f"{self.user.email} - {self.workout_type} on {self.date}"
