from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomTokenRefreshView(TokenRefreshView):
    """
    Vista personalizada para refresh de tokens con información adicional
    """
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        # Obtener información del usuario del token
        refresh_token = serializer.validated_data.get('refresh')
        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh.payload.get('user_id')
            user = User.objects.get(id=user_id)
            
            response_data = serializer.validated_data
            response_data['user_info'] = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email_verified': user.email_verified,
                'is_social_user': user.is_social_user
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except (User.DoesNotExist, TokenError):
            return Response(serializer.validated_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Vista para logout - invalida el refresh token
    """
    try:
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logout exitoso'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Error en logout',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """
    Vista para verificar si un token es válido
    """
    user = request.user
    return Response({
        'valid': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email_verified': user.email_verified,
            'is_social_user': user.is_social_user,
            'rol': user.rol
        }
    }, status=status.HTTP_200_OK)


class TokenInfoView(APIView):
    """
    Vista para obtener información detallada del token actual
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            # Información básica del token
            token_info = {
                'token_valid': True,
                'token_prefix': token[:10] + '...',
                'user_info': {
                    'id': user.id,
                    'public_id': user.public_id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                    'email_verified': user.email_verified,
                    'is_social_user': user.is_social_user,
                    'social_provider': user.social_provider,
                    'rol': user.rol,
                    'is_staff': user.is_staff,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.isoformat() if user.date_joined else None
                },
                'permissions': {
                    'can_edit_profile': True,
                    'can_access_admin': user.is_staff,
                    'email_verified': user.email_verified,
                    'needs_email_verification': not user.email_verified and not user.is_social_user
                }
            }
            
            return Response(token_info, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'No se encontró token en el header Authorization'
        }, status=status.HTTP_400_BAD_REQUEST)