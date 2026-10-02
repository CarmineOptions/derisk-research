from __future__ import annotations

import logging
from redis.asyncio import ConnectionPool, Redis
from redis import Redis as SyncRedis

logger = logging.getLogger(__name__)

_redis_pool: ConnectionPool | None = None
_sync_pool: ConnectionPool | None = None


def get_redis_pool() -> ConnectionPool:
    global _redis_pool
    if _redis_pool is None:
        from apps.dashboard_app.config import REDIS_HOST, REDIS_PORT
        _redis_pool = ConnectionPool(
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            decode_responses=True,
        )
    return _redis_pool


def get_sync_redis_pool() -> ConnectionPool:
    global _sync_pool
    if _sync_pool is None:
        from apps.dashboard_app.config import REDIS_HOST, REDIS_PORT
        _sync_pool = ConnectionPool(
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            decode_responses=True,
        )
    return _sync_pool


async def get_redis_client() -> Redis:
    return Redis(connection_pool=get_redis_pool())


def get_sync_redis_client() -> SyncRedis:
    return SyncRedis(connection_pool=get_sync_redis_pool())
