import base64
import uuid
from django.conf import settings
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tms.v20201229 import tms_client, models as tms_models
from tencentcloud.ims.v20201229 import ims_client, models as ims_models
from common import constants as c
from common.exceptions import BusinessException


def _build_http_profile(endpoint: str) -> HttpProfile:
    """
    构造腾讯云客户端 HTTP 配置
    """
    http_profile = HttpProfile()
    http_profile.endpoint = endpoint
    return http_profile


def _build_client_profile(endpoint: str) -> ClientProfile:
    """
    构造腾讯云客户端配置
    """
    client_profile = ClientProfile()
    client_profile.httpProfile = _build_http_profile(endpoint)
    return client_profile


def _build_credential():
    """
    构造腾讯云凭证
    """
    return credential.Credential(
        settings.COS_SECRET_ID,
        settings.COS_SECRET_KEY,
    )


def _build_text_client():
    """
    构造文本审核客户端
    """
    return tms_client.TmsClient(
        _build_credential(),
        settings.COS_REGION,
        _build_client_profile("tms.tencentcloudapi.com"),
    )


def _build_image_client():
    """
    构造图片审核客户端
    """
    return ims_client.ImsClient(
        _build_credential(),
        settings.COS_REGION,
        _build_client_profile("ims.tencentcloudapi.com"),
    )


def _build_data_id(prefix: str) -> str:
    """
    构造审核请求的数据标识
    """
    return f"{prefix}_{uuid.uuid4().hex}"[:64]


def _build_text_user(user):
    """
    构造文本审核的用户信息
    """
    if not user:
        return None

    user_info = tms_models.User()
    user_info.UserId = str(user.id)
    # 7 表示“其它 string”类型账号
    user_info.AccountType = 7
    user_info.Nickname = user.username
    return user_info


def _build_image_user(user):
    """
    构造图片审核的用户信息
    """
    if not user:
        return None

    user_info = ims_models.User()
    user_info.UserId = str(user.id)
    # 7 表示“其它 string”类型账号
    user_info.AccountType = "7"
    user_info.Nickname = user.username
    return user_info


def check_text_content(content: str, user=None, data_id: str = None, session_id: str = None) -> dict:
    """
    调用腾讯云文本内容安全
    """
    request = tms_models.TextModerationRequest()
    request.Content = base64.b64encode((content or "").encode("utf-8")).decode("utf-8")
    request.BizType = settings.CONTENT_SAFETY_TEXT_BIZTYPE
    request.DataId = data_id or _build_data_id("text")
    request.SourceLanguage = "zh"
    request.Type = "TEXT"

    user_info = _build_text_user(user)
    if user_info:
        request.User = user_info

    if session_id:
        request.SessionId = str(session_id)

    try:
        response = _build_text_client().TextModeration(request)
    except TencentCloudSDKException as exc:
        raise BusinessException(
            code=c.CONTENT_AUDIT_FAILED,
            msg=c.CONTENT_AUDIT_FAILED_MSG,
        ) from exc

    return {
        "suggestion": response.Suggestion,
        "label": response.Label,
        "sub_label": response.SubLabel,
        "score": response.Score,
        "request_id": response.RequestId,
        "biz_type": response.BizType,
        "data_id": response.DataId,
    }


def check_image_content(file_url: str, user=None, data_id: str = None) -> dict:
    """
    调用腾讯云图片内容安全
    """
    request = ims_models.ImageModerationRequest()
    request.FileUrl = file_url
    request.BizType = settings.CONTENT_SAFETY_IMAGE_BIZTYPE
    request.DataId = data_id or _build_data_id("image")

    user_info = _build_image_user(user)
    if user_info:
        request.User = user_info

    try:
        response = _build_image_client().ImageModeration(request)
    except TencentCloudSDKException as exc:
        raise BusinessException(
            code=c.CONTENT_AUDIT_FAILED,
            msg=c.CONTENT_AUDIT_FAILED_MSG,
        ) from exc

    return {
        "suggestion": response.Suggestion,
        "label": response.Label,
        "sub_label": response.SubLabel,
        "score": response.Score,
        "request_id": response.RequestId,
        "biz_type": response.BizType,
        "data_id": response.DataId,
    }


def assert_text_safe(content: str, user=None, data_id: str = None, session_id: str = None) -> None:
    """
    校验文本内容是否可通过审核
    """
    result = check_text_content(content, user=user, data_id=data_id, session_id=session_id)
    if result["suggestion"] != c.CONTENT_SAFETY_SUGGESTION_PASS:
        raise BusinessException(
            code=c.CONTENT_AUDIT_REJECTED,
            msg=c.CONTENT_AUDIT_REJECTED_MSG,
        )


def assert_image_safe(file_url: str, user=None, data_id: str = None) -> None:
    """
    校验图片内容是否可通过审核
    """
    result = check_image_content(file_url, user=user, data_id=data_id)
    if result["suggestion"] != c.CONTENT_SAFETY_SUGGESTION_PASS:
        raise BusinessException(
            code=c.CONTENT_AUDIT_REJECTED,
            msg=c.CONTENT_AUDIT_REJECTED_MSG,
        )
