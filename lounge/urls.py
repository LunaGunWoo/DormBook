from django.urls import path
from .views import *

urlpatterns = [
    path(
        "ping-pong-tables/",
        PingPongTableListAPIView.as_view(),
        name="ping-pong-table-list",
    ),
    path(
        "ping-pong-tables/<int:pk>/timeslots/",
        PingPongTableTimeSlotListAPIView.as_view(),
        name="ping-pong-table-timeslot-list",
    ),
    path(
        "ping-pong-tables/<int:pk>/book/",
        PingPongTableTimeSlotBookAPIView.as_view(),
        name="ping-pong-table-timeslot-book",
    ),
]
