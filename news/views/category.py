from news.models import Category
from ..serializers.category import GETCategorySerializer, POSTCategorySerializer
from rest_framework import viewsets

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = GETCategorySerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return POSTCategorySerializer
        return GETCategorySerializer