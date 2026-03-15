from django.db import transaction
from django.db.models import F
from comment.models import Comment
from answer.models import Answer
from base.models import User
from vote.models import CommentVote
from vote import constants as vote_c
from base import services as base_services
from base import constants as base_c
from common.content_safety import assert_text_safe


def create_comment(user, validated_data):
    """
    创建评论
    """
    answer_id = validated_data.pop('answer_id')
    parent_id = validated_data.pop('parent_id', None)
    reply_to_id = validated_data.pop('reply_to_id', None)
    
    # 获取关联对象
    answer = Answer.objects.get(id=answer_id)
    parent = Comment.objects.get(id=parent_id) if parent_id else None
    reply_to = User.objects.get(id=reply_to_id) if reply_to_id else None

    assert_text_safe(
        validated_data.get('content'),
        user=user,
        data_id=f"comment_create_{answer_id}",
    )
    
    # 创建评论
    comment = Comment.objects.create(
        user=user,
        answer=answer,
        parent=parent,
        reply_to=reply_to,
        content=validated_data['content']
    )

    recipient = reply_to or (parent.user if parent else None)
    if recipient:
        base_services.create_notification(
            recipient=recipient,
            actor=user,
            notification_type=base_c.NOTIFICATION_TYPE_COMMENT_REPLIED,
            title='我的评论有人回复了',
            content=f'{user.username} 回复了你的评论',
            payload={
                'question_id': str(answer.question_id),
                'answer_id': str(answer.id),
                'comment_id': str(comment.id),
                'parent_comment_id': str(parent.id) if parent else None,
            },
        )

    return comment


def like_comment(user, comment):
    """
    评论点赞/取消点赞（toggle操作）
    """
    with transaction.atomic():
        vote, created = CommentVote.objects.get_or_create(
            user=user,
            comment=comment,
            defaults={'vote_type': vote_c.UPVOTE}
        )
        
        if created:
            # 新点赞
            Comment.objects.filter(id=comment.id).update(
                like_count=F('like_count') + 1
            )
        else:
            # 取消点赞
            vote.delete()
            Comment.objects.filter(id=comment.id).update(
                like_count=F('like_count') - 1
            )
        
        # 刷新comment对象以获取最新的like_count
        comment.refresh_from_db()
