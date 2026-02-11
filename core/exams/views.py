import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView

from .models import Exam
from .models import Item
from .models import Option
from .models import SubQuestion


class ExamListView(LoginRequiredMixin, ListView):
    """Lista de exámenes"""

    model = Exam
    template_name = "pages/exam-list.html"
    context_object_name = "exams"
    paginate_by = 10

    def get_queryset(self):
        queryset = Exam.objects.select_related("created_by")
        search = self.request.GET.get("search")

        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        return context


class ExamCreateView(LoginRequiredMixin, View):
    """Crear nuevo examen"""

    template_name = "pages/exam-create.html"

    def get(self, request):
        from django.shortcuts import render

        return render(request, self.template_name)

    def post(self, request):
        from django.shortcuts import redirect, render

        name = request.POST.get("name", "").strip()

        # Validaciones
        errors = {}
        if not name:
            errors["name"] = "El nombre es obligatorio"

        if errors:
            return render(request, self.template_name, {"errors": errors})

        # Crear examen
        exam = Exam.objects.create(
            name=name,
            created_by=request.user,
        )

        return redirect("exams:editor", pk=exam.pk)


class ExamEditorView(LoginRequiredMixin, DetailView):
    """Editor de ítems del examen"""

    model = Exam
    template_name = "pages/exam-editor.html"
    context_object_name = "exam"

    def get_queryset(self):
        return Exam.objects.prefetch_related(
            "items__subquestions__options",
        ).select_related("created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = self.object.items.all().order_by("order")
        return context


class ExamPreviewView(LoginRequiredMixin, DetailView):
    """Vista previa del examen"""

    model = Exam
    template_name = "pages/exam-preview.html"
    context_object_name = "exam"

    def get_queryset(self):
        return Exam.objects.prefetch_related(
            "items__subquestions__options",
        ).select_related("created_by")


class ExamDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar examen"""

    model = Exam
    success_url = reverse_lazy("exams:list")

    def delete(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            self.object = self.get_object()
            self.object.delete()
            return JsonResponse({"success": True})
        return super().delete(request, *args, **kwargs)


# =============================================================================
# API Views para AJAX
# =============================================================================


class BaseAPIView(LoginRequiredMixin, View):
    """Vista base para API con manejo de JSON"""

    def get_json_data(self):
        try:
            return json.loads(self.request.body)
        except json.JSONDecodeError:
            return {}


class ItemCreateAPI(BaseAPIView):
    """Crear nuevo ítem"""

    def post(self, request):
        data = self.get_json_data()
        exam = get_object_or_404(Exam, pk=data.get("exam_id"))

        # Obtener el siguiente orden
        max_order = exam.items.aggregate(Max("order"))["order__max"] or 0

        item = Item.objects.create(
            exam=exam,
            code=data.get("code", ""),
            instruction=data.get("instruction", ""),
            scoring_type=data.get("scoring_type", Item.SCORING_DICHOTOMOUS),
            order=max_order + 1,
            correct_criteria=data.get("correct_criteria", ""),
            partial_criteria=data.get("partial_criteria", ""),
            incorrect_criteria=data.get("incorrect_criteria", ""),
        )

        return JsonResponse({
            "success": True,
            "item": {
                "id": item.id,
                "code": item.code,
                "instruction": item.instruction,
                "order": item.order,
                "scoring_type": item.scoring_type,
            },
        })


class ItemUpdateAPI(BaseAPIView):
    """Actualizar ítem existente"""

    def put(self, request, pk):
        data = self.get_json_data()
        item = get_object_or_404(Item, pk=pk)

        item.code = data.get("code", item.code)
        item.instruction = data.get("instruction", item.instruction)
        item.scoring_type = data.get("scoring_type", item.scoring_type)
        item.order = data.get("order", item.order)
        item.correct_criteria = data.get("correct_criteria", item.correct_criteria)
        item.partial_criteria = data.get("partial_criteria", item.partial_criteria)
        item.incorrect_criteria = data.get("incorrect_criteria", item.incorrect_criteria)
        item.save()

        return JsonResponse({
            "success": True,
            "item": {
                "id": item.id,
                "code": item.code,
                "instruction": item.instruction,
                "order": item.order,
            },
        })


class ItemDeleteAPI(BaseAPIView):
    """Eliminar ítem"""

    def delete(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        item.delete()
        return JsonResponse({"success": True})


class SubQuestionCreateAPI(BaseAPIView):
    """Crear nueva subpregunta"""

    def post(self, request):
        data = self.get_json_data()
        item = get_object_or_404(Item, pk=data.get("item_id"))

        # Obtener el siguiente orden
        max_order = item.subquestions.aggregate(Max("order"))["order__max"] or 0

        subq = SubQuestion.objects.create(
            item=item,
            order=max_order + 1,
            context_text=data.get("context_text", ""),
            question_type=data.get("question_type", SubQuestion.TYPE_CLOSED),
        )

        return JsonResponse({
            "success": True,
            "subquestion": {
                "id": subq.id,
                "order": subq.order,
                "context_text": subq.context_text,
                "question_type": subq.question_type,
            },
        })


class SubQuestionUpdateAPI(BaseAPIView):
    """Actualizar subpregunta"""

    def put(self, request, pk):
        data = self.get_json_data()
        subq = get_object_or_404(SubQuestion, pk=pk)

        subq.order = data.get("order", subq.order)
        subq.context_text = data.get("context_text", subq.context_text)
        subq.question_type = data.get("question_type", subq.question_type)
        subq.save()

        # Si cambió a tipo abierto, eliminar opciones existentes
        if subq.question_type == SubQuestion.TYPE_OPEN:
            subq.options.all().delete()

        return JsonResponse({
            "success": True,
            "subquestion": {
                "id": subq.id,
                "order": subq.order,
            },
        })


class SubQuestionDeleteAPI(BaseAPIView):
    """Eliminar subpregunta"""

    def delete(self, request, pk):
        subq = get_object_or_404(SubQuestion, pk=pk)
        subq.delete()
        return JsonResponse({"success": True})


class OptionCreateAPI(BaseAPIView):
    """Crear nueva opción"""

    def post(self, request):
        data = self.get_json_data()
        subq = get_object_or_404(SubQuestion, pk=data.get("subquestion_id"))

        # Obtener el siguiente orden y label
        max_order = subq.options.aggregate(Max("order"))["order__max"] or 0
        labels = ["a", "b", "c", "d", "e", "f"]
        next_label = labels[min(max_order, len(labels) - 1)]

        option = Option.objects.create(
            subquestion=subq,
            label=data.get("label", next_label),
            text=data.get("text", ""),
            is_correct=data.get("is_correct", False),
            order=max_order + 1,
        )

        return JsonResponse({
            "success": True,
            "option": {
                "id": option.id,
                "label": option.label,
                "text": option.text,
                "is_correct": option.is_correct,
                "order": option.order,
            },
        })


class OptionUpdateAPI(BaseAPIView):
    """Actualizar opción"""

    def put(self, request, pk):
        data = self.get_json_data()
        option = get_object_or_404(Option, pk=pk)

        option.label = data.get("label", option.label)
        option.text = data.get("text", option.text)
        option.is_correct = data.get("is_correct", option.is_correct)
        option.order = data.get("order", option.order)
        option.save()

        return JsonResponse({
            "success": True,
            "option": {
                "id": option.id,
                "label": option.label,
                "text": option.text,
                "is_correct": option.is_correct,
            },
        })


class OptionDeleteAPI(BaseAPIView):
    """Eliminar opción"""

    def delete(self, request, pk):
        option = get_object_or_404(Option, pk=pk)
        option.delete()
        return JsonResponse({"success": True})
