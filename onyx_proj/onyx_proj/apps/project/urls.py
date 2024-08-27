from django.urls import path
from . import views

urlpatterns = [
    path("get_project_list/", views.get_project_list),
    path("update_data_ingestion_updates/", views.update_data_ingestion_updates),
    path("project_ingest/", views.auto_project_ingestion),
    path("local/insert_project_details_in_local/", views.insert_project_details_in_local),

    ]
