from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkoutViewSet, WorkoutChoicesView

router = DefaultRouter()
router.register(r"workouts", WorkoutViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("workout-choices/", WorkoutChoicesView.as_view(), name="workout-choices"),
]
