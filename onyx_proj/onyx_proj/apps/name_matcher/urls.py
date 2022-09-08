from django.urls import path
from . import views

urlpatterns = [
    path("get_similarity/", views.get_similarity),
    path("get_similarity_v2/", views.get_similarity_v2),
    path("compare_with_payu/", views.compare_with_payu),
    path("get_names_similarity/",views.compare_names)

]
