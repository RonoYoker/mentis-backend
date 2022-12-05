from django.urls import path
from . import views

urlpatterns = [
    path("self/", views.get_user)
]