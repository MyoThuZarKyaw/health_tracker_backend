from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date
from .models import Workout, Meal, Steps

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
        response = self.client.get(
            reverse("workout-list"), {"date": date.today().isoformat()}
        )
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


class StepsModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@email.com", full_name="Test User", password="testpass123"
        )

    def test_steps_creation(self):
        """Test creating a steps entry with valid data"""
        steps = Steps.objects.create(
            user=self.user,
            date=date.today(),
            total_steps=8500,
            status="completed",
            description="Daily step goal achieved",
        )

        self.assertEqual(steps.user, self.user)
        self.assertEqual(steps.total_steps, 8500)
        self.assertEqual(steps.status, "completed")
        self.assertEqual(
            str(steps), f"{self.user.email} - 8500 steps on {date.today()}"
        )

    def test_steps_str_method(self):
        """Test the string representation of steps"""
        steps = Steps.objects.create(
            user=self.user, date=date.today(), total_steps=6500, status="in_progress"
        )
        expected_str = f"{self.user.email} - 6500 steps on {date.today()}"
        self.assertEqual(str(steps), expected_str)

    def test_steps_ordering(self):
        """Test that steps are ordered by date and created_at descending"""
        steps1 = Steps.objects.create(
            user=self.user, date=date.today(), total_steps=8000
        )
        steps2 = Steps.objects.create(
            user=self.user, date=date(2025, 10, 28), total_steps=7500
        )

        steps = Steps.objects.all()
        self.assertEqual(steps[0], steps1)  # More recent date first
        self.assertEqual(steps[1], steps2)


