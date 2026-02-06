from django.contrib import admin

from .models import ExamApplication
from .models import ItemScore
from .models import Response
from .models import ResponseRow


class ResponseRowInline(admin.TabularInline):
    model = ResponseRow
    extra = 0
    show_change_link = True


class ResponseInline(admin.TabularInline):
    model = Response
    extra = 0
    raw_id_fields = ["subquestion", "selected_option"]


class ItemScoreInline(admin.TabularInline):
    model = ItemScore
    extra = 0
    raw_id_fields = ["item"]


@admin.register(ExamApplication)
class ExamApplicationAdmin(admin.ModelAdmin):
    list_display = ["name", "exam", "created_by", "created_at", "total_rows"]
    list_filter = ["exam", "created_by"]
    search_fields = ["name", "exam__name"]
    inlines = [ResponseRowInline]


@admin.register(ResponseRow)
class ResponseRowAdmin(admin.ModelAdmin):
    list_display = ["row_number", "application"]
    list_filter = ["application"]
    inlines = [ResponseInline, ItemScoreInline]


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ["row", "subquestion", "selected_option", "is_correct"]
    list_filter = ["is_correct", "row__application"]
    raw_id_fields = ["row", "subquestion", "selected_option"]


@admin.register(ItemScore)
class ItemScoreAdmin(admin.ModelAdmin):
    list_display = ["row", "item", "score"]
    list_filter = ["row__application", "item__exam"]
    raw_id_fields = ["row", "item"]
