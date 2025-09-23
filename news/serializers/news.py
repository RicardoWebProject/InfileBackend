from rest_framework import serializers
from news.models import News, Category, User
import uuid
from django.utils import timezone


class NewsSerializer(serializers.ModelSerializer):
    """
    Serializer para leer noticias (GET requests)
    """
    category_info = serializers.SerializerMethodField()
    author_info = serializers.SerializerMethodField()
    
    class Meta:
        model = News
        fields = [
            'public_id', 'headline', 'news_body', 'cover_image',
            'category_info', 'author_info', 'publication_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['public_id', 'publication_date', 'created_at', 'updated_at']
    
    def get_category_info(self, obj):
        """Información completa de la categoría"""
        if obj.category:
            return {
                'public_id': obj.category.public_id,
                'category_name': obj.category.category_name
            }
        return None
    
    def get_author_info(self, obj):
        """Información completa del autor"""
        if obj.author:
            return {
                'public_id': obj.author.public_id,
                'first_name': obj.author.first_name,
                'last_name': obj.author.last_name,
                'email': obj.author.email,
                'avatar_url': obj.author.avatar_url
            }
        return None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Formatear fechas
        if instance.publication_date:
            data['publication_date'] = instance.publication_date.strftime('%Y-%m-%d %H:%M:%S')
        if instance.created_at:
            data['created_at'] = instance.created_at.strftime('%Y-%m-%d %H:%M:%S')
        if instance.updated_at:
            data['updated_at'] = instance.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        
        return data


class CreateNewsSerializer(serializers.ModelSerializer):
    """
    Serializer para crear noticias (POST requests)
    """
    category_public_id = serializers.CharField(write_only=True)
    author_public_id = serializers.CharField(write_only=True, required=False)
    cover_image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = News
        fields = [
            'headline', 'news_body', 'cover_image',
            'category_public_id', 'author_public_id'
        ]
    
    def validate_category_public_id(self, value):
        """Validar que la categoría existe"""
        try:
            category = Category.objects.get(public_id=value)
            return value
        except Category.DoesNotExist:
            raise serializers.ValidationError("Categoría no encontrada")
    
    def validate_author_public_id(self, value):
        """Validar que el autor existe"""
        if value:
            try:
                author = User.objects.get(public_id=value)
                return value
            except User.DoesNotExist:
                raise serializers.ValidationError("Autor no encontrado")
        return value
    
    def create(self, validated_data):
        # Obtener category y author por public_id
        category_public_id = validated_data.pop('category_public_id')
        author_public_id = validated_data.pop('author_public_id', None)
        
        category = Category.objects.get(public_id=category_public_id)
        
        # Si no se proporciona author_public_id, usar el usuario autenticado
        if author_public_id:
            author = User.objects.get(public_id=author_public_id)
        else:
            author = self.context['request'].user
        
        # Crear la noticia
        news = News.objects.create(
            public_id=uuid.uuid4().hex[:8],
            category=category,
            author=author,
            **validated_data
        )
        
        return news


class UpdateNewsSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar noticias (PUT/PATCH requests)
    """
    category_public_id = serializers.CharField(write_only=True, required=False)
    cover_image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = News
        fields = [
            'headline', 'news_body', 'cover_image',
            'category_public_id'
        ]
    
    def validate_category_public_id(self, value):
        """Validar que la categoría existe"""
        if value:
            try:
                category = Category.objects.get(public_id=value)
                return value
            except Category.DoesNotExist:
                raise serializers.ValidationError("Categoría no encontrada")
        return value
    
    def update(self, instance, validated_data):
        # Si se proporciona category_public_id, actualizar la relación
        category_public_id = validated_data.pop('category_public_id', None)
        
        if category_public_id:
            category = Category.objects.get(public_id=category_public_id)
            instance.category = category
        
        # Actualizar otros campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.updated_at = timezone.now()
        instance.save()
        
        return instance


class NewsListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listado de noticias
    """
    category_name = serializers.CharField(source='category.category_name', read_only=True)
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = News
        fields = [
            'public_id', 'headline', 'cover_image',
            'category_name', 'author_name', 'publication_date'
        ]
    
    def get_author_name(self, obj):
        """Nombre completo del autor"""
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}".strip()
        return "Anónimo"
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Formatear fecha para listado
        if instance.publication_date:
            data['publication_date'] = instance.publication_date.strftime('%Y-%m-%d')
        return data