from django.utils import timezone
from rest_framework import serializers
from news.models import User
import uuid

class GETUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['public_id', 'first_name', 'last_name', 'username',
                    'email', 'phone_number', 'rol', 'created_at', 'updated_at']
        read_only_fields = ['public_id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['created_at'] = instance.created_at.strftime('%Y-%m-%d') if instance.created_at else 'N/A'
        data['updated_at'] = instance.updated_at.strftime('%Y-%m-%d') if instance.updated_at else 'N/A'
        return data

class POSTUserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['public_id','first_name', 'last_name', 
                    'email', 'phone_number', 'rol', 'password', 'created_at', 'updated_at']
        read_only_fields = ['public_id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = User(
            public_id=uuid.uuid4().hex[:8],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            rol=validated_data.get('rol', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['created_at'] = instance.created_at.strftime('%Y-%m-%d') if instance.created_at else 'N/A'
        data['updated_at'] = instance.updated_at.strftime('%Y-%m-%d') if instance.updated_at else 'N/A'
        return data
    
    def update(self, instance, validated_data):
        update_fields = []
        
        for field in [
            'first_name', 'last_name', 'email', 'phone_number', 'rol', 'password'
        ]:
            if field in validated_data:
                update_fields.append(field)
        
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        
        if update_fields:
            instance.updated_at = timezone.now()
            instance.save(update_fields=update_fields)
        
        return instance