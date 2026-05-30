from django.contrib import admin

from answer.models import Answer


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("short_content", "question", "respondent", "created", "modified")
    list_filter = ("created", "modified")
    search_fields = ("content", "question__title", "respondent__username", "respondent__email")
    readonly_fields = ("id", "created", "modified")
    autocomplete_fields = ("question", "respondent")
    ordering = ("-created",)

    @admin.display(description="内容摘要")
    def short_content(self, obj):
        return obj.content[:50]
