from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from news.models import News, Category
from news.serializers.news import (
    NewsSerializer, CreateNewsSerializer, 
    UpdateNewsSerializer, NewsListSerializer
)
from news.permissions import IsEmailVerified, IsAuthorOrAdmin, IsAuthorOrReadOnly


class NewsViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operaciones CRUD de noticias
    """
    queryset = News.objects.all()
    lookup_field = 'public_id'
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]
    
    def get_serializer_class(self):
        """Seleccionar el serializer apropiado según la acción"""
        if self.action == 'create':
            return CreateNewsSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateNewsSerializer
        elif self.action == 'list':
            return NewsListSerializer
        else:
            return NewsSerializer
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve']:
            # Lectura permitida para usuarios verificados
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'create':
            # Creación para usuarios verificados
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Modificación/eliminación solo para el autor o admin
            permission_classes = [permissions.IsAuthenticated, IsEmailVerified, IsAuthorOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated, IsEmailVerified]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtrar noticias según los parámetros de consulta"""
        queryset = News.objects.select_related('category', 'author').order_by('-publication_date')
        
        # Filtrar por categoría
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category__public_id=category_id)
        
        # Filtrar por autor
        author_id = self.request.query_params.get('author', None)
        if author_id:
            queryset = queryset.filter(author__public_id=author_id)
        
        # Filtrar por búsqueda en título
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(headline__icontains=search)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear una nueva noticia"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            news = serializer.save()
            # Devolver datos completos de la noticia creada
            response_serializer = NewsSerializer(news)
            return Response(
                {
                    'message': 'Noticia creada exitosamente',
                    'news': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Actualizar una noticia completa"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid():
            news = serializer.save()
            response_serializer = NewsSerializer(news)
            return Response(
                {
                    'message': 'Noticia actualizada exitosamente',
                    'news': response_serializer.data
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        """Actualizar parcialmente una noticia"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            news = serializer.save()
            response_serializer = NewsSerializer(news)
            return Response(
                {
                    'message': 'Noticia actualizada exitosamente',
                    'news': response_serializer.data
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar una noticia"""
        instance = self.get_object()
        instance.delete()
        return Response(
            {'message': 'Noticia eliminada exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def my_news(self, request):
        """Obtener noticias del usuario autenticado"""
        user_news = News.objects.filter(author=request.user).select_related('category')
        serializer = NewsListSerializer(user_news, many=True)
        return Response({
            'count': user_news.count(),
            'news': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Obtener noticias agrupadas por categoría"""
        categories = Category.objects.all()
        result = []
        
        for category in categories:
            news_in_category = News.objects.filter(category=category)[:5]  # Últimas 5 noticias
            if news_in_category.exists():
                result.append({
                    'category': {
                        'public_id': category.public_id,
                        'category_name': category.category_name
                    },
                    'news_count': News.objects.filter(category=category).count(),
                    'latest_news': NewsListSerializer(news_in_category, many=True).data
                })
        
        return Response({
            'categories': result
        })
    
    @action(detail=True, methods=['get'])
    def related_news(self, request, public_id=None):
        """Obtener noticias relacionadas (misma categoría)"""
        news = self.get_object()
        related = News.objects.filter(
            category=news.category
        ).exclude(
            public_id=news.public_id
        )[:5]
        
        serializer = NewsListSerializer(related, many=True)
        return Response({
            'count': related.count(),
            'related_news': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Obtener noticias recientes"""
        recent_news = News.objects.select_related('category', 'author').order_by('-created_at')[:10]
        serializer = NewsListSerializer(recent_news, many=True)
        return Response({
            'count': recent_news.count(),
            'recent_news': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Estadísticas de noticias del usuario"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_news = News.objects.filter(author=request.user)
        categories_used = user_news.values_list('category__category_name', flat=True).distinct()
        
        stats = {
            'total_news': user_news.count(),
            'categories_used': list(categories_used),
            'categories_count': len(categories_used),
            'latest_news': user_news.order_by('-created_at').first().headline if user_news.exists() else None
        }
        
        return Response(stats)