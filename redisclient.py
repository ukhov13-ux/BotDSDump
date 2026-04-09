import redis.asyncio as redis
from config import REDIS_URL

async def get_redis():
    return redis.from_url(REDIS_URL, decode_responses=True)
