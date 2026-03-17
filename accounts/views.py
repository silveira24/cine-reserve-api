from rest_framework import generics, permissions
from .serializers import UserSerializer
from .models import User

from drf_spectacular.utils import extend_schema
@extend_schema(auth=[], responses={201: UserSerializer})
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer