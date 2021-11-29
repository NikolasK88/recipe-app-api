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
