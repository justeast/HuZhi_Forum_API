import uuid
import django_filters
from question.models import Question


class QuestionFilter(django_filters.FilterSet):
    """
    问题过滤器
    """
    topics = django_filters.CharFilter(method='filter_topics')
    
    def filter_topics(self, queryset, name, value):
        """
        自定义 topics 过滤方法，支持不带连字符的 UUID 格式
        """
        if not value:
            return queryset
        
        # 将逗号分隔的字符串转换为 UUID 列表
        topic_ids = [v.strip() for v in value.split(',')]
        valid_uuids = []
        
        for topic_id in topic_ids:
            try:
                # 尝试将字符串转换为 UUID，自动处理带/不带连字符的格式
                valid_uuid = uuid.UUID(topic_id)
                valid_uuids.append(valid_uuid)
            except (ValueError, AttributeError):
                # 忽略无效的 UUID
                continue
        
        if valid_uuids:
            return queryset.filter(topics__id__in=valid_uuids).distinct()
        
        return queryset
    
    class Meta:
        model = Question
        fields = ['topics']
