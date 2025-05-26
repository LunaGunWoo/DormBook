from django.urls import path
from .views import (
    TreadmillListAPIView,
    TreadmillTimeSlotListAPIView,
    TreadmillTimeSlotBookAPIView,
    CycleListAPIView,
    CycleTimeSlotListAPIView,
    CycleTimeSlotBookAPIView,
)

urlpatterns = [
    path(
        "treadmills/",
        TreadmillListAPIView.as_view(),
        name="treadmill-list",
    ),
    path(
        "treadmills/<int:pk>/timeslots/",
        TreadmillTimeSlotListAPIView.as_view(),
        name="treadmill-timeslot-list",
    ),
    path(
        "treadmills/<int:pk>/book/",
        TreadmillTimeSlotBookAPIView.as_view(),
        name="treadmill-timeslot-book",
    ),
    path(
        "cycles/",
        CycleListAPIView.as_view(),
        name="cycle-list",
    ),
    path(
        "cycles/<int:pk>/timeslots/",
        CycleTimeSlotListAPIView.as_view(),
        name="cycle-timeslot-list",
    ),
    path(
        "cycles/<int:pk>/book/",
        CycleTimeSlotBookAPIView.as_view(),
        name="cycle-timeslot-book",
    ),
]
