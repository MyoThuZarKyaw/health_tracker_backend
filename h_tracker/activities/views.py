from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Workout, Meal, Steps
from .serializers import WorkoutSerializer, MealSerializer, StepsSerializer


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class WorkoutViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["date", "workout_type", "status"]
    ordering_fields = ["date", "created_at", "duration", "calories_burned"]
    ordering = ["-date", "-created_at"]
    queryset = Workout.objects.all()  # Required for DRF router

    def get_queryset(self):
        """
        Return workouts for the current authenticated user only.
        """
        return Workout.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically set the user to the current authenticated user.
        """
        serializer.save(user=self.request.user)


class WorkoutChoicesView(APIView):
    """
    API view to return workout type and status choices for frontend use.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        workout_types = [
            {"value": choice[0], "label": choice[1]}
            for choice in Workout.WORKOUT_TYPE_CHOICES
        ]

        workout_statuses = [
            {"value": choice[0], "label": choice[1]}
            for choice in Workout.STATUS_CHOICES
        ]

        return Response(
            {"workout_types": workout_types, "workout_statuses": workout_statuses}
        )


class MealChoicesView(APIView):
    """
    API view to return meal type and status choices for frontend use.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        meal_types = [
            {"value": choice[0], "label": choice[1]}
            for choice in Meal.MEAL_TYPE_CHOICES
        ]

        meal_statuses = [
            {"value": choice[0], "label": choice[1]} for choice in Meal.STATUS_CHOICES
        ]

        return Response({"meal_types": meal_types, "meal_statuses": meal_statuses})


class StepsViewSet(viewsets.ModelViewSet):
    serializer_class = StepsSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["date", "status"]
    ordering_fields = ["date", "created_at", "total_steps"]
    ordering = ["-date", "-created_at"]
    queryset = Steps.objects.all()  # Required for DRF router

    def get_queryset(self):
        """
        Return steps for the current authenticated user only.
        """
        return Steps.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically set the user to the current authenticated user.
        """
        serializer.save(user=self.request.user)


class StepsChoicesView(APIView):
    """
    API view to return steps status choices for frontend use.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        steps_statuses = [
            {"value": choice[0], "label": choice[1]} for choice in Steps.STATUS_CHOICES
        ]

        return Response({"steps_statuses": steps_statuses})


class MealViewSet(viewsets.ModelViewSet):
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["date", "meal_type", "status"]
    ordering_fields = ["date", "created_at", "calories"]
    ordering = ["-date", "-created_at"]
    queryset = Meal.objects.all()  # Required for DRF router

    def get_queryset(self):
        """
        Return meals for the current authenticated user only.
        """
        return Meal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically set the user to the current authenticated user.
        """
        serializer.save(user=self.request.user)
