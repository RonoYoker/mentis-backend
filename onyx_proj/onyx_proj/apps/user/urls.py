from django.urls import path
from . import views

urlpatterns = [
    path("self/", views.get_user),
    path("user/", views.get_user_detail),
    path("update_user/", views.update_user),
    path("save_user/", views.save_user),
    path("session/", views.update_project_session)

]