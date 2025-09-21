from news.models import User
from ..serializers.user import GETUserSerializer, POSTUserSerializer
from rest_framework import viewsets
from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers.token import CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GETUserSerializer
        return POSTUserSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    