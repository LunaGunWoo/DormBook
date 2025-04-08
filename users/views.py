from django.contrib.auth import login, authenticate, logout
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from .serializers import *
from .models import *


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
            login(request=request, user=self.object)
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
    model = User

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student_id_number = serializer.data.get("student_id_number")
        password = serializer.data.get("password")
        user = authenticate(
            request=request,
            student_id_number=student_id_number,
            password=password,
        )

        if user is not None:
            login(request, user)
            return Response({"detail": "로그인 성공"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "로그인 실패"}, status=status.HTTP_401_UNAUTHORIZED
            )


class LogOutAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logout(request=request)
        return Response({"detail": "로그아웃 성공"}, status=status.HTTP_200_OK)
