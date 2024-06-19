from django.urls import path
from . import views

urlpatterns = [
    path("strategy_action/", views.strategy_action),
    path("fetch_strategy_lists/", views.fetch_strategy_list),
    path("view_strategy/", views.view_strategy),
    path("save_strategy/", views.save_strategy),
    path("get_strategy_schedule_details/", views.get_strategy_campaign_schedule_details),
    path("save_strategy_configuration/", views.save_strategy_configuration),
    path("strategy_configuration_action/", views.configuration_action),
    path("trigger_strategy/", views.trigger_strategy),
    path("view_configuration/", views.view_configuration),
    path("get_configuration_schedule_details/", views.get_configuration_campaign_schedule_details),
    path("fetch_configuration_lists/", views.fetch_configuration_list),

]
