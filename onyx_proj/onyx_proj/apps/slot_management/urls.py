from django.urls import path, include
from . import views

urlpatterns = [
    path("check_availability/", views.check_availability)
]
