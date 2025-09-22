from news.models import Category
from ..serializers.category import GETCategorySerializer, POSTCategorySerializer
from rest_framework import viewsets, permissions
from ..permissions import IsVerifiedEmailUser


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = GETCategorySerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return POSTCategorySerializer
        return GETCategorySerializer
    
    def get_permissions(self):
        """
        Define permisos según la acción
        """
        if self.action in ['list', 'retrieve']:
            # Leer categorías - solo autenticados
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Crear/editar/eliminar - solo admin o usuarios con email verificado
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]