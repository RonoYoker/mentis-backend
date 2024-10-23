from django.urls import path, include

from mentis_proj.apps.assessment.views import *

urlpatterns = [
    path("get_assessment", get_assesment),
    path("get_assessment_result",get_assesment_result)

]

