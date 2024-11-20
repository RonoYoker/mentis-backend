from django.template.loader import render_to_string
from django.shortcuts import HttpResponse


def main(request):
    rendered_page = render_to_string('mentis/base.html')
    return HttpResponse(rendered_page)