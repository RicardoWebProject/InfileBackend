"""
URL configuration for infileNews project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers    
from news.views.user import UserViewSet, CustomTokenObtainPairView
from news.views.category import CategoryViewSet
from news.views.news import NewsViewSet
from news.views.social_auth import GoogleAuthView, GoogleAuthCallbackView, FacebookAuthView, FacebookAuthCallbackView
from news.views.email_verification import (
    SendEmailVerificationView, 
    VerifyEmailView, 
    ResendEmailVerificationView,
    check_email_verification_status
)
from news.views.auth_views import (
    CustomTokenRefreshView,
    logout_view,
    verify_token,
    TokenInfoView
)

router = routers.DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register('categories', CategoryViewSet, basename='categories')
router.register('news', NewsViewSet, basename='news')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', verify_token, name='token_verify'),
    path('api/token/info/', TokenInfoView.as_view(), name='token_info'),
    path('api/logout/', logout_view, name='logout'),
    
    # Social authentication
    path('auth/google/', GoogleAuthView.as_view(), name='google_auth'),
    path('auth/google/callback/', GoogleAuthCallbackView.as_view(), name='google_auth_callback'),
    path('auth/facebook/', FacebookAuthView.as_view(), name='facebook_auth'),
    path('auth/facebook/callback/', FacebookAuthCallbackView.as_view(), name='facebook_auth_callback'),
    
    # Email verification endpoints
    path('auth/send-verification/', SendEmailVerificationView.as_view(), name='send_email_verification'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('auth/resend-verification/', ResendEmailVerificationView.as_view(), name='resend_email_verification'),
    path('auth/check-verification/<str:email>/', check_email_verification_status, name='check_email_verification'),
]

# Servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
