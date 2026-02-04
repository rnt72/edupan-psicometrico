from django.urls import path

from . import views

app_name = "exams"

urlpatterns = [
    # Vistas principales
    path("", views.ExamListView.as_view(), name="list"),
    path("create/", views.ExamCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.ExamEditorView.as_view(), name="editor"),
    path("<int:pk>/preview/", views.ExamPreviewView.as_view(), name="preview"),
    path("<int:pk>/delete/", views.ExamDeleteView.as_view(), name="delete"),
    # API endpoints para AJAX
    path("api/items/", views.ItemCreateAPI.as_view(), name="api-item-create"),
    path("api/items/<int:pk>/", views.ItemUpdateAPI.as_view(), name="api-item-update"),
    path("api/items/<int:pk>/delete/", views.ItemDeleteAPI.as_view(), name="api-item-delete"),
    path("api/subquestions/", views.SubQuestionCreateAPI.as_view(), name="api-subq-create"),
    path("api/subquestions/<int:pk>/", views.SubQuestionUpdateAPI.as_view(), name="api-subq-update"),
    path("api/subquestions/<int:pk>/delete/", views.SubQuestionDeleteAPI.as_view(), name="api-subq-delete"),
    path("api/options/", views.OptionCreateAPI.as_view(), name="api-option-create"),
    path("api/options/<int:pk>/", views.OptionUpdateAPI.as_view(), name="api-option-update"),
    path("api/options/<int:pk>/delete/", views.OptionDeleteAPI.as_view(), name="api-option-delete"),
]
