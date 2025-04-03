from django.urls import path
from .views import *

urlpatterns = [
    path("change-password/", ChangePasswordAPIView.as_view(), name="change password"),
    path("login/", LogInAPIView.as_view(), name="login"),
]
