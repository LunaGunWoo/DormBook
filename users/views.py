from django.contrib.auth import login, authenticate, logout
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    MyAllBookingsResponseSerializer,
)
from .models import User
from lounge.models import PingPongTableTimeSlot, ArcadeMachineTimeSlot
from lounge.serializers import (
    ListPingPongTableTimeSlotSerializer,
    ListArcadeMachineTimeSlotSerializer,
)
from kitchen.models import InductionTimeSlot
from kitchen.serializers import ListInductionTimeSlotSerializer
from gym.models import TreadmillTimeSlot, CycleTimeSlot
from gym.serializers import ListTreadmillTimeSlotSerializer, ListCycleTimeSlotSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class ChangePasswordAPIView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user

    def put(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response(
                {"detail": "Password updated successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class LogInAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student_id_number = serializer.validated_data.get("student_id_number")
        password = serializer.validated_data.get("password")
        user = authenticate(
            request=request,
            student_id_number=student_id_number,
            password=password,
        )

        if user is not None:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {"detail": "로그인 성공", "token": token.key},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"detail": "로그인 실패"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogOutAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except (AttributeError, Token.DoesNotExist):
            pass

        logout(request=request)
        return Response({"detail": "로그아웃 성공"}, status=status.HTTP_200_OK)


class MyAllBookingsListAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="사용자의 모든 예약 목록 조회",
        operation_description="현재 로그인한 사용자가 예약한 모든 시설(라운지, 부엌, 헬스장)의 예약 내역을 시설 유형별로 분류하여 반환합니다.",
        responses={
            status.HTTP_200_OK: MyAllBookingsResponseSerializer(),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(
                description="인증되지 않은 사용자"
            ),
        },
        tags=["Users"],
    )
    def get(self, request, *args, **kwargs):
        user = request.user

        ping_pong_bookings = PingPongTableTimeSlot.objects.filter(user=user).order_by(
            "start_time"
        )
        arcade_machine_bookings = ArcadeMachineTimeSlot.objects.filter(
            user=user
        ).order_by("start_time")
        induction_bookings = InductionTimeSlot.objects.filter(user=user).order_by(
            "start_time"
        )
        treadmill_bookings = TreadmillTimeSlot.objects.filter(user=user).order_by(
            "start_time"
        )
        cycle_bookings = CycleTimeSlot.objects.filter(user=user).order_by("start_time")

        ping_pong_data = ListPingPongTableTimeSlotSerializer(
            ping_pong_bookings, many=True, context={"request": request}
        ).data
        arcade_data = ListArcadeMachineTimeSlotSerializer(
            arcade_machine_bookings, many=True, context={"request": request}
        ).data
        induction_data = ListInductionTimeSlotSerializer(
            induction_bookings, many=True, context={"request": request}
        ).data
        treadmill_data = ListTreadmillTimeSlotSerializer(
            treadmill_bookings, many=True, context={"request": request}
        ).data
        cycle_data = ListCycleTimeSlotSerializer(
            cycle_bookings, many=True, context={"request": request}
        ).data

        response_data = {
            "ping_pong_table_bookings": ping_pong_data,
            "arcade_machine_bookings": arcade_data,
            "induction_bookings": induction_data,
            "treadmill_bookings": treadmill_data,
            "cycle_bookings": cycle_data,
        }

        return Response(response_data, status=status.HTTP_200_OK)
