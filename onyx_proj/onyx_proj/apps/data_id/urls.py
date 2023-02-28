from django.urls import path
from . import views

urlpatterns = [
    path("fetch_data_id_details/", views.get_data_id_details_by_project_id)
]
