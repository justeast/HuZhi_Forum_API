import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from model_utils.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    """
    自定义用户模型
    """
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)

    email = models.EmailField(unique=True,blank=False,null=False,
        error_messages={
            'unique': "该邮箱已被注册。",
            'blank': "邮箱不能为空。",
            'null': "邮箱不能为空。",
        },
        verbose_name="邮箱"
    )

    phone = models.CharField(max_length=11,unique=True,null=True,blank=True,verbose_name="手机号")

    avatar = models.URLField(max_length=500,blank=True,null=True,verbose_name="头像URL")

    bio = models.TextField(max_length=500,blank=True,null=True,verbose_name="个人简介")

    class Meta:
        db_table = "base_user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        ordering = ['-created']

    def __str__(self):
        return self.username
