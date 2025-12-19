# 密码复杂度校验正则
PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'

# 错误码定义
PASSWORD_FORMAT_ERROR = 10001  # 密码格式错误
USER_NOT_FOUND = 10002  # 用户不存在
PASSWORD_INCORRECT = 10003  # 密码错误
INVALID_TOKEN = 10004  # 无效token
CODE_SEND_TOO_FREQUENT = 10005  # 验证码发送过于频繁
INVALID_VERIFY_CODE = 10006  # 验证码无效或已过期
EMAIL_SEND_FAILED = 10007  # 邮件发送失败

# 错误消息
PASSWORD_FORMAT_ERROR_MSG = "密码需包含大小写字母和数字，长度至少8位"
USER_NOT_FOUND_MSG = "用户不存在"
PASSWORD_INCORRECT_MSG = "密码错误"
INVALID_TOKEN_MSG = "无效的token"
CODE_SEND_TOO_FREQUENT_MSG = "验证码发送过于频繁，请稍后再试"
INVALID_VERIFY_CODE_MSG = "验证码无效或已过期"
EMAIL_SEND_FAILED_MSG = "邮件发送失败，请稍后重试"

# Redis Key前缀
REDIS_KEY_PWD_RESET_CODE = "pwd_reset_code:"  # 密码重置验证码
REDIS_KEY_PWD_RESET_LIMIT = "pwd_reset_limit:"  # 密码重置限流
