from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkoutViewSet,
    MealViewSet,
    StepsViewSet,
    WorkoutChoicesView,
    MealChoicesView,
    StepsChoicesView,
)

router = DefaultRouter()
router.register(r"workouts", WorkoutViewSet)
router.register(r"meals", MealViewSet)
router.register(r"steps", StepsViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("workout-choices/", WorkoutChoicesView.as_view(), name="workout-choices"),
    path("meal-choices/", MealChoicesView.as_view(), name="meal-choices"),
    path("steps-choices/", StepsChoicesView.as_view(), name="steps-choices"),
]
