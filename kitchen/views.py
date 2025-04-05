from rest_framework import permissions, status, generics
from rest_framework.response import Response
from .serializers import *
from .models import *


class InductionListAPIView(generics.ListAPIView):
    queryset = Induction.objects.all()
    serializer_class = InductionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        queryset = self.get_queryset()
        serializer = InductionSerializer(queryset, many=True)
        return Response(serializer.data)
