from django.urls import path
from . import views


urlpatterns = {
    path("async_query_execution/", views.invoke_async_query_execution)
}
