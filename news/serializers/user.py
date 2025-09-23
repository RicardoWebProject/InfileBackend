from django.utils import timezone
from rest_framework import serializers
from news.models import User
import uuid

# Importar funciones para email de verificación
from news.views.email_verification import generate_verification_token
from django.core.mail import send_mail
from django.conf import settings

class GETUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['public_id', 'first_name', 'last_name', 'username',
                    'email', 'phone_number', 'rol', 'social_provider', 
                    'avatar_url', 'is_social_user', 'email_verified', 
                    'created_at', 'updated_at']
        read_only_fields = ['public_id', 'created_at', 'updated_at', 'email_verified']
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
        fields = ['public_id','first_name', 'last_name', 'username',
                    'email', 'phone_number', 'rol', 'password', 'created_at', 'updated_at']
        read_only_fields = ['public_id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        # Crear usuario
        user = User(
            public_id=uuid.uuid4().hex[:8],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number', ''),
            rol=validated_data.get('rol', 'user'),
            email_verified=False,
            username=validated_data['username'],
        )
        user.set_password(validated_data['password'])
        
        # Generar token de verificación
        verification_token = generate_verification_token()
        user.email_verification_token = verification_token
        user.email_verification_sent_at = timezone.now()
        
        user.save()
        
        # Enviar email de verificación automáticamente
        self._send_verification_email(user, verification_token)
        
        return user
    
    def _send_verification_email(self, user, token):
        """
        Envía email de verificación cuando se crea un usuario
        """
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            
            # Mensaje simple para email de verificación
            html_message = f"""
            <h2>¡Bienvenido a InfileNews!</h2>
            <p>Hola {user.first_name},</p>
            <p>Gracias por registrarte en InfileNews. Para completar tu registro y activar tu cuenta, por favor verifica tu email haciendo clic en el siguiente enlace:</p>
            <p><a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verificar Email</a></p>
            <p>O copia y pega este enlace en tu navegador:</p>
            <p>{verification_url}</p>
            <p>Este enlace expirará en {settings.EMAIL_VERIFICATION_TIMEOUT_HOURS} horas.</p>
            <p>Si no creaste una cuenta en InfileNews, puedes ignorar este email.</p>
            <p>¡Esperamos verte pronto en nuestra plataforma!</p>
            <p>Saludos,<br>El equipo de InfileNews</p>
            """
            
            plain_message = f"""
            ¡Bienvenido a InfileNews!
            
            Hola {user.first_name},
            
            Gracias por registrarte en InfileNews. Para completar tu registro y activar tu cuenta, por favor verifica tu email visitando el siguiente enlace:
            {verification_url}
            
            Este enlace expirará en {settings.EMAIL_VERIFICATION_TIMEOUT_HOURS} horas.
            
            Si no creaste una cuenta en InfileNews, puedes ignorar este email.
            
            ¡Esperamos verte pronto en nuestra plataforma!
            
            Saludos,
            El equipo de InfileNews
            """
            
            send_mail(
                subject='¡Bienvenido a InfileNews! Verifica tu email',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,  # No fallar si no se puede enviar
            )
            
        except Exception as e:
            # Log el error pero no fallar la creación del usuario
            print(f"Error enviando email de verificación durante registro: {e}")
    
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


class SocialAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=True)
    
    def validate_access_token(self, value):
        if not value:
            raise serializers.ValidationError("Access token es requerido")
        return value


class SocialUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['public_id', 'first_name', 'last_name', 'email', 
                 'avatar_url', 'social_provider', 'is_social_user', 
                 'created_at', 'updated_at']
        read_only_fields = ['public_id', 'created_at', 'updated_at']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['created_at'] = instance.created_at.strftime('%Y-%m-%d') if instance.created_at else 'N/A'
        data['updated_at'] = instance.updated_at.strftime('%Y-%m-%d') if instance.updated_at else 'N/A'
        return data