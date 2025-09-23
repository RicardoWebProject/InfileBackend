from news.models import User
from ..serializers.user import GETUserSerializer, POSTUserSerializer
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers.token import CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GETUserSerializer
        return POSTUserSerializer
    
    def get_permissions(self):
        """
        Define permisos según la acción
        """
        if self.action == 'create':
            # Registro público (crear usuario)
            permission_classes = [permissions.AllowAny]
        elif self.action in ['list']:
            # Listar usuarios solo para staff/admin
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            # Ver/editar solo propio perfil o admin
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'destroy':
            # Eliminar solo admin
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filtrar queryset según usuario y permisos
        """
        if not self.request.user.is_authenticated:
            return User.objects.none()
        
        # Si es admin, puede ver todos
        if self.request.user.is_staff:
            return User.objects.all()
        
        # Usuario normal solo ve su propio perfil
        if self.action in ['retrieve', 'update', 'partial_update']:
            return User.objects.filter(id=self.request.user.id)
        
        return User.objects.all()
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Endpoint para obtener información del usuario autenticado
        GET /users/me/
        """
        serializer = GETUserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_me(self, request):
        """
        Endpoint para actualizar información del usuario autenticado
        PUT/PATCH /users/update_me/
        """
        serializer = POSTUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(GETUserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    