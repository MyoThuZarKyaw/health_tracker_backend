from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkoutViewSet, MealViewSet, WorkoutChoicesView, MealChoicesView

router = DefaultRouter()
router.register(r"workouts", WorkoutViewSet)
router.register(r"meals", MealViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("workout-choices/", WorkoutChoicesView.as_view(), name="workout-choices"),
    path("meal-choices/", MealChoicesView.as_view(), name="meal-choices"),
]
