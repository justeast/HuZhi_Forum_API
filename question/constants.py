# 关注操作常量
QUESTION_FOLLOW_ACTION = 1  # 关注
QUESTION_UNFOLLOW_ACTION = 2  # 取消关注

QUESTION_FOLLOW_ACTION_CHOICES = (
    (QUESTION_FOLLOW_ACTION, '关注'),
    (QUESTION_UNFOLLOW_ACTION, '取消关注'),
)

# 错误码定义
QUESTION_NOT_FOUND = 20001  # 问题不存在
QUESTION_NO_PERMISSION = 20002  # 无权限操作该问题
INVALID_FOLLOW_ACTION = 20003  # 无效的关注操作

# 错误消息
QUESTION_NOT_FOUND_MSG = "问题不存在"
QUESTION_NO_PERMISSION_MSG = "无权限操作该问题"
INVALID_FOLLOW_ACTION_MSG = "无效的关注操作，action 必须为 1(关注) 或 2(取消关注)"

# 首页热度排序（带时间衰减）参数
# hot_score = view_count / pow(age_hours + k, alpha)
HOME_HOT_SCORE_K = 2.0
HOME_HOT_SCORE_ALPHA = 1.5

# 首页候选问题时间窗口（天）
# 默认取近 N 天；若窗口内无数据，视图层会自动兜底放宽窗口，避免首页空白
HOME_FEED_WINDOW_DAYS = 120

# “写回答”推荐问题相关性分数
ANSWER_RECOMMEND_FOLLOWED_USER_SCORE = 3
ANSWER_RECOMMEND_FOLLOWED_TOPIC_SCORE = 2
ANSWER_RECOMMEND_HISTORY_TOPIC_SCORE = 1

# “写回答”推荐问题的历史活跃窗口（天）
ANSWER_RECOMMEND_HISTORY_WINDOW_DAYS = 180
