from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Category(models.Model):
    id = models.BigAutoField(primary_key=True)
    public_id = models.CharField(max_length=10, unique=True)
    category_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = 'category'

class User(AbstractUser):
    id = models.BigAutoField(primary_key=True)
    public_id = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    email = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=225)
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    rol = models.CharField(max_length=10, default='')
    
    # Campos para autenticación social
    social_provider = models.CharField(max_length=20, blank=True, null=True)  # 'google', 'facebook', etc.
    social_id = models.CharField(max_length=100, blank=True, null=True)  # ID del usuario en la red social
    avatar_url = models.URLField(blank=True, null=True)  # URL del avatar de la red social
    is_social_user = models.BooleanField(default=False)
    
    # Campos para verificación de email
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'user'

class News(models.Model):
    id = models.BigAutoField(primary_key=True)
    public_id = models.CharField(max_length=10, unique=True)
    headline = models.CharField(max_length=100)
    news_body = models.TextField()
    cover_image = models.ImageField(upload_to='images/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    publication_date = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'news'
