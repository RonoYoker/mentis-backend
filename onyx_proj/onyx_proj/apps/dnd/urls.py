from django.urls import path
from . import views

urlpatterns = [
    path("local/update_dnd/", views.update_dnd)
    ]