from django.urls import path
from . import views

urlpatterns = {
    path("fetch_campaigns_by_content_id/", views.fetch_campaigns_by_content_id),
    path("fetch_campaigns_content_list/", views.fetch_campaigns_content_list),
    path("fetch_campaigns_content_list_v2/", views.fetch_campaigns_content_list_v2),
    path("view_content_data/", views.view_content),
    path("deactivate_content/", views.deactivate_content_by_content_id),
    path("content_url_and_subject_line_mapping_action", views.content_url_and_subject_line_mapping_action),
    path("save_content/", views.save_content),
    path("content_action/", views.content_action),
    path("migrate_content/", views.migrate_content_across_projects),
    path("trigger_template_validation", views.trigger_template_validation),
    path("get_template_all_logs", views.get_template_all_logs),
    path("template_sandesh_callback", views.template_sandesh_callback),
    path("local/messageData", views.fetch_campaign_data_by_account_id),
    path("local/route_template_message/", views.route_local_template_message),
    path("local/message_data", views.fetch_campaign_data_by_account_id),
    path("get_template_stats/", views.get_template_stats)
}
