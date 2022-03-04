from django.urls import path
from . import views

urlpatterns = [
    path("save_custom_segment/", views.save_custom_segment),
    path("get_segments/", views.get_all_segments),
    path("fetch_headers/", views.fetch_headers_by_segment_id),
    path("header_compatibility_check/", views.check_headers_compatibility)
]
