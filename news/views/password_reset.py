from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import secrets
import string
from datetime import timedelta

User = get_user_model()

# Configuración
PASSWORD_RESET_TIMEOUT_HOURS = getattr(settings, 'PASSWORD_RESET_TIMEOUT_HOURS', 1)  # 1 hora por defecto


def generate_reset_token():
    """
    Genera un token seguro para reset de contraseña
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(64))


class ForgotPasswordView(APIView):
    """
    Endpoint para solicitar recuperación de contraseña
    POST /auth/forgot-password/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            
            # No revelar si el usuario existe o no por seguridad
            # Siempre devolver mensaje de éxito
            
            # Solo enviar email si el usuario existe y no es usuario social
            if not user.is_social_user:
                # Generar token de reset
                reset_token = generate_reset_token()
                user.password_reset_token = reset_token
                user.password_reset_sent_at = timezone.now()
                user.save(update_fields=['password_reset_token', 'password_reset_sent_at'])
                
                # Enviar email
                self._send_reset_email(user, reset_token)
            
        except User.DoesNotExist:
            # No hacer nada, pero devolver mensaje de éxito por seguridad
            pass
        
        return Response(
            {
                'message': 'Si el email existe en nuestro sistema, se ha enviado un enlace de recuperación de contraseña',
                'detail': f'El enlace expirará en {PASSWORD_RESET_TIMEOUT_HOURS} hora(s)'
            },
            status=status.HTTP_200_OK
        )
    
    def _send_reset_email(self, user, token):
        """
        Envía email con enlace de recuperación de contraseña
        """
        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            
            # Renderizar template HTML
            context = {
                'user': user,
                'reset_url': reset_url,
                'timeout_hours': PASSWORD_RESET_TIMEOUT_HOURS,
                'site_name': 'InfileNews'
            }
            
            html_message = render_to_string('emails/password_reset.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject='Recuperación de contraseña - InfileNews',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,
            )
            
        except Exception as e:
            print(f"Error enviando email de recuperación: {e}")


class ResetPasswordView(APIView):
    """
    Endpoint para restablecer contraseña con token
    POST /auth/reset-password/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Validaciones básicas
        if not all([token, new_password, confirm_password]):
            return Response(
                {'error': 'Token, nueva contraseña y confirmación son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != confirm_password:
            return Response(
                {'error': 'Las contraseñas no coinciden'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {'error': 'La contraseña debe tener al menos 8 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(password_reset_token=token)
            
            # Verificar si el token no ha expirado
            if user.password_reset_sent_at:
                time_limit = user.password_reset_sent_at + timedelta(hours=PASSWORD_RESET_TIMEOUT_HOURS)
                if timezone.now() > time_limit:
                    return Response(
                        {'error': 'El token de recuperación ha expirado'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'Token inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar que no sea usuario social
            if user.is_social_user:
                return Response(
                    {'error': 'Los usuarios de redes sociales no pueden cambiar su contraseña aquí'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cambiar contraseña
            user.set_password(new_password)
            user.password_reset_token = None  # Limpiar token
            user.password_reset_sent_at = None
            user.updated_at = timezone.now()
            user.save(update_fields=['password', 'password_reset_token', 'password_reset_sent_at', 'updated_at'])
            
            return Response(
                {'message': 'Contraseña restablecida exitosamente'},
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Token inválido o expirado'},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    Cambiar contraseña para usuarios autenticados
    POST /auth/change-password/
    """
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        return Response(
            {'error': 'Contraseña actual, nueva contraseña y confirmación son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    
    # Verificar que no sea usuario social
    if user.is_social_user:
        return Response(
            {'error': 'Los usuarios de redes sociales no pueden cambiar su contraseña'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar contraseña actual
    if not user.check_password(current_password):
        return Response(
            {'error': 'La contraseña actual es incorrecta'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar nueva contraseña
    if new_password != confirm_password:
        return Response(
            {'error': 'Las contraseñas no coinciden'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {'error': 'La contraseña debe tener al menos 8 caracteres'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Cambiar contraseña
    user.set_password(new_password)
    user.updated_at = timezone.now()
    user.save(update_fields=['password', 'updated_at'])
    
    return Response(
        {'message': 'Contraseña cambiada exitosamente'},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def validate_reset_token(request):
    """
    Validar si un token de reset es válido
    GET /auth/validate-reset-token/?token=TOKEN
    """
    token = request.query_params.get('token')
    
    if not token:
        return Response(
            {'error': 'Token es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(password_reset_token=token)
        
        # Verificar si el token no ha expirado
        if user.password_reset_sent_at:
            time_limit = user.password_reset_sent_at + timedelta(hours=PASSWORD_RESET_TIMEOUT_HOURS)
            if timezone.now() > time_limit:
                return Response(
                    {'valid': False, 'error': 'Token expirado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'valid': False, 'error': 'Token inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {
                'valid': True,
                'email': user.email,
                'expires_in_minutes': int((time_limit - timezone.now()).total_seconds() / 60)
            },
            status=status.HTTP_200_OK
        )
        
    except User.DoesNotExist:
        return Response(
            {'valid': False, 'error': 'Token inválido'},
            status=status.HTTP_400_BAD_REQUEST
        )