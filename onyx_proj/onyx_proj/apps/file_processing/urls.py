from django.urls import path
from . import views


urlpatterns = {
    path("get_file_headers/", views.get_file_headers_by_data_id)
}
