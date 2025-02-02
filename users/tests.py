from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model


User = get_user_model()


class UserCreationTests(APITestCase):
    def setUp(self):
        self.valid_data = {
            "email": "testuser@example.com",
            "phone_number": "+1234567890",
            "password": "strongpassword123",
            "first_name": "John",
            "last_name": "Doe",
        }
        self.invalid_data = {
            "email": "",
            "phone_number": "",
            "password": "",
            "first_name": "",
            "last_name": "",
        }
        self.url = reverse("user_create")

    def test_user_creation_with_valid_data(self):
        """Test creating a user with valid data."""
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(User.objects.filter(email=self.valid_data["email"]).exists())

    def test_user_creation_with_invalid_data(self):
        """Test creating a user with invalid data."""
        response = self.client.post(self.url, self.invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("password", response.data)

    def test_user_creation_with_duplicate_email(self):
        """Test creating a user with a duplicate email."""
        User.objects.create_user(
            username=self.valid_data["email"],
            email=self.valid_data["email"],
            phone_number="+0987654321",
            password="password123",
        )
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_creation_with_duplicate_phone(self):
        """Test creating a user with a duplicate phone number."""
        User.objects.create_user(
            username="uniqueuser",
            email="unique@example.com",
            phone_number=self.valid_data["phone_number"],
            password="password123",
        )
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data)

    def test_user_creation_without_required_fields(self):
        """Test creating a user without required fields."""
        response = self.client.post(self.url, {"password": "password123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("first_name", response.data)
        self.assertIn("last_name", response.data)
