from rest_framework import serializers
from core import models


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag obj"""

    class Meta:
        model = models.Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient obj"""

    class Meta:
        model = models.Ingredient
        fields = ('id', 'name')
        read_only_field = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes obj"""
    ingredients = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=models.Ingredient.objects.all())
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=models.Tag.objects.all())

    class Meta:
        model = models.Recipe
        fields = ('id', 'title', 'time_minutes', 'price', 'ingredients',
                  'tags', 'link', 'image')
        read_only_field = ('id',)


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail"""
    ingredients = IngredientSerializer(
        many=True,
        read_only=True)
    tags = TagSerializer(
        many=True,
        read_only=True)


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to recipes"""

    class Meta:
        model = models.Recipe
        fields = ('id', 'image')
        read_only_field = ('id',)
