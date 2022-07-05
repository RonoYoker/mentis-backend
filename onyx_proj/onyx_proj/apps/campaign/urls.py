from django.urls import path
from . import views

urlpatterns = [
    path("get_test_campaign_data/", views.get_test_campaign_data),
    path("save_campaign_data/", views.save_campaign_data),
    path("get_min_max_date/", views.get_min_max_date),
    path("get_time_range_for_date/", views.get_time_range_for_date),
    path("get_vendor_config_data/", views.get_vendor_config_data),
    path("get_campaign_data_for_period/", views.get_campaign_data_for_period),
    path("update_campaign_progress_status/", views.update_campaign_progress_status),
    path("generate_recurring_schedule/", views.generate_recurring_schedule),
    path("validate_recurring_campaign/", views.validate_recurring_campaign),
    path("get_campaign_monitoring_stats/", views.get_campaign_monitoring_stats),
    path("update_campaign_stats/", views.update_campaign_stats)
]
