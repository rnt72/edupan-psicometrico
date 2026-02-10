from django.contrib import admin

from .models import Institution
from .models import Region
from .models import Student


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "institution_count"]
    search_fields = ["name", "code"]

    @admin.display(description="Instituciones")
    def institution_count(self, obj):
        return obj.institutions.count()


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "region", "student_count"]
    list_filter = ["region"]
    search_fields = ["name", "code"]

    @admin.display(description="Estudiantes")
    def student_count(self, obj):
        return obj.students.count()


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["reference_code", "institution", "region", "created_at"]
    list_filter = ["region", "institution"]
    search_fields = ["reference_code"]
    readonly_fields = ["reference_code", "created_at"]
