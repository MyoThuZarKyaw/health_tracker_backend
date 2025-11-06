from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date
from .models import Workout

User = get_user_model()


class WorkoutModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@email.com", full_name="Test User", password="testpass123"
        )

    def test_workout_creation(self):
        """Test creating a workout with valid data"""
        workout = Workout.objects.create(
            user=self.user,
            date=date.today(),
            workout_type="cardio",
            duration=30,
            calories_burned=250,
            status="completed",
            description="Morning run",
        )

        self.assertEqual(workout.user, self.user)
        self.assertEqual(workout.workout_type, "cardio")
        self.assertEqual(workout.duration, 30)
        self.assertEqual(workout.calories_burned, 250)
        self.assertEqual(workout.status, "completed")
        self.assertEqual(str(workout), f"{self.user.email} - cardio on {date.today()}")

    def test_workout_str_method(self):
        """Test the string representation of workout"""
        workout = Workout.objects.create(
            user=self.user,
            date=date.today(),
            workout_type="strength",
            duration=45,
            calories_burned=180,
        )
        expected_str = f"{self.user.email} - strength on {date.today()}"
        self.assertEqual(str(workout), expected_str)

    def test_workout_ordering(self):
        """Test that workouts are ordered by date and created_at descending"""
        workout1 = Workout.objects.create(
            user=self.user,
            date=date.today(),
            workout_type="cardio",
            duration=30,
            calories_burned=250,
        )
        workout2 = Workout.objects.create(
            user=self.user,
            date=date(2025, 10, 28),
            workout_type="strength",
            duration=45,
            calories_burned=180,
        )

        workouts = Workout.objects.all()
        self.assertEqual(workouts[0], workout1)  # More recent date first
        self.assertEqual(workouts[1], workout2)


class WorkoutAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@email.com", full_name="Test User", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            email="other@email.com", full_name="Other User", password="testpass123"
        )

        # Get JWT token
        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "test@email.com", "password": "testpass123"},
        )
        self.token = token_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # Create test workout
        self.workout = Workout.objects.create(
            user=self.user,
            date=date.today(),
            workout_type="cardio",
            duration=30,
            calories_burned=250,
            status="completed",
        )

    def test_workout_list_authenticated(self):
        """Test listing workouts for authenticated user"""
        response = self.client.get(reverse("workout-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_workout_list_unauthenticated(self):
        """Test that unauthenticated users cannot list workouts"""
        self.client.credentials()  # Remove authentication
        response = self.client.get(reverse("workout-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_workout_create(self):
        """Test creating a new workout"""
        data = {
            "date": "2025-10-29",
            "workout_type": "strength",
            "duration": 45,
            "calories_burned": 180,
            "status": "completed",
            "description": "Weight training session",
        }
        response = self.client.post(reverse("workout-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Workout.objects.count(), 2)
        self.assertEqual(response.data["workout_type"], "strength")

    def test_workout_create_invalid_data(self):
        """Test creating workout with invalid data"""
        data = {
            "date": "2025-10-29",
            "workout_type": "invalid_type",  # Invalid choice
            "duration": 30,
            "calories_burned": 250,
        }
        response = self.client.post(reverse("workout-list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_workout_retrieve(self):
        """Test retrieving a specific workout"""
        response = self.client.get(
            reverse("workout-detail", kwargs={"pk": self.workout.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["workout_type"], "cardio")

    def test_workout_retrieve_other_user(self):
        """Test that users cannot access other users' workouts"""
        other_workout = Workout.objects.create(
            user=self.other_user,
            date=date.today(),
            workout_type="yoga",
            duration=60,
            calories_burned=120,
        )
        response = self.client.get(
            reverse("workout-detail", kwargs={"pk": other_workout.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_workout_update(self):
        """Test updating a workout"""
        data = {
            "date": "2025-10-29",
            "workout_type": "cardio",
            "duration": 35,
            "calories_burned": 280,
            "status": "completed",
            "description": "Updated morning run",
        }
        response = self.client.put(
            reverse("workout-detail", kwargs={"pk": self.workout.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.workout.refresh_from_db()
        self.assertEqual(self.workout.duration, 35)
        self.assertEqual(self.workout.calories_burned, 280)

    def test_workout_partial_update(self):
        """Test partially updating a workout"""
        data = {"status": "in_progress"}
        response = self.client.patch(
            reverse("workout-detail", kwargs={"pk": self.workout.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.workout.refresh_from_db()
        self.assertEqual(self.workout.status, "in_progress")

    def test_workout_delete(self):
        """Test deleting a workout"""
        response = self.client.delete(
            reverse("workout-detail", kwargs={"pk": self.workout.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Workout.objects.count(), 0)

    def test_workout_filtering(self):
        """Test filtering workouts by various fields"""
        # Create additional workouts for filtering
        Workout.objects.create(
            user=self.user,
            date=date(2025, 10, 28),
            workout_type="strength",
            duration=45,
            calories_burned=180,
            status="completed",
        )

        # Filter by date
        response = self.client.get(reverse("workout-list"), {"date": "2025-11-07"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Filter by workout_type
        response = self.client.get(reverse("workout-list"), {"workout_type": "cardio"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Filter by status
        response = self.client.get(reverse("workout-list"), {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_workout_ordering(self):
        """Test ordering workouts"""
        # Create workout with earlier date
        Workout.objects.create(
            user=self.user,
            date=date(2025, 10, 28),
            workout_type="yoga",
            duration=60,
            calories_burned=120,
        )

        response = self.client.get(reverse("workout-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by date descending (most recent first)
        self.assertEqual(response.data[0]["workout_type"], "cardio")  # Today's workout
        self.assertEqual(
            response.data[1]["workout_type"], "yoga"
        )  # Yesterday's workout


class WorkoutChoicesAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@email.com", full_name="Test User", password="testpass123"
        )

        # Get JWT token
        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "test@email.com", "password": "testpass123"},
        )
        self.token = token_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_workout_choices_authenticated(self):
        """Test getting workout choices for authenticated user"""
        response = self.client.get(reverse("workout-choices"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that workout_types are present
        self.assertIn("workout_types", response.data)
        self.assertIn("workout_statuses", response.data)

        # Check workout types
        workout_types = response.data["workout_types"]
        self.assertEqual(len(workout_types), 6)  # We have 6 workout types
        expected_types = ["cardio", "strength", "yoga", "pilates", "sports", "other"]
        actual_values = [wt["value"] for wt in workout_types]
        self.assertEqual(actual_values, expected_types)

        # Check workout statuses
        workout_statuses = response.data["workout_statuses"]
        self.assertEqual(len(workout_statuses), 4)  # We have 4 status choices
        expected_statuses = ["planned", "in_progress", "completed", "cancelled"]
        actual_values = [ws["value"] for ws in workout_statuses]
        self.assertEqual(actual_values, expected_statuses)

    def test_workout_choices_unauthenticated(self):
        """Test that unauthenticated users cannot access workout choices"""
        self.client.credentials()  # Remove authentication
        response = self.client.get(reverse("workout-choices"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
