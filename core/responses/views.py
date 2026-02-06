import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView

from core.exams.models import Exam
from core.exams.models import Item
from core.exams.models import Option
from core.exams.models import SubQuestion

from .models import ExamApplication
from .models import ItemScore
from .models import Response
from .models import ResponseRow


class AnalysisDashboardView(LoginRequiredMixin, ListView):
    """Dashboard principal de análisis: lista exámenes con sus aplicaciones"""

    model = Exam
    template_name = "pages/analysis-dashboard.html"
    context_object_name = "exams"

    def get_queryset(self):
        return Exam.objects.filter(is_active=True).prefetch_related("applications")


class ApplicationCreateView(LoginRequiredMixin, View):
    """Crear nueva aplicación de examen"""

    template_name = "pages/application-create.html"

    def get(self, request, exam_pk):
        exam = get_object_or_404(Exam, pk=exam_pk)
        return render(request, self.template_name, {"exam": exam})

    def post(self, request, exam_pk):
        exam = get_object_or_404(Exam, pk=exam_pk)
        name = request.POST.get("name", "").strip()
        num_rows = request.POST.get("num_rows", "10")

        errors = {}
        if not name:
            errors["name"] = "El nombre es obligatorio"

        try:
            num_rows = int(num_rows)
            if num_rows < 1 or num_rows > 500:
                errors["num_rows"] = "Debe ser entre 1 y 500"
        except (ValueError, TypeError):
            errors["num_rows"] = "Debe ser un número válido"

        if ExamApplication.objects.filter(exam=exam, name=name).exists():
            errors["name"] = "Ya existe una aplicación con ese nombre para este examen"

        if errors:
            return render(request, self.template_name, {
                "exam": exam,
                "errors": errors,
                "form_data": {"name": name, "num_rows": num_rows},
            })

        application = ExamApplication.objects.create(
            exam=exam,
            name=name,
            created_by=request.user,
        )

        # Crear filas (alumnos anónimos)
        rows = [
            ResponseRow(application=application, row_number=i)
            for i in range(1, num_rows + 1)
        ]
        ResponseRow.objects.bulk_create(rows)

        # Redirigir a captura del primer alumno
        first_row = application.rows.first()
        return redirect("responses:capture", pk=application.pk, row_pk=first_row.pk)


class ResponseCaptureView(LoginRequiredMixin, View):
    """Vista de captura: muestra el examen y el digitador responde sobre él, alumno por alumno"""

    template_name = "pages/response-capture.html"

    def get(self, request, pk, row_pk=None):
        application = get_object_or_404(
            ExamApplication.objects.select_related("exam"),
            pk=pk,
        )
        exam = application.exam

        # Si no viene row_pk, redirigir al primer alumno
        if row_pk is None:
            first_row = application.rows.order_by("row_number").first()
            if first_row is None:
                # No hay filas, crear una
                first_row = ResponseRow.objects.create(application=application, row_number=1)
            return redirect("responses:capture", pk=application.pk, row_pk=first_row.pk)

        current_row = get_object_or_404(ResponseRow, pk=row_pk, application=application)

        # Todas las filas para navegación
        all_rows = list(application.rows.order_by("row_number"))

        # Posición actual para prev/next
        current_index = next(
            (i for i, r in enumerate(all_rows) if r.pk == current_row.pk), 0
        )
        prev_row = all_rows[current_index - 1] if current_index > 0 else None
        next_row = all_rows[current_index + 1] if current_index < len(all_rows) - 1 else None

        # Obtener ítems con subpreguntas y opciones
        items = (
            exam.items.prefetch_related("subquestions__options")
            .order_by("order")
        )

        # Respuestas existentes de este alumno (por subpregunta)
        existing_responses = {}
        for resp in Response.objects.filter(
            row=current_row
        ).select_related("selected_option"):
            existing_responses[resp.subquestion_id] = {
                "option_id": resp.selected_option_id,
                "is_correct": resp.is_correct,
            }

        # Puntuaciones directas de este alumno (por ítem)
        existing_item_scores = {}
        for iscore in ItemScore.objects.filter(row=current_row):
            existing_item_scores[iscore.item_id] = iscore.score

        return render(request, self.template_name, {
            "application": application,
            "exam": exam,
            "items": items,
            "current_row": current_row,
            "all_rows": all_rows,
            "prev_row": prev_row,
            "next_row": next_row,
            "existing_responses": existing_responses,
            "existing_responses_json": json.dumps(existing_responses),
            "existing_item_scores": existing_item_scores,
            "existing_item_scores_json": json.dumps(existing_item_scores),
        })


