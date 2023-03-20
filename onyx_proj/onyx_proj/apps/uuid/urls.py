from django.urls import path
from . import views

urlpatterns = [
    path("get_uuid_info/", views.get_uuid_info_local),
]
