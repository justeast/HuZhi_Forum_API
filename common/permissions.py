from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    仅对象所有者可以编辑，其他人只读
    对象需要有 questioner 字段
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.questioner == request.user
