from django.urls import path
from . import views

urlpatterns = [
    path("get_uuid_info/", views.get_uuid_info_local),
    path("get_encrypted_data/", views.get_encrypted_data),
    path("get_decrypted_data/", views.get_decrypted_data),
    path("generate_uuid_data/", views.generate_uuid_data),
    path("generate_short_url/", views.generate_short_url_data),
]
