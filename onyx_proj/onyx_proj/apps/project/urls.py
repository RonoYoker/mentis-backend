from django.urls import path
from . import views

urlpatterns = [
    path("get_project_list/", views.get_project_list)
    ]
