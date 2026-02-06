from django.conf import settings
from django.db import models


class ExamApplication(models.Model):
    """Sesión de aplicación de un examen (ej: 'Aplicación Marzo 2026')"""

    exam = models.ForeignKey(
        "exams.Exam",
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name="Examen",
    )
    name = models.CharField(
        "Nombre de la aplicación",
        max_length=255,
        help_text="Ej: Aplicación Marzo 2026",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="applications_created",
        verbose_name="Creado por",
    )
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)

    class Meta:
        verbose_name = "Aplicación de Examen"
        verbose_name_plural = "Aplicaciones de Examen"
        ordering = ["-created_at"]
        unique_together = ["exam", "name"]

    def __str__(self):
        return f"{self.name} - {self.exam.name}"

    def total_rows(self):
        return self.rows.count()


class ResponseRow(models.Model):
    """Fila de respuestas (un alumno anónimo identificado solo por número)"""

    application = models.ForeignKey(
        ExamApplication,
        on_delete=models.CASCADE,
        related_name="rows",
        verbose_name="Aplicación",
    )
    row_number = models.PositiveIntegerField("Número de fila")

    class Meta:
        verbose_name = "Fila de Respuesta"
        verbose_name_plural = "Filas de Respuesta"
        ordering = ["row_number"]
        unique_together = ["application", "row_number"]

    def __str__(self):
        return f"Alumno {self.row_number} - {self.application.name}"


class Response(models.Model):
    """Respuesta individual: qué opción eligió un alumno en una subpregunta"""

    row = models.ForeignKey(
        ResponseRow,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name="Fila",
    )
    subquestion = models.ForeignKey(
        "exams.SubQuestion",
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name="Subpregunta",
    )
    selected_option = models.ForeignKey(
        "exams.Option",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responses",
        verbose_name="Opción seleccionada",
    )
    is_correct = models.BooleanField("Es correcta", default=False)

    class Meta:
        verbose_name = "Respuesta"
        verbose_name_plural = "Respuestas"
        unique_together = ["row", "subquestion"]

    def __str__(self):
        option_label = self.selected_option.label if self.selected_option else "—"
        return f"Alumno {self.row.row_number} → {self.subquestion} = {option_label}"

    def save(self, *args, **kwargs):
        """Auto-calcula is_correct basado en selected_option.is_correct"""
        if self.selected_option:
            self.is_correct = self.selected_option.is_correct
        else:
            self.is_correct = False
        # Asegurar que is_correct se guarde cuando update_or_create pasa update_fields
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'is_correct' not in update_fields:
            kwargs['update_fields'] = list(update_fields) + ['is_correct']
        super().save(*args, **kwargs)


class ItemScore(models.Model):
    """Puntuación directa a nivel de ítem (para preguntas abiertas o scoring manual)"""

    row = models.ForeignKey(
        ResponseRow,
        on_delete=models.CASCADE,
        related_name="item_scores",
        verbose_name="Fila",
    )
    item = models.ForeignKey(
        "exams.Item",
        on_delete=models.CASCADE,
        related_name="scores",
        verbose_name="Ítem",
    )
    score = models.PositiveIntegerField(
        "Puntuación",
        default=0,
        help_text="0=Incorrecta, 1=Parcialmente correcta, 2=Correcta",
    )

    class Meta:
        verbose_name = "Puntuación de Ítem"
        verbose_name_plural = "Puntuaciones de Ítems"
        unique_together = ["row", "item"]

    def __str__(self):
        return f"Alumno {self.row.row_number} → {self.item.code} = {self.score}"
