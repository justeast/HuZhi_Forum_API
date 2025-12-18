# 密码复杂度校验正则
PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'

# 错误码定义
PASSWORD_FORMAT_ERROR = 10001  # 密码格式错误
USER_NOT_FOUND = 10002  # 用户不存在
PASSWORD_INCORRECT = 10003  # 密码错误
INVALID_TOKEN = 10004  # 无效token

# 错误消息
PASSWORD_FORMAT_ERROR_MSG = "密码需包含大小写字母和数字，长度至少8位"
USER_NOT_FOUND_MSG = "用户不存在"
PASSWORD_INCORRECT_MSG = "密码错误"
INVALID_TOKEN_MSG = "无效的token"
