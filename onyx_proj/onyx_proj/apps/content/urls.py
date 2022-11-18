from django.urls import path
from . import views


urlpatterns = {
    path("fetch_campaigns_by_content_id/", views.fetch_campaigns_by_content_id)
}
