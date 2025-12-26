UPVOTE = 1
DOWNVOTE = -1
CANCEL_VOTE = 0

VOTE_TYPE_CHOICES = (
    (UPVOTE, '赞同'),
    (DOWNVOTE, '不赞同/反对'),
    (CANCEL_VOTE, '取消投票/未投票'),
)

# 错误码定义
INVALID_VOTE_TYPE = 50001  # 无效的投票类型

# 错误消息
INVALID_VOTE_TYPE_MSG = "无效的投票类型，必须为 1(赞同)、-1(反对) 或 0(取消投票)"
