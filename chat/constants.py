# 消息类型
TEXT = 1
IMAGE = 2

MSG_TYPE_CHOICES = (
    (TEXT, '文本'),
    (IMAGE, '图片'),
)

# WebSocket 消息类型
WS_MSG_TYPE_SEND = "send_message"  # 客户端发送消息
WS_MSG_TYPE_NEW = "new_message"  # 服务端推送新消息
WS_MSG_TYPE_READ = "message_read"  # 消息已读通知
WS_MSG_TYPE_ERROR = "error"  # 错误响应

# 错误码定义
CHAT_NOT_FOUND = 80001  # 会话不存在
CHAT_PERMISSION_DENIED = 80002  # 无权限访问该会话
MESSAGE_SEND_FAILED = 80003  # 消息发送失败
INVALID_RECEIVER = 80004  # 无效的接收者
CANNOT_CHAT_WITH_SELF = 80005  # 不能给自己发消息
MESSAGE_NOT_FOUND = 80006  # 消息不存在
INVALID_TOKEN = 80007  # 无效的认证令牌

# 错误消息
CHAT_NOT_FOUND_MSG = "会话不存在"
CHAT_PERMISSION_DENIED_MSG = "无权限访问该会话"
MESSAGE_SEND_FAILED_MSG = "消息发送失败"
INVALID_RECEIVER_MSG = "无效的接收者"
CANNOT_CHAT_WITH_SELF_MSG = "不能给自己发消息"
MESSAGE_NOT_FOUND_MSG = "消息不存在"
INVALID_TOKEN_MSG = "无效的认证令牌"