class SaveResponseAPI(LoginRequiredMixin, View):
    """API AJAX: guarda la opción seleccionada para una subpregunta"""

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        application = get_object_or_404(ExamApplication, pk=pk)
        row_id = data.get("row_id")
        subquestion_id = data.get("subquestion_id")
        option_id = data.get("option_id")

        row = get_object_or_404(ResponseRow, pk=row_id, application=application)
        subquestion = get_object_or_404(SubQuestion, pk=subquestion_id)

        if option_id:
            option = get_object_or_404(Option, pk=option_id, subquestion=subquestion)
        else:
            option = None

        response, _created = Response.objects.update_or_create(
            row=row,
            subquestion=subquestion,
            defaults={"selected_option": option},
        )

        # Auto-calcular el ItemScore del ítem padre
        item = subquestion.item
        auto_score = self._calculate_item_score(row, item)

        # Guardar el ItemScore automáticamente
        ItemScore.objects.update_or_create(
            row=row,
            item=item,
            defaults={"score": auto_score},
        )

        return JsonResponse({
            "success": True,
            "is_correct": response.is_correct,
            "option_id": response.selected_option_id,
            "item_id": item.id,
            "item_auto_score": auto_score,
        })

    def _calculate_item_score(self, row, item):
        """Calcula el score del ítem basado en las respuestas de sus subpreguntas"""
        subqs = list(item.subquestions.order_by("order"))
        if not subqs:
            return 0

        responses = Response.objects.filter(
            row=row,
            subquestion__in=subqs,
        )
        correct_count = responses.filter(is_correct=True).count()
        total = len(subqs)

        if item.scoring_type == "D":
            return 1 if correct_count == total else 0
        else:
            # Politómico
            if correct_count == 0:
                return 0
            elif correct_count == total:
                return 2
            else:
                return 1


class SaveItemScoreAPI(LoginRequiredMixin, View):
    """API AJAX: guarda puntuación directa a nivel de ítem (preguntas abiertas)"""

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        application = get_object_or_404(ExamApplication, pk=pk)
        row_id = data.get("row_id")
        item_id = data.get("item_id")
        score = data.get("score")

        row = get_object_or_404(ResponseRow, pk=row_id, application=application)
        item = get_object_or_404(Item, pk=item_id, exam=application.exam)

        # Validar score según tipo
        if item.scoring_type == "D":
            if score not in (0, 1):
                return JsonResponse({"error": "Score dicotómico debe ser 0 o 1"}, status=400)
        else:
            if score not in (0, 1, 2):
                return JsonResponse({"error": "Score politómico debe ser 0, 1 o 2"}, status=400)

        item_score, _created = ItemScore.objects.update_or_create(
            row=row,
            item=item,
            defaults={"score": score},
        )

        return JsonResponse({
            "success": True,
            "item_id": item.id,
            "score": item_score.score,
        })


class AddRowAPI(LoginRequiredMixin, View):
    """API AJAX: agrega una nueva fila/alumno"""

    def post(self, request, pk):
        application = get_object_or_404(ExamApplication, pk=pk)
        max_row = application.rows.aggregate(
            max_num=Max("row_number")
        )["max_num"] or 0

        new_row = ResponseRow.objects.create(
            application=application,
            row_number=max_row + 1,
        )

        return JsonResponse({
            "success": True,
            "row_id": new_row.id,
            "row_number": new_row.row_number,
        })


class DeleteRowAPI(LoginRequiredMixin, View):
    """API AJAX: elimina la última fila de la grilla"""

    def delete(self, request, pk):
        application = get_object_or_404(ExamApplication, pk=pk)
        last_row = application.rows.order_by("-row_number").first()

        if not last_row:
            return JsonResponse({"error": "No hay filas"}, status=400)

        last_row.delete()
        return JsonResponse({"success": True})


class WinstepsExportView(LoginRequiredMixin, View):
    """Genera y descarga archivo .txt compatible con Winsteps.
    
    Prioridad: usa ItemScore (puntuación directa) si existe,
    sino calcula desde las respuestas por subpregunta.
    """

    def get(self, request, pk):
        application = get_object_or_404(
            ExamApplication.objects.select_related("exam"),
            pk=pk,
        )
        exam = application.exam

        # Obtener ítems ordenados
        items = list(
            exam.items.prefetch_related("subquestions").order_by("order")
        )

        # Obtener todas las filas
        rows = application.rows.order_by("row_number")

        # Cargar todos los ItemScores
        all_item_scores = {}
        for iscore in ItemScore.objects.filter(row__application=application):
            all_item_scores[(iscore.row_id, iscore.item_id)] = iscore.score

        # Cargar respuestas por subpregunta como fallback
        all_responses = {}
        for resp in Response.objects.filter(row__application=application):
            all_responses[(resp.row_id, resp.subquestion_id)] = resp.is_correct

        # Generar líneas del archivo
        lines = []
        for row in rows:
            score_string = ""
            for item in items:
                # Prioridad: ItemScore directo
                direct_score = all_item_scores.get((row.id, item.id))
                if direct_score is not None:
                    score_string += str(direct_score)
                else:
                    # Fallback: calcular desde subpreguntas
                    subqs = list(item.subquestions.order_by("order"))
                    if not subqs:
                        continue

                    correct_count = sum(
                        1 for sq in subqs
                        if all_responses.get((row.id, sq.id), False)
                    )
                    total = len(subqs)

                    if item.scoring_type == "D":
                        score_string += "1" if correct_count == total else "0"
                    else:
                        if correct_count == 0:
                            score_string += "0"
                        elif correct_count == total:
                            score_string += "2"
                        else:
                            score_string += "1"

            lines.append(score_string)

        content = "\n".join(lines)
        filename = f"winsteps_{exam.name.replace(' ', '_')}_{application.name.replace(' ', '_')}.txt"

        response = HttpResponse(content, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ApplicationDeleteView(LoginRequiredMixin, View):
    """Eliminar aplicación vía AJAX"""

    def delete(self, request, pk):
        application = get_object_or_404(ExamApplication, pk=pk)
        application.delete()
        return JsonResponse({"success": True})
