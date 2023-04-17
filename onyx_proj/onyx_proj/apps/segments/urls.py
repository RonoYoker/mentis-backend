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
    path("process_save_segment_callback/", views.custom_segment_callback),
    path("update_segment_data/", views.update_segment_callback),
    path("segment_records_count/", views.segment_records_count),
    path("fetch_segment_list/", views.fetch_segments_list),
    path("old_segment_tagging/", views.update_segment_tags),
    path("update_custom_segment_callback/", views.update_custom_segment_callback),
    path("deactivate_segment/", views.deactivate_segment),
    path("get_master_mapping_for_segment/", views.get_master_mapping_by_data_id),
    path("back_fill_encrypted_data/", views.back_fill_segment_data)

]
