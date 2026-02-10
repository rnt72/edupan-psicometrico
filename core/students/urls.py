from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    # API para obtener instituciones filtradas por región (AJAX)
    path(
        "api/institutions/<int:region_pk>/",
        views.InstitutionsByRegionAPI.as_view(),
        name="api-institutions-by-region",
    ),
    # API para crear institución on-the-fly (AJAX)
    path(
        "api/institutions/create/",
        views.InstitutionCreateAPI.as_view(),
        name="api-institution-create",
    ),
]
