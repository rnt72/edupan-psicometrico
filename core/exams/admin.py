from django.contrib import admin

from .models import Exam
from .models import Item
from .models import Option
from .models import SubQuestion


class ItemInline(admin.TabularInline):
    model = Item
    extra = 0
    fields = ["code", "order", "instruction", "scoring_type"]
    ordering = ["order"]


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ItemInline]

    fieldsets = (
        (None, {"fields": ("name",)}),
        ("Estado", {"fields": ("is_active", "created_by")}),
        ("Fechas", {"fields": ("created_at", "updated_at")}),
    )


class OptionInline(admin.TabularInline):
    model = Option
    extra = 3
    fields = ["label", "text", "is_correct", "order"]
    ordering = ["order"]


class SubQuestionInline(admin.TabularInline):
    model = SubQuestion
    extra = 1
    fields = ["order", "context_text", "image"]
    ordering = ["order"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["code", "exam", "instruction_short", "scoring_type", "order"]
    list_filter = ["exam", "scoring_type"]
    search_fields = ["code", "instruction"]
    inlines = [SubQuestionInline]

    fieldsets = (
        (None, {"fields": ("exam", "code", "order")}),
        ("Contenido", {"fields": ("instruction", "image")}),
        ("Calificacion", {"fields": ("scoring_type",)}),
        (
            "Criterios Winsteps",
            {
                "fields": ("correct_criteria", "partial_criteria", "incorrect_criteria"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Instruccion")
    def instruction_short(self, obj):
        return obj.instruction[:60] + "..." if len(obj.instruction) > 60 else obj.instruction


@admin.register(SubQuestion)
class SubQuestionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "item", "order"]
    list_filter = ["item__exam"]
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ["label", "text", "is_correct", "subquestion"]
    list_filter = ["is_correct", "subquestion__item__exam"]
    search_fields = ["text"]
