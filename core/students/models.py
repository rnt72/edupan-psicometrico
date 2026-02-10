import uuid

from django.db import models


class Region(models.Model):
    """Región geográfica (ej: Región Norte, Región Sur)"""

    name = models.CharField("Nombre", max_length=200, unique=True)
    code = models.CharField(
        "Código",
        max_length=20,
        unique=True,
        help_text="Ej: REG-01, NORTE",
    )

    class Meta:
        verbose_name = "Región"
        verbose_name_plural = "Regiones"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Institution(models.Model):
    """Institución educativa (escuela)"""

    name = models.CharField("Nombre", max_length=300)
    code = models.CharField(
        "Código",
        max_length=50,
        blank=True,
        default="",
        help_text="Código opcional de la institución",
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="institutions",
        verbose_name="Región",
    )

    class Meta:
        verbose_name = "Institución"
        verbose_name_plural = "Instituciones"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.region.name})"


class Student(models.Model):
    """Estudiante anónimo identificado solo por un código de referencia autogenerado.
    Se crea únicamente al momento de subir respuestas.
    """

    reference_code = models.CharField(
        "Código de referencia",
        max_length=20,
        unique=True,
        editable=False,
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name="Institución",
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name="Región",
    )
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)

    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference_code

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = self._generate_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_code():
        """Genera código único tipo STU-XXXXXX"""
        while True:
            code = f"STU-{uuid.uuid4().hex[:6].upper()}"
            if not Student.objects.filter(reference_code=code).exists():
                return code
