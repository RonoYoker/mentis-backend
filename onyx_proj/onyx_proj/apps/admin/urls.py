from django.urls import path
from . import views

urlpatterns = [
    path("get_user_role/", views.get_user_role),
    path("get_role_permissions/", views.get_role_permissions),
    path("save_user_role/", views.save_user_role)
    ]
