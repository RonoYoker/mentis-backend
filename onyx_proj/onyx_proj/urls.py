"""onyx_proj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from onyx_proj.apps.project import urls as project
from onyx_proj.apps.segments import urls as segment_urls
from onyx_proj.apps.campaign import urls as campaign_urls
from onyx_proj.apps.home import urls as home_urls
from onyx_proj.apps.slot_management import urls as slot_urls
from onyx_proj.apps.name_matcher import urls as name_matcher_urls
from onyx_proj.apps.user import urls as user_urls
from onyx_proj.apps.content import urls as content_urls
from onyx_proj.apps.data_id import urls as dataid_urls
from onyx_proj.apps.file_processing import urls as file_process_route_urls
from onyx_proj.apps.async_task_invocation import urls as async_task_urls
from onyx_proj.apps.uuid import urls as uuid_urls
from onyx_proj.apps.admin import urls as admin_controller

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(home_urls)),
    path("segments/", include(segment_urls)),
    path("campaign/", include(campaign_urls)),
    path("slots/", include(slot_urls)),
    path("name_matcher/", include(name_matcher_urls)),
    path("user/", include(user_urls)),
    path("content/", include(content_urls)),
    path("local/async_task_invocation/", include(async_task_urls)),
    path("local/uuid/", include(uuid_urls)),
    path("data_id/", include(dataid_urls)),
    path("content/", include(content_urls)),
    path("file_processing/", include(file_process_route_urls)),
    path("project/", include(project)),
    path("admin_controller/", include(admin_controller))
]
