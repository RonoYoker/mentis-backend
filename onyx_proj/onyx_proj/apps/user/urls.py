from django.urls import path
from . import views

urlpatterns = [
    path("self/", views.get_user),
    path("user/", views.get_user_projects),
    path("update_user/", views.update_user_projects),
    path("save_user/", views.save_user_projects),
    path("session/", views.update_project_session)

]