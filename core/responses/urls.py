from django.urls import path

from . import views

app_name = "responses"

urlpatterns = [
    # Dashboard principal
    path("", views.AnalysisDashboardView.as_view(), name="dashboard"),
    # Aplicaciones
    path(
        "application/create/<int:exam_pk>/",
        views.ApplicationCreateView.as_view(),
        name="application-create",
    ),
    path(
        "application/<int:pk>/capture/",
        views.ResponseCaptureView.as_view(),
        name="capture-redirect",
    ),
    path(
        "application/<int:pk>/capture/<int:row_pk>/",
        views.ResponseCaptureView.as_view(),
        name="capture",
    ),
    path(
        "application/<int:pk>/export/",
        views.WinstepsExportView.as_view(),
        name="export",
    ),
    path(
        "application/<int:pk>/delete/",
        views.ApplicationDeleteView.as_view(),
        name="application-delete",
    ),
    # API AJAX
    path(
        "application/<int:pk>/api/save-response/",
        views.SaveResponseAPI.as_view(),
        name="api-save-response",
    ),
    path(
        "application/<int:pk>/api/save-item-score/",
        views.SaveItemScoreAPI.as_view(),
        name="api-save-item-score",
    ),
    path(
        "application/<int:pk>/api/add-row/",
        views.AddRowAPI.as_view(),
        name="api-add-row",
    ),
    path(
        "application/<int:pk>/api/delete-row/",
        views.DeleteRowAPI.as_view(),
        name="api-delete-row",
    ),
]
