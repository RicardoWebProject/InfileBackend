from google.auth.transport import requests
from google.oauth2 import id_token
import facebook
import requests as http_requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils import timezone
import uuid

from news.models import User
from ..serializers.user import SocialAuthSerializer, SocialUserSerializer


class GoogleAuthView(APIView):
    """
    Vista para autenticación con Google OAuth2
    """
    
    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Datos inválidos', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        access_token = serializer.validated_data['access_token']
        
        try:
            # Verificar el token con Google
            google_user_info = self.verify_google_token(access_token)
            
            if not google_user_info:
                return Response(
                    {'error': 'Token de Google inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Buscar o crear usuario
            user, created = self.get_or_create_user(google_user_info)
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            # Serializar datos del usuario
            user_serializer = SocialUserSerializer(user)
            
            return Response({
                'message': 'Autenticación exitosa',
                'user': user_serializer.data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'is_new_user': created
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': 'Error en la autenticación', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def verify_google_token(self, access_token):
        """
        Verifica el token de acceso con Google y obtiene la información del usuario
        """
        try:
            # Verificar el token con Google
            idinfo = id_token.verify_oauth2_token(
                access_token, 
                requests.Request(), 
                getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)
            )
            
            # Verificar que el token sea válido
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Token inválido')
            
            return {
                'email': idinfo.get('email'),
                'first_name': idinfo.get('given_name', ''),
                'last_name': idinfo.get('family_name', ''),
                'google_id': idinfo.get('sub'),
                'avatar_url': idinfo.get('picture', ''),
                'email_verified': idinfo.get('email_verified', False)
            }
            
        except ValueError as e:
            print(f"Error verificando token de Google: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado verificando token: {e}")
            return None
    
    def get_or_create_user(self, google_user_info):
        """
        Busca un usuario existente o crea uno nuevo basado en la información de Google
        """
        email = google_user_info['email']
        google_id = google_user_info['google_id']
        
        # Primero intentar encontrar por email
        user = User.objects.filter(email=email).first()
        
        if user:
            # Usuario existente - actualizar información de Google si no la tiene
            created = False
            if not user.is_social_user or user.social_provider != 'google':
                user.social_provider = 'google'
                user.social_id = google_id
                user.is_social_user = True
                user.avatar_url = google_user_info['avatar_url']
                user.updated_at = timezone.now()
                user.save()
        else:
            # Crear nuevo usuario
            created = True
            user = User.objects.create(
                public_id=uuid.uuid4().hex[:8],
                email=email,
                first_name=google_user_info['first_name'],
                last_name=google_user_info['last_name'],
                username=email,  # Usar email como username
                social_provider='google',
                social_id=google_id,
                avatar_url=google_user_info['avatar_url'],
                is_social_user=True,
                rol='user',  # Rol por defecto
                phone_number='',  # Vacío para usuarios sociales
            )
            # Para usuarios sociales, no establecer password
            user.set_unusable_password()
            user.save()
        
        return user, created


class GoogleAuthCallbackView(APIView):
    """
    Vista alternativa para manejar callback directo de Google (opcional)
    """
    
    def get(self, request):
        return Response({
            'message': 'Usa el endpoint POST /auth/google/ con el access_token'
        }, status=status.HTTP_200_OK)


class FacebookAuthView(APIView):
    """
    Vista para autenticación con Facebook OAuth2
    """
    
    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Datos inválidos', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        access_token = serializer.validated_data['access_token']
        
        try:
            # Verificar el token con Facebook
            facebook_user_info = self.verify_facebook_token(access_token)
            
            if not facebook_user_info:
                return Response(
                    {'error': 'Token de Facebook inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Buscar o crear usuario
            user, created = self.get_or_create_user(facebook_user_info)
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            # Serializar datos del usuario
            user_serializer = SocialUserSerializer(user)
            
            return Response({
                'message': 'Autenticación exitosa',
                'user': user_serializer.data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'is_new_user': created
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': 'Error en la autenticación', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def verify_facebook_token(self, access_token):
        """
        Verifica el token de acceso con Facebook y obtiene la información del usuario
        """
        try:
            # Verificar token con Facebook Graph API
            app_id = getattr(settings, 'FACEBOOK_APP_ID', None)
            app_secret = getattr(settings, 'FACEBOOK_APP_SECRET', None)
            
            if not app_id or not app_secret:
                raise ValueError('Facebook credentials not configured')
            
            # Verificar que el token sea válido
            verify_url = f"https://graph.facebook.com/debug_token?input_token={access_token}&access_token={app_id}|{app_secret}"
            verify_response = http_requests.get(verify_url)
            verify_data = verify_response.json()
            
            if not verify_data.get('data', {}).get('is_valid'):
                raise ValueError('Token inválido')
            
            # Obtener información del usuario
            graph = facebook.GraphAPI(access_token=access_token, version="3.1")
            user_info = graph.get_object(
                'me',
                fields='id,name,email,first_name,last_name,picture.type(large)'
            )
            
            return {
                'email': user_info.get('email'),
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('last_name', ''),
                'facebook_id': user_info.get('id'),
                'avatar_url': user_info.get('picture', {}).get('data', {}).get('url', ''),
                'full_name': user_info.get('name', '')
            }
            
        except Exception as e:
            print(f"Error verificando token de Facebook: {e}")
            return None
    
    def get_or_create_user(self, facebook_user_info):
        """
        Busca un usuario existente o crea uno nuevo basado en la información de Facebook
        """
        email = facebook_user_info['email']
        facebook_id = facebook_user_info['facebook_id']
        
        if not email:
            # Si Facebook no proporciona email, usar el ID de Facebook
            email = f"facebook_{facebook_id}@facebook.local"
        
        # Primero intentar encontrar por email
        user = User.objects.filter(email=email).first()
        
        if user:
            # Usuario existente - actualizar información de Facebook si no la tiene
            created = False
            if not user.is_social_user or user.social_provider != 'facebook':
                user.social_provider = 'facebook'
                user.social_id = facebook_id
                user.is_social_user = True
                user.avatar_url = facebook_user_info['avatar_url']
                user.updated_at = timezone.now()
                user.save()
        else:
            # Crear nuevo usuario
            created = True
            user = User.objects.create(
                public_id=uuid.uuid4().hex[:8],
                email=email,
                first_name=facebook_user_info['first_name'],
                last_name=facebook_user_info['last_name'],
                username=email,  # Usar email como username
                social_provider='facebook',
                social_id=facebook_id,
                avatar_url=facebook_user_info['avatar_url'],
                is_social_user=True,
                rol='user',  # Rol por defecto
                phone_number='',  # Vacío para usuarios sociales
            )
            # Para usuarios sociales, no establecer password
            user.set_unusable_password()
            user.save()
        
        return user, created


class FacebookAuthCallbackView(APIView):
    """
    Vista alternativa para manejar callback directo de Facebook (opcional)
    """
    
    def get(self, request):
        return Response({
            'message': 'Usa el endpoint POST /auth/facebook/ con el access_token'
        }, status=status.HTTP_200_OK)