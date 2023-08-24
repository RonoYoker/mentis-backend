from django.urls import path
from . import views

urlpatterns = [
    path("generate_otp/", views.generate_otp),
    path("validate_otp/", views.validate_otp)
    ]