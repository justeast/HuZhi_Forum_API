# 密码复杂度校验正则
PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'

# 错误码定义
PASSWORD_FORMAT_ERROR = 10001  # 密码格式错误

# 错误消息
PASSWORD_FORMAT_ERROR_MSG = "密码需包含大小写字母和数字，长度至少8位"
