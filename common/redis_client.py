import redis
from django.conf import settings

# Redis连接池
_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)


def get_redis_client() -> redis.Redis:
    """
    获取Redis客户端
    """
    return redis.Redis(connection_pool=_pool)
