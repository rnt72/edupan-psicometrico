from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template import TemplateDoesNotExist


@login_required
def root_page_view(request):
    return redirect("exams:list")


@login_required
def dynamic_pages_view(request, template_name):
    try:
        return render(request, f'pages/{template_name}.html')
    except TemplateDoesNotExist:
        return render(request, f'pages/pages-404.html')
