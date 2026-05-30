from django.contrib import admin

from comment.models import Comment


def truncate_text(value, length=30):
    if not value:
        return "-"
    return value if len(value) <= length else f"{value[:length]}..."


class CommentLevelFilter(admin.SimpleListFilter):
    title = "评论层级"
    parameter_name = "level"

    def lookups(self, request, model_admin):
        return (
            ("root", "一级评论"),
            ("reply", "回复评论"),
        )

    def queryset(self, request, queryset):
        if self.value() == "root":
            return queryset.filter(parent__isnull=True)
        if self.value() == "reply":
            return queryset.filter(parent__isnull=False)
        return queryset


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "short_content",
        "comment_level",
        "user",
        "question_title",
        "answer_summary",
        "reply_target",
        "like_count",
        "created",
    )
    list_filter = (CommentLevelFilter, "created", "modified")
    search_fields = (
        "content",
        "user__username",
        "user__email",
        "answer__content",
        "answer__question__title",
    )
    readonly_fields = ("id", "created", "modified")
    autocomplete_fields = ("user", "answer", "parent", "reply_to")
    ordering = ("-created",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "reply_to", "parent__user", "answer__respondent", "answer__question")
        )

    @admin.display(description="内容摘要")
    def short_content(self, obj):
        return truncate_text(obj.content, 50)

    @admin.display(description="层级", ordering="parent")
    def comment_level(self, obj):
        return "回复评论" if obj.parent_id else "一级评论"

    @admin.display(description="所属问题", ordering="answer__question__title")
    def question_title(self, obj):
        return truncate_text(obj.answer.question.title, 30)

    @admin.display(description="所属回答")
    def answer_summary(self, obj):
        return f"{obj.answer.respondent.username}：{truncate_text(obj.answer.content, 30)}"

    @admin.display(description="回复对象")
    def reply_target(self, obj):
        if not obj.parent_id:
            return "-"

        target_user = obj.reply_to or obj.parent.user
        return f"{target_user.username}：{truncate_text(obj.parent.content, 30)}"
