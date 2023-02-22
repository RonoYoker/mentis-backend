from django.urls import path
from . import views


urlpatterns = {
    path("fetch_campaigns_by_content_id/", views.fetch_campaigns_by_content_id),
    path("fetch_campaigns_content_list/", views.fetch_campaigns_content_list),
    path("view_content_data/", views.view_content)
}
