from rest_framework import serializers
from .models import Workout, Meal, Steps


class WorkoutSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Workout
        fields = [
            "id",
            "user",
            "user_email",
            "date",
            "workout_type",
            "duration",
            "calories_burned",
            "status",
            "description",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]

    def create(self, validated_data):
        # Automatically set the user to the current authenticated user
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class StepsSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Steps
        fields = [
            "id",
            "user",
            "user_email",
            "date",
            "total_steps",
            "status",
            "description",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]

    def create(self, validated_data):
        # Automatically set the user to the current authenticated user
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class MealSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Meal
        fields = [
            "id",
            "user",
            "user_email",
            "date",
            "meal_type",
            "food_name",
            "calories",
            "status",
            "description",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]

    def create(self, validated_data):
        # Automatically set the user to the current authenticated user
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
