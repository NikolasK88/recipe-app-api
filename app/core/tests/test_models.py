from django.test import TestCase
from django.contrib.auth import get_user_model

# from app.core import models


class ModelTests(TestCase):

    def test_create_user_with_email_succesful(self):
        """Test creating a new user with email is succesful"""
        email = 'test@gmail.com'
        password = '1qazxsw2'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertEqual(user.check_password(password), True)

    def test_new_user_email_normalized(self):
        """Test email for a new user is normolized"""
        email = 'test@GMAIL.COM'
        user = get_user_model().objects.create_user(
            email=email,
            password='1qazxsw2'
        )
        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating a user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, '1qazxsw2')

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser(
            'test@gmail.com',
            '1qazxsw2'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)