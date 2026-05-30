from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm
from django.utils.translation import ngettext

from base.models import User


class CustomUserCreationForm(AdminUserCreationForm):
    """
    后台新增用户表单，补上项目自定义用户的必填字段。
    """

    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ("username", "email", "phone", "avatar", "cover_image", "bio")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = CustomUserCreationForm
    list_display = (
        "username",
        "email",
        "phone",
        "is_active",
        "is_staff",
        "is_superuser",
        "created",
        "modified",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "created", "modified")
    search_fields = ("username", "email", "phone")
    ordering = ("-created",)
    readonly_fields = ("id", "created", "modified", "last_login", "date_joined")
    actions = ("ban_users", "unban_users")

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("乎知论坛资料", {"fields": ("id", "phone", "avatar", "cover_image", "bio", "created", "modified")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "phone",
                    "avatar",
                    "cover_image",
                    "bio",
                    "usable_password",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    @admin.action(description="封禁选中用户")
    def ban_users(self, request, queryset):
        protected_queryset = queryset.filter(is_superuser=True) | queryset.filter(pk=request.user.pk)
        target_queryset = queryset.exclude(is_superuser=True).exclude(pk=request.user.pk)
        updated_count = target_queryset.update(is_active=False)
        protected_count = protected_queryset.distinct().count()

        if updated_count:
            self.message_user(
                request,
                ngettext(
                    "已封禁 %(count)d 个用户。",
                    "已封禁 %(count)d 个用户。",
                    updated_count,
                ) % {"count": updated_count},
                messages.SUCCESS,
            )
        if protected_count:
            self.message_user(
                request,
                "已跳过超级管理员或当前登录管理员，避免误封。",
                messages.WARNING,
            )

    @admin.action(description="解封选中用户")
    def unban_users(self, request, queryset):
        updated_count = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                "已解封 %(count)d 个用户。",
                "已解封 %(count)d 个用户。",
                updated_count,
            ) % {"count": updated_count},
            messages.SUCCESS,
        )
