from django.utils import timezone
from rest_framework import serializers
from news.models import Category
import uuid

class GETCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['public_id', 'category_name', 'created_at', 'updated_at']
        read_only_fields = ['public_id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['created_at'] = instance.created_at.strftime('%Y-%m-%d') if instance.created_at else 'N/A'
        data['updated_at'] = instance.updated_at.strftime('%Y-%m-%d') if instance.updated_at else 'N/A'
        return data

class POSTCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['public_id', 'category_name', 'created_at', 'updated_at']
        read_only_fields = ['public_id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        category = Category(
            public_id=uuid.uuid4().hex[:8],
            category_name=validated_data['category_name'],
        )
        category.save()
        return category
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['created_at'] = instance.created_at.strftime('%Y-%m-%d') if instance.created_at else 'N/A'
        data['updated_at'] = instance.updated_at.strftime('%Y-%m-%d') if instance.updated_at else 'N/A'
        return data
    
    def update(self, instance, validated_data):
        update_fields = []
        
        for field in ['category_name']:
            if field in validated_data:
                update_fields.append(field)
                setattr(instance, field, validated_data[field])
        
        if update_fields:
            instance.updated_at = timezone.now()
            update_fields.append('updated_at')
            instance.save(update_fields=update_fields)
        
        return instance