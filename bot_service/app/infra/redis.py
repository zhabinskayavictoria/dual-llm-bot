import redis.asyncio as redis
from app.core.config import settings

def get_redis() -> redis.Redis:
    """Возвращает асинхронный клиент Redis"""
    return redis.from_url(settings.REDIS_URL, decode_responses=True)