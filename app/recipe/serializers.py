from rest_framework import serializers
from core import models


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag obj"""

    class Meta:
        model = models.Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)
