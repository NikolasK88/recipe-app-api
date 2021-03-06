from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import tempfile
import os
from PIL import Image
from core import models
from recipe import serializers


RECIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return URL for recipe uploaded image"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return models.Recipe.objects.create(user=user, **defaults)


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return models.Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create and return a sample ingredient"""
    return models.Ingredient.objects.create(user=user, name=name)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that auth is required"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test auth recipe API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'admin@gmail.com',
            '1qazxsw2')
        self.client.force_authenticate(self.user)

    def test_retrieving_recipes(self):
        """Test retrieving a list of recipies"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = models.Recipe.objects.all().order_by('-id')
        serializer = serializers.RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""
        user2 = get_user_model().objects.create_user(
            'test2@gmail.com',
            '1qazxsw2')
        sample_recipe(user=user2)
        recipe = sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = models.Recipe.objects.filter(user=self.user)
        serializer = serializers.RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.data[0]['title'], recipe.title)

    def test_view_recipe_detail(self):
        """Test viewing recipe details"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = serializers.RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': "Chocolate cake",
            'time_minutes': 10,
            'price': 5.00
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = models.Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_creating_recipe_with_tags(self):
        """Test creating the recipe with tags"""
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Dessert')

        payload = {
            'title': "Avocado lime cheesecake",
            'tags': [tag1.id, tag2.id],
            'time_minutes': 60,
            'price': 20.00
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = models.Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_creating_recipe_with_ingredients(self):
        """Test creating the ingredients with tags"""
        ingredient1 = sample_ingredient(user=self.user, name='Ginger')
        ingredient2 = sample_ingredient(user=self.user, name='Prawns')

        payload = {
            'title': "Thai prawn red curry",
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 60,
            'price': 20.00
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = models.Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_updating_recipe(self):
        """Test updating a recipe with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Curry')

        payload = {
            'title': 'Sample recip',
            'tags': [new_tag.id]
        }

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Spaghettu carbonara',
            'time_minutes': 25,
            'price': 5.00
        }

        url = detail_url(recipe.id)
        self.client.put(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class REcipeImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'admin@gmail.com',
            '1qazxsw2')
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_for_recipe(self):
        """Test that upload image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)

            res = self.client.patch(url,
                                    {'image': ntf},
                                    format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.patch(url,
                                {'image': 'not image'},
                                format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipe_by_tags(self):
        """Test returning recipe with specific tags"""
        recipe1 = sample_recipe(user=self.user,
                                title='Thia vagetable curry')
        recipe2 = sample_recipe(user=self.user,
                                title='Pizza')
        recipe3 = sample_recipe(user=self.user,
                                title='Roast Beef')
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Vegetarian')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        res = self.client.get(
            RECIPE_URL,
            {'tags': f'{tag1.id}, {tag2.id}'}
        )

        serializer1 = serializers.RecipeSerializer(recipe1)
        serializer2 = serializers.RecipeSerializer(recipe2)
        serializer3 = serializers.RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipe_by_ingredients(self):
        """Test returning recipe with specific ingredients"""
        recipe1 = sample_recipe(user=self.user,
                                title='Thia vagetable curry')
        recipe2 = sample_recipe(user=self.user,
                                title='Pizza')
        recipe3 = sample_recipe(user=self.user,
                                title='Roast Beef')
        ingredient1 = sample_ingredient(user=self.user,
                                        name='Potato')
        ingredient2 = sample_ingredient(user=self.user,
                                        name='Cheese')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        res = self.client.get(
            RECIPE_URL,
            {'ingredients': f'{ingredient1.id}, {ingredient2.id}'}
        )

        serializer1 = serializers.RecipeSerializer(recipe1)
        serializer2 = serializers.RecipeSerializer(recipe2)
        serializer3 = serializers.RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
