from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core import models
from recipe import serializers


INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientsAPITests(TestCase):
    """Test the publicy available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the endpoint"""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """Test the private ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'test1'
        )
        self.client.force_authenticate(self.user)

    def test_retrive_ingredient_list(self):
        """Test retrieving a list of ingredients"""
        models.Ingredient.objects.create(user=self.user, name='Kale')
        models.Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENT_URL)

        ingredients = models.Ingredient.objects.all().order_by('-name')
        serializer = serializers.IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Tet that ingredients for the authenticated user are returned"""
        user2 = get_user_model().objects.create_user('test2@gmail.com',
                                                     'testpass1')
        models.Ingredient.objects.create(user=user2, name='Salt')
        ingredient = models.Ingredient.objects.create(user=self.user,
                                                      name='Kale')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredients_successful(self):
        """Test that successfully creates ingredient obj"""
        payload = {'name': 'Cucumber'}

        res = self.client.post(INGREDIENT_URL, payload)

        ingredient_exists = models.Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(ingredient_exists)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_ingredients_invalid(self):
        """Test that creating ingredient obj with invalid credentials"""
        payload = {'name': ''}

        res = self.client.post(INGREDIENT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
