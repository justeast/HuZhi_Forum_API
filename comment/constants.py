# 错误码定义
COMMENT_NOT_FOUND = 40001  # 评论不存在
PARENT_COMMENT_NOT_FOUND = 40003  # 父评论不存在
INVALID_PARENT_COMMENT = 40004  # 父评论不属于同一个回答
REPLY_TO_USER_NOT_FOUND = 40005  # 被回复用户不存在
COMMENT_NO_PERMISSION = 40006  # 无权限删除该评论
INVALID_COMMENT_REPLY = 40007  # 二级评论必须同时指定parent_id和reply_to_id

# 错误消息
COMMENT_NOT_FOUND_MSG = "评论不存在"
PARENT_COMMENT_NOT_FOUND_MSG = "父评论不存在"
INVALID_PARENT_COMMENT_MSG = "父评论必须属于同一个回答"
REPLY_TO_USER_NOT_FOUND_MSG = "被回复用户不存在"
COMMENT_NO_PERMISSION_MSG = "无权限删除该评论"
INVALID_COMMENT_REPLY_MSG = "二级评论必须同时指定parent_id和reply_to_id"
