from rest_framework import serializers
from vote import constants as c


class VoteReqSerializer(serializers.Serializer):
    """
    投票请求序列化器
    """
    vote_type = serializers.ChoiceField(
        choices=c.VOTE_TYPE_CHOICES,
        required=True,
        help_text="投票类型: 1=赞同, -1=反对, 0=取消投票"
    )
