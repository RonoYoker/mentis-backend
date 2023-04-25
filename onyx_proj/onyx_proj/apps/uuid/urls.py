from django.urls import path
from . import views

urlpatterns = [
    path("get_uuid_info/", views.get_uuid_info_local),
    path("get_encrypted_data/", views.get_encrypted_data),
]
