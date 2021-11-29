from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core import models
from recipe import serializers


TAGS_URL = reverse('recipe:tag-list')


def create_user(**params):
    """Creating a user for tests"""
    return get_user_model().objects.create_user(**params)


class PubligTagsAPITests(TestCase):
    """Test that publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrivering tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        self.user = create_user(email='test@gmail.com',
                                password='1qazxsw2',
                                name='Test name')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrive_tags(self):
        """Test retriving tags"""
        models.Tag.objects.create(user=self.user, name='Vegan')
        models.Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        tags = models.Tag.objects.all().order_by('-name')
        serializer = serializers.TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user"""
        user2 = get_user_model().objects.create_user('test2@gmail.com',
                                                     'test1')
        models.Tag.objects.create(user=user2, name="Fruit")
        tag = models.Tag.objects.create(user=self.user, name="Confort Food")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {'name': 'Test tag'}
        self.client.post(TAGS_URL, payload)

        exists = models.Tag.objects.filter(user=self.user,
                                           name=payload['name']).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Test creating tag with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
