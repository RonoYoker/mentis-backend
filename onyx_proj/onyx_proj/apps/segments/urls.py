from django.urls import path
from . import views

urlpatterns = [
    path("save_custom_segment/", views.save_custom_segment),
    path("get_segments/", views.get_all_segments),
    path("fetch_headers/", views.fetch_headers_by_segment_id),
    path("header_compatibility_check/", views.check_headers_compatibility),
    path("get_segment_by_unique_id/", views.get_segment_by_unique_id),
    path("update_custom_segment/", views.update_custom_segment),
    path("update_segment_refresh_count/", views.update_segment_refresh_count),
    path("segment_refresh_count/", views.segment_refresh_count),
    path("get_sample_data/", views.fetch_sample_data),
    path("segment_records_count/",views.segment_records_count)
]
