from django.conf import settings
from django.db import models
from django.urls import reverse


class GradeLevel(models.Model):
    """Nivel de grado escolar (ej: 2do-3er Grado, 4to-5to Grado)"""

    name = models.CharField("Nombre", max_length=100)
    code = models.CharField("Código", max_length=10, unique=True)
    order = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Nivel de Grado"
        verbose_name_plural = "Niveles de Grado"
        ordering = ["order"]

    def __str__(self):
        return self.name


class SubjectArea(models.Model):
    """Área o materia (ej: Español, Matemáticas)"""

    name = models.CharField("Nombre", max_length=100)
    code = models.CharField("Código", max_length=10, unique=True)

    class Meta:
        verbose_name = "Área/Materia"
        verbose_name_plural = "Áreas/Materias"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Exam(models.Model):
    """Plantilla de examen psicométrico"""

    name = models.CharField("Nombre del Examen", max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="exams_created",
        verbose_name="Creado por",
    )
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Examen"
        verbose_name_plural = "Exámenes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.grade_level} ({self.subject_area})"

    def get_absolute_url(self):
        return reverse("exams:editor", kwargs={"pk": self.pk})


class Item(models.Model):
    """Ítem/Pregunta principal con código único (ej: EA01, EA02)"""

    SCORING_DICHOTOMOUS = "D"
    SCORING_POLYTOMOUS = "P"
    SCORING_CHOICES = [
        (SCORING_DICHOTOMOUS, "Dicotómico (0=incorrecto, 1=correcto)"),
        (SCORING_POLYTOMOUS, "Politómico (0=incorrecto, 1=parcial, 2=correcto)"),
    ]

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Examen",
    )
    code = models.CharField("Código", max_length=20, help_text="Ej: EA01, EA02")
    order = models.PositiveIntegerField("Orden", default=0)
    instruction = models.TextField(
        "Instrucción",
        help_text="Ej: ¿Qué se ve en el dibujo? Marca la palabra correcta.",
    )
    image = models.ImageField(
        "Imagen",
        upload_to="exams/items/",
        blank=True,
        null=True,
    )
    scoring_type = models.CharField(
        "Tipo de Calificación",
        max_length=1,
        choices=SCORING_CHOICES,
        default=SCORING_DICHOTOMOUS,
    )

    # Criterios de calificación para Winsteps
    correct_criteria = models.TextField(
        "Criterio Correcta",
        blank=True,
        help_text="Descripción de cuándo la respuesta es correcta",
    )
    partial_criteria = models.TextField(
        "Criterio Parcialmente Correcta",
        blank=True,
        help_text="Descripción de cuándo la respuesta es parcialmente correcta",
    )
    incorrect_criteria = models.TextField(
        "Criterio Incorrecta",
        blank=True,
        help_text="Descripción de cuándo la respuesta es incorrecta",
    )

    class Meta:
        verbose_name = "Ítem"
        verbose_name_plural = "Ítems"
        ordering = ["order"]
        unique_together = ["exam", "code"]

    def __str__(self):
        return f"{self.code} - {self.instruction[:50]}"


class SubQuestion(models.Model):
    """Subpregunta dentro de un ítem (puede haber múltiples por ítem)"""

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="subquestions",
        verbose_name="Ítem",
    )
    order = models.PositiveIntegerField("Orden", default=0)
    image = models.ImageField(
        "Imagen",
        upload_to="exams/subquestions/",
        blank=True,
        null=True,
    )
    context_text = models.TextField(
        "Contenido",
        blank=True,
        help_text="Contenido de la subpregunta (puede incluir texto, tablas, imágenes)",
    )

    class Meta:
        verbose_name = "Subpregunta"
        verbose_name_plural = "Subpreguntas"
        ordering = ["order"]

    def __str__(self):
        return f"Subpregunta {self.order} de {self.item.code}"


class Option(models.Model):
    """Opción de respuesta para una subpregunta"""

    subquestion = models.ForeignKey(
        SubQuestion,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Subpregunta",
    )
    label = models.CharField(
        "Etiqueta",
        max_length=5,
        help_text="Ej: a, b, c, d",
    )
    text = models.CharField(
        "Texto",
        max_length=500,
        help_text="Texto de la opción",
    )
    is_correct = models.BooleanField("Es correcta", default=False)
    order = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Opción"
        verbose_name_plural = "Opciones"
        ordering = ["order"]

    def __str__(self):
        correct_mark = " ✓" if self.is_correct else ""
        return f"{self.label}. {self.text}{correct_mark}"
