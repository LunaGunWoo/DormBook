from django.urls import path
from .views import *

urlpatterns = [
    path("inductions/", InductionListAPIView.as_view(), name="induction list")
]
