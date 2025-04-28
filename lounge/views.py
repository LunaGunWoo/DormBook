from rest_framework import permissions, generics
from .models import *
from .serializers import *


class PingPongTableListAPIView(generics.ListAPIView):
    queryset = PingPongTable.objects.all()
    serializer_class = PingPongTableSerializer
    permission_classes = [permissions.IsAuthenticated]
