from django.urls import path
from .views import *

urlpatterns = [
    path("inductions/", InductionListAPIView.as_view(), name="induction list"),
    path(
        "inductions/<int:pk>/timeslots/",
        InductionTimeSlotListAPIView.as_view(),
        name="induction-timeslot list",
    ),
    path(
        "inductions/<int:pk>/book/",
        InductionTimeSlotBookAPIView.as_view(),
        name="induction-timeslot book",
    ),
]
