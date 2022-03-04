from django.urls import path
from . import views

urlpatterns = [
    path("saveCustomSegment/", views.save_custom_segment),
    path("getSegments/", views.get_all_segments),
    path("fetchHeaders/", views.fetch_headers_by_segment_id),
    path("headerCompatibilityCheck/", views.check_headers_compatibility)
]
