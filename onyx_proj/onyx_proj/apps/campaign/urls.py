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
    path("validate_test_campaign/", views.validate_test_campaign),
    path("get_dashboard_tab_campaign_data/", views.get_dashboard_tab_campaign_data),
    path("get_campaign_monitoring_stats/", views.get_campaign_monitoring_stats),
    path("update_campaign_stats/", views.update_campaign_stats),
    path("update_campaign_status/", views.update_camp_status_in_camps_tables),
    path("fetch_campaign_lists/", views.fetch_campaign_list),
    path("get_campaign_monitoring_stats_for_admins/", views.get_campaign_monitoring_stats_for_admins),
    path("local/check_test_campaign_validation_status/", views.test_campaign_validation_status_local),
    path("test_campaign_validation_status/", views.test_campaign_validator),
    path("view_campaign/", views.get_campaign_data_by_unique_id),
    path("deactivate_campaign/", views.deactivate_campaign),
    path("approval_action/", views.approval_action_on_campaign_builder),
    path("test_campaign/", views.initiate_test_campaign)
]
