from django.contrib import admin

from question.models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "questioner", "view_count", "created", "modified")
    list_filter = ("topics", "created", "modified")
    search_fields = ("title", "content", "questioner__username", "questioner__email")
    readonly_fields = ("id", "created", "modified")
    autocomplete_fields = ("questioner",)
    filter_horizontal = ("followers", "topics")
    ordering = ("-created",)
