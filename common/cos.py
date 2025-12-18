from django.conf import settings
from sts.sts import Sts


def get_cos_temporary_credential():
    """
    生成COS临时密钥
    """
    config = {
        'secret_id': settings.COS_SECRET_ID,
        'secret_key': settings.COS_SECRET_KEY,
        'duration_seconds': 900,  # 有效期15分钟
        'bucket': settings.COS_BUCKET,
        'region': settings.COS_REGION,
        # 允许的操作
        'allow_actions': [
            'cos:PutObject',
            'cos:PostObject',
            'cos:InitiateMultipartUpload',
            'cos:ListMultipartUploads',
            'cos:ListParts',
            'cos:UploadPart',
            'cos:CompleteMultipartUpload',
        ],
        # 允许上传到所有路径
        'allow_prefix': ['*'],
    }

    sts = Sts(config)
    response = sts.get_credential()
    return response
