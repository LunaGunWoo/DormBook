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


class InductionTimeSlotListAPIView(generics.ListAPIView):
    serializer_class = ListInductionTimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        induction_pk = self.kwargs.get("pk")
        return InductionTimeSlot.objects.filter(induction__pk=induction_pk)


class InductionTimeSlotBookAPIView(generics.GenericAPIView):
    serializer_class = BookInductionTimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, timeslot_pk):
        try:
            time_slot = InductionTimeSlot.objects.get(pk=timeslot_pk)
            if time_slot.user:
                return Response(
                    {"error": "이미 예약 되었습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            time_slot.book(request.user)
            serializer = self.get_serializer(time_slot)
            return Response(serializer.data)
        except InductionTimeSlot.DoesNotExist:
            return Response(
                {"error": "해당 시간 슬롯을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
