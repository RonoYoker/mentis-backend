from django.urls import path
from onyx_proj.apps.home import views

urlpatterns = [
    path("", views.index, name="home"),
    path("ping", views.ping, name="health check")
]
