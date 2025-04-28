from django.urls import path
from .views import *

urlpatterns = [
    path(
        "ping-pong-tables/",
        PingPongTableListAPIView.as_view(),
        name="ping-pong-table list",
    ),
]
