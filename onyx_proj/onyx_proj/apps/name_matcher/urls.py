from django.urls import path
from . import views

urlpatterns = [
    path("get_similarity/", views.get_similarity),
    path("compare_with_payu/", views.compare_with_payu),

]
