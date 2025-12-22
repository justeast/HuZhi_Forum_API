from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    仅对象所有者可以编辑，其他人只读
    对象需要有 questioner（Question）或 creator（Topic）字段
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 明确检查对象具有哪个所有者字段
        if hasattr(obj, 'questioner'):
            return obj.questioner == request.user
        elif hasattr(obj, 'creator'):
            return obj.creator == request.user
        
        # 如果对象既没有 questioner 也没有 creator，拒绝访问
        return False
