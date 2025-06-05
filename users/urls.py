from django.urls import path
from .views import (
    ChangePasswordAPIView,
    LogInAPIView,
    LogOutAPIView,
    MyAllBookingsListAPIView,
)

urlpatterns = [
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path("login/", LogInAPIView.as_view(), name="login"),
    path("logout/", LogOutAPIView.as_view(), name="logout"),
    path("my-bookings/", MyAllBookingsListAPIView.as_view(), name="my-all-bookings"),
]
