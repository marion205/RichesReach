# cache.py
import json
from typing import Any, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis
from settings import settings

r = redis.from_url(settings.REDIS_URL, decode_responses=True)

def stamp(value: Any, source: str) -> str:
    payload = {"asOf": datetime.utcnow().isoformat(), "source": source, "value": value}
    return json.dumps(payload)

async def get_json(key: str) -> Optional[dict]:
    raw = await r.get(key)
    return json.loads(raw) if raw else None

async def set_json(key: str, value: Any, ttl_s: int):
    await r.set(key, value if isinstance(value, str) else json.dumps(value), ex=ttl_s)