class StepsAPITest(APITestCase):
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

        # Create test steps entry
        self.steps = Steps.objects.create(
            user=self.user, date=date.today(), total_steps=8500, status="completed"
        )

    def test_steps_list_authenticated(self):
        """Test listing steps for authenticated user"""
        response = self.client.get(reverse("steps-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_steps_list_unauthenticated(self):
        """Test that unauthenticated users cannot list steps"""
        self.client.credentials()  # Remove authentication
        response = self.client.get(reverse("steps-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_steps_create(self):
        """Test creating a new steps entry"""
        data = {
            "date": "2025-10-29",
            "total_steps": 7200,
            "status": "completed",
            "description": "Good walking day",
        }
        response = self.client.post(reverse("steps-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Steps.objects.count(), 2)
        self.assertEqual(response.data["total_steps"], 7200)

    def test_steps_create_invalid_data(self):
        """Test creating steps with invalid data"""
        data = {
            "date": "2025-10-29",
            "total_steps": -100,  # Invalid negative steps
            "status": "invalid_status",
        }
        response = self.client.post(reverse("steps-list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_steps_retrieve(self):
        """Test retrieving a specific steps entry"""
        response = self.client.get(
            reverse("steps-detail", kwargs={"pk": self.steps.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_steps"], 8500)

    def test_steps_retrieve_other_user(self):
        """Test that users cannot access other users' steps"""
        other_steps = Steps.objects.create(
            user=self.other_user, date=date.today(), total_steps=9000
        )
        response = self.client.get(
            reverse("steps-detail", kwargs={"pk": other_steps.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_steps_update(self):
        """Test updating a steps entry"""
        data = {
            "date": "2025-10-29",
            "total_steps": 9000,
            "status": "completed",
            "description": "Updated step count",
        }
        response = self.client.put(
            reverse("steps-detail", kwargs={"pk": self.steps.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.steps.refresh_from_db()
        self.assertEqual(self.steps.total_steps, 9000)

    def test_steps_partial_update(self):
        """Test partially updating a steps entry"""
        data = {"status": "in_progress"}
        response = self.client.patch(
            reverse("steps-detail", kwargs={"pk": self.steps.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.steps.refresh_from_db()
        self.assertEqual(self.steps.status, "in_progress")

    def test_steps_delete(self):
        """Test deleting a steps entry"""
        response = self.client.delete(
            reverse("steps-detail", kwargs={"pk": self.steps.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Steps.objects.count(), 0)

    def test_steps_filtering(self):
        """Test filtering steps by various fields"""
        # Create additional steps for filtering
        Steps.objects.create(
            user=self.user,
            date=date(2025, 10, 28),
            total_steps=7500,
            status="completed",
        )

        # Filter by date
        response = self.client.get(
            reverse("steps-list"), {"date": date.today().isoformat()}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Filter by status
        response = self.client.get(reverse("steps-list"), {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_steps_ordering(self):
        """Test ordering steps"""
        # Create steps with earlier date
        Steps.objects.create(user=self.user, date=date(2025, 10, 28), total_steps=6500)

        response = self.client.get(reverse("steps-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by date descending (most recent first)
        self.assertEqual(response.data[0]["total_steps"], 8500)  # Today's steps
        self.assertEqual(response.data[1]["total_steps"], 6500)  # Yesterday's steps


class StepsChoicesAPITest(APITestCase):
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

    def test_steps_choices_authenticated(self):
        """Test getting steps choices for authenticated user"""
        response = self.client.get(reverse("steps-choices"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that steps_statuses are present
        self.assertIn("steps_statuses", response.data)

        # Check steps statuses
        steps_statuses = response.data["steps_statuses"]
        self.assertEqual(len(steps_statuses), 3)  # We have 3 status choices
        expected_statuses = ["planned", "in_progress", "completed"]
        actual_values = [ss["value"] for ss in steps_statuses]
        self.assertEqual(actual_values, expected_statuses)

    def test_steps_choices_unauthenticated(self):
        """Test that unauthenticated users cannot access steps choices"""
        self.client.credentials()  # Remove authentication
        response = self.client.get(reverse("steps-choices"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MealModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@email.com", full_name="Test User", password="testpass123"
        )

    def test_meal_creation(self):
        """Test creating a meal with valid data"""
        meal = Meal.objects.create(
            user=self.user,
            date=date.today(),
            meal_type="breakfast",
            food_name="Oatmeal",
            calories=300,
            status="consumed",
            description="Healthy breakfast",
        )

        self.assertEqual(meal.user, self.user)
        self.assertEqual(meal.meal_type, "breakfast")
        self.assertEqual(meal.food_name, "Oatmeal")
        self.assertEqual(meal.calories, 300)
        self.assertEqual(meal.status, "consumed")
        self.assertEqual(str(meal), f"{self.user.email} - breakfast on {date.today()}")

    def test_meal_str_method(self):
        """Test the string representation of meal"""
        meal = Meal.objects.create(
            user=self.user,
            date=date.today(),
            meal_type="lunch",
            food_name="Salad",
            calories=250,
        )
        expected_str = f"{self.user.email} - lunch on {date.today()}"
        self.assertEqual(str(meal), expected_str)

    def test_meal_ordering(self):
        """Test that meals are ordered by date and created_at descending"""
        meal1 = Meal.objects.create(
            user=self.user,
            date=date.today(),
            meal_type="breakfast",
            food_name="Oatmeal",
            calories=300,
        )
        meal2 = Meal.objects.create(
            user=self.user,
            date=date(2025, 10, 28),
            meal_type="dinner",
            food_name="Pasta",
            calories=500,
        )

        meals = Meal.objects.all()
        self.assertEqual(meals[0], meal1)  # More recent date first
        self.assertEqual(meals[1], meal2)


class MealAPITest(APITestCase):
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

        # Create test meal
        self.meal = Meal.objects.create(
            user=self.user,
            date=date.today(),
            meal_type="breakfast",
            food_name="Oatmeal",
            calories=300,
            status="consumed",
        )

    def test_meal_list_authenticated(self):
        """Test listing meals for authenticated user"""
        response = self.client.get(reverse("meal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_meal_list_unauthenticated(self):
        """Test that unauthenticated users cannot list meals"""
        self.client.credentials()  # Remove authentication
        response = self.client.get(reverse("meal-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_meal_create(self):
        """Test creating a new meal"""
        data = {
            "date": "2025-10-29",
            "meal_type": "lunch",
            "food_name": "Grilled Chicken Salad",
            "calories": 350,
            "status": "consumed",
            "description": "Healthy lunch option",
        }
        response = self.client.post(reverse("meal-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Meal.objects.count(), 2)
        self.assertEqual(response.data["meal_type"], "lunch")

    def test_meal_create_invalid_data(self):
        """Test creating meal with invalid data"""
        data = {
            "date": "2025-10-29",
            "meal_type": "invalid_type",  # Invalid choice
            "food_name": "Test Food",
            "calories": 200,
        }
        response = self.client.post(reverse("meal-list"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_meal_retrieve(self):
        """Test retrieving a specific meal"""
        response = self.client.get(reverse("meal-detail", kwargs={"pk": self.meal.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["meal_type"], "breakfast")

    def test_meal_retrieve_other_user(self):
        """Test that users cannot access other users' meals"""
        other_meal = Meal.objects.create(
            user=self.other_user,
            date=date.today(),
            meal_type="dinner",
            food_name="Steak",
            calories=600,
        )
        response = self.client.get(reverse("meal-detail", kwargs={"pk": other_meal.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_meal_update(self):
        """Test updating a meal"""
        data = {
            "date": "2025-10-29",
            "meal_type": "breakfast",
            "food_name": "Oatmeal with fruits",
            "calories": 320,
            "status": "consumed",
            "description": "Updated breakfast",
        }
        response = self.client.put(
            reverse("meal-detail", kwargs={"pk": self.meal.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.meal.refresh_from_db()
        self.assertEqual(self.meal.calories, 320)
        self.assertEqual(self.meal.food_name, "Oatmeal with fruits")

    def test_meal_partial_update(self):
        """Test partially updating a meal"""
        data = {"status": "skipped"}
        response = self.client.patch(
            reverse("meal-detail", kwargs={"pk": self.meal.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.meal.refresh_from_db()
        self.assertEqual(self.meal.status, "skipped")

    def test_meal_delete(self):
        """Test deleting a meal"""
        response = self.client.delete(
            reverse("meal-detail", kwargs={"pk": self.meal.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Meal.objects.count(), 0)

    def test_meal_filtering(self):
        """Test filtering meals by various fields"""
        # Create additional meals for filtering
        Meal.objects.create(
            user=self.user,
            date=date(2025, 10, 28),
            meal_type="dinner",
            food_name="Pasta",
            calories=500,
            status="consumed",
        )

        # Filter by date
        response = self.client.get(
            reverse("meal-list"), {"date": date.today().isoformat()}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Filter by meal_type
        response = self.client.get(reverse("meal-list"), {"meal_type": "breakfast"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Filter by status
        response = self.client.get(reverse("meal-list"), {"status": "consumed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_meal_ordering(self):
        """Test ordering meals"""
        # Create meal with earlier date
        Meal.objects.create(
            user=self.user,
            date=date(2025, 10, 28),
            meal_type="lunch",
            food_name="Sandwich",
            calories=400,
        )

        response = self.client.get(reverse("meal-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by date descending (most recent first)
        self.assertEqual(response.data[0]["meal_type"], "breakfast")  # Today's meal
        self.assertEqual(response.data[1]["meal_type"], "lunch")  # Yesterday's meal


class MealChoicesAPITest(APITestCase):
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

    def test_meal_choices_authenticated(self):
        """Test getting meal choices for authenticated user"""
        response = self.client.get(reverse("meal-choices"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that meal_types are present
        self.assertIn("meal_types", response.data)
        self.assertIn("meal_statuses", response.data)

        # Check meal types
        meal_types = response.data["meal_types"]
        self.assertEqual(len(meal_types), 4)  # We have 4 meal types
        expected_meal_types = ["breakfast", "lunch", "dinner", "snack"]
        actual_values = [mt["value"] for mt in meal_types]
        self.assertEqual(actual_values, expected_meal_types)

        # Check meal statuses
        meal_statuses = response.data["meal_statuses"]
        self.assertEqual(len(meal_statuses), 3)  # We have 3 meal status choices
        expected_meal_statuses = ["planned", "consumed", "skipped"]
        actual_values = [ms["value"] for ms in meal_statuses]
        self.assertEqual(actual_values, expected_meal_statuses)

    def test_meal_choices_unauthenticated(self):
        """Test that unauthenticated users cannot access meal choices"""
        self.client.credentials()  # Remove authentication
        response = self.client.get(reverse("meal-choices"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
