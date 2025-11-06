from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@email.com", full_name="Test User", password="testpass123"
        )
        self.assertEqual(user.email, "test@email.com")
        self.assertEqual(user.full_name, "Test User")
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email="admin@email.com", full_name="Admin User", password="adminpass123"
        )
        self.assertEqual(superuser.email, "admin@email.com")
        self.assertEqual(superuser.full_name, "Admin User")
        self.assertTrue(superuser.check_password("adminpass123"))
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_email_unique(self):
        User.objects.create_user(
            email="duplicate@email.com", full_name="First User", password="pass123"
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="duplicate@email.com",
                full_name="Second User",
                password="pass123",
            )

    def test_user_str(self):
        user = User.objects.create_user(
            email="strtest@email.com", full_name="String Test", password="pass123"
        )
        self.assertEqual(str(user), "strtest@email.com")


class UserRegistrationAPITest(APITestCase):
    def test_user_registration_success(self):
        url = reverse("user-register")
        data = {
            "full_name": "First User",
            "email": "firstuser@email.com",
            "password": "password123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["full_name"], "First User")
        self.assertEqual(response.data["email"], "firstuser@email.com")
        self.assertIn("id", response.data)
        # Verify user was created in database
        user = User.objects.get(email="firstuser@email.com")
        self.assertEqual(user.full_name, "First User")
        self.assertTrue(user.check_password("password123"))

    def test_user_registration_duplicate_email(self):
        # Create first user
        User.objects.create_user(
            email="duplicate@email.com", full_name="First User", password="pass123"
        )
        url = reverse("user-register")
        data = {
            "full_name": "Second User",
            "email": "duplicate@email.com",
            "password": "pass123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_registration_missing_fields(self):
        url = reverse("user-register")
        data = {
            "full_name": "Incomplete User",
            # Missing email and password
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("password", response.data)

    def test_user_registration_short_password(self):
        url = reverse("user-register")
        data = {
            "full_name": "Short Pass User",
            "email": "shortpass@email.com",
            "password": "123",  # Too short
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
