from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    仅对象所有者可以编辑，其他人只读
    对象需要有 questioner（Question）、creator（Topic）或 respondent（Answer）字段
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 明确检查对象具有哪个所有者字段
        if hasattr(obj, 'questioner'):
            return obj.questioner == request.user
        elif hasattr(obj, 'creator'):
            return obj.creator == request.user
        elif hasattr(obj, 'respondent'):
            return obj.respondent == request.user
        
        # 如果对象没有所有者字段，拒绝访问
        return False


class IsCommentOwnerOrAnswerAuthor(permissions.BasePermission):
    """
    评论删除权限：
    1. 评论作者本人可以删除
    2. 该评论所属回答的作者可以删除
    3. 管理员可以删除
    """
    def has_object_permission(self, request, view, obj):
        # 管理员拥有所有权限
        if request.user.is_staff:
            return True
        
        # 评论作者本人
        if obj.user == request.user:
            return True
        
        # 回答作者可以删除自己回答下的评论
        if obj.answer.respondent == request.user:
            return True
        
        return False
