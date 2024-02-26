from django.urls import path
from . import views

urlpatterns = [
    path("strategy_action/", views.strategy_action),
    path("fetch_strategy_lists/", views.fetch_strategy_list),
    path("view_strategy/", views.view_strategy),
    path("save_strategy/", views.save_strategy),
    path("get_strategy_schedule_details/", views.get_strategy_campaign_schedule_details)
]
