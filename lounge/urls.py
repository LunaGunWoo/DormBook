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
    path(
        "arcade-machines/",
        ArcadeMachineListAPIView.as_view(),
        name="arcade-machine-list",
    ),
    path(
        "arcade-machines/<int:pk>/timeslots/",
        ArcadeMachineTimeSlotListAPIView.as_view(),
        name="arcade-machine-timeslot-list",
    ),
    path(
        "arcade-machines/<int:pk>/book/",
        ArcadeMachineTimeSlotBookAPIView.as_view(),
        name="arcade-machine-timeslot-book",
    ),
]
