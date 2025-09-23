from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets
import string

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import serializers

from news.models import User


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No existe un usuario con este email")
        return value


class VerifyEmailTokenSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, max_length=100)
    
    def validate_token(self, value):
        if not value:
            raise serializers.ValidationError("Token es requerido")
        return value


def generate_verification_token():
    """
    Genera un token seguro para verificación de email
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


class SendEmailVerificationView(APIView):
    """
    Vista para enviar email de verificación
    """
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Datos inválidos', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Verificar si el usuario ya está verificado
            if user.email_verified:
                return Response(
                    {'message': 'Este email ya está verificado'},
                    status=status.HTTP_200_OK
                )
            
            # Verificar si ya se envió un email recientemente (evitar spam)
            if (user.email_verification_sent_at and 
                timezone.now() - user.email_verification_sent_at < timedelta(minutes=5)):
                return Response(
                    {'error': 'Email de verificación ya enviado. Espera 5 minutos antes de solicitar otro.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Generar nuevo token
            verification_token = generate_verification_token()
            user.email_verification_token = verification_token
            user.email_verification_sent_at = timezone.now()
            user.save()
            
            # Enviar email
            success = self.send_verification_email(user, verification_token)
            
            if success:
                return Response(
                    {'message': 'Email de verificación enviado exitosamente'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Error al enviar el email. Intenta nuevamente.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': 'Error interno del servidor', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def send_verification_email(self, user, token):
        """
        Envía el email de verificación al usuario
        """
        try:
            # URL de verificación
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            
            # Contexto para el template
            context = {
                'user': user,
                'verification_url': verification_url,
                'site_name': 'InfileNews',
                'timeout_hours': settings.EMAIL_VERIFICATION_TIMEOUT_HOURS,
            }
            
            # Renderizar template HTML
            try:
                html_message = render_to_string('emails/email_verification.html', context)
                plain_message = strip_tags(html_message)
            except:
                # Fallback a mensaje simple si no hay template
                html_message = f"""
                <h2>Verifica tu email en InfileNews</h2>
                <p>Hola {user.first_name},</p>
                <p>Para completar tu registro, por favor verifica tu email haciendo clic en el siguiente enlace:</p>
                <p><a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verificar Email</a></p>
                <p>O copia y pega este enlace en tu navegador:</p>
                <p>{verification_url}</p>
                <p>Este enlace expirará en {settings.EMAIL_VERIFICATION_TIMEOUT_HOURS} horas.</p>
                <p>Si no creaste una cuenta en InfileNews, puedes ignorar este email.</p>
                <p>Saludos,<br>El equipo de InfileNews</p>
                """
                plain_message = f"""
                Verifica tu email en InfileNews
                
                Hola {user.first_name},
                
                Para completar tu registro, por favor verifica tu email visitando el siguiente enlace:
                {verification_url}
                
                Este enlace expirará en {settings.EMAIL_VERIFICATION_TIMEOUT_HOURS} horas.
                
                Si no creaste una cuenta en InfileNews, puedes ignorar este email.
                
                Saludos,
                El equipo de InfileNews
                """
            
            # Enviar email
            send_mail(
                subject='Verifica tu email - InfileNews',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            print(f"Error enviando email de verificación: {e}")
            return False


class VerifyEmailView(APIView):
    """
    Vista para verificar el email usando el token
    """
    
    def post(self, request):
        serializer = VerifyEmailTokenSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Datos inválidos', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = serializer.validated_data['token']
        
        try:
            user = User.objects.get(email_verification_token=token)
            
            # Verificar si el token ha expirado
            if (user.email_verification_sent_at and 
                timezone.now() - user.email_verification_sent_at > timedelta(hours=settings.EMAIL_VERIFICATION_TIMEOUT_HOURS)):
                return Response(
                    {'error': 'El token de verificación ha expirado. Solicita uno nuevo.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar email
            user.email_verified = True
            user.email_verification_token = None  # Limpiar token usado
            user.save()
            
            return Response(
                {'message': 'Email verificado exitosamente'},
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Token de verificación inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Error interno del servidor', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResendEmailVerificationView(APIView):
    """
    Vista para reenviar email de verificación
    """
    
    def post(self, request):
        # Reutilizar la lógica de SendEmailVerificationView
        send_view = SendEmailVerificationView()
        return send_view.post(request)


@api_view(['GET'])
def check_email_verification_status(request, email):
    """
    Endpoint para verificar el estado de verificación de un email
    """
    try:
        user = User.objects.get(email=email)
        return Response({
            'email': email,
            'verified': user.email_verified,
            'verification_sent': user.email_verification_sent_at is not None
        })
    except User.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )