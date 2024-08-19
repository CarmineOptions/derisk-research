from uuid import UUID

from aiogram.utils.deep_linking import create_deep_link
<<<<<<< HEAD
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
=======
from redis.asyncio import Redis
>>>>>>> 17a3757a5ba77813845053c05474f48ecb6a29bc

from .bot import bot


async def get_subscription_link(ident: UUID) -> str:
    """
    Generate a subscription link for a given identifier.

    :param ident: The unique identifier for the subscription (from NotificationData.id).
    :return: The generated subscription link, e.g., "https://t.me/TestBot?start=DARAAD".
    """
    me = await bot.me()
    return create_deep_link(
        username=me.username, link_type="start", payload=str(ident), encode=True
    )


<<<<<<< HEAD
class RedisUUIDQueue:
=======
class AsyncRedisUUIDQueue:
>>>>>>> 17a3757a5ba77813845053c05474f48ecb6a29bc
    def __init__(self, key: str, redis_url: str) -> None:
        self.__db = Redis.from_url(redis_url)
        self.key = key

<<<<<<< HEAD
    def enqueue(self, item: UUID) -> None:
        """Adds an item to the end of the queue."""
        self.__db.rpush(self.key, str(item))

    def enqueue_front(self, item: UUID) -> None:
        """Adds an item to the front of the queue."""
        self.__db.lpush(self.key, str(item))

    def dequeue(self, block: bool = True, timeout: int = 0) -> UUID:
=======
    async def enqueue(self, item: UUID) -> None:
        """Adds an item to the end of the queue."""
        await self.__db.rpush(self.key, str(item))

    async def enqueue_front(self, item: UUID) -> None:
        """Adds an item to the front of the queue."""
        await self.__db.lpush(self.key, str(item))

    async def dequeue(self, block: bool = True, timeout: int = 0) -> UUID:
>>>>>>> 17a3757a5ba77813845053c05474f48ecb6a29bc
        """Removes and returns an item from the queue.

        If blocking is enabled, it will wait for an item.
        """
<<<<<<< HEAD
        _, item = self.__db.blpop([self.key], timeout=timeout)
        return UUID(item)

    def size(self) -> int:
        """Returns the number of items in the queue."""
        return self.__db.llen(self.key)

    def clear(self) -> None:
        """Deletes all items from the queue."""
        self.__db.delete(self.key)


class AsyncRedisUUIDQueue:
    def __init__(self, key: str, redis_url: str) -> None:
        self.__db = AsyncRedis.from_url(redis_url)
        self.key = key

    async def enqueue(self, item: UUID) -> None:
        """Adds an item to the end of the queue."""
        await self.__db.rpush(self.key, str(item))

    async def enqueue_front(self, item: UUID) -> None:
        """Adds an item to the front of the queue."""
        await self.__db.lpush(self.key, str(item))

    async def dequeue(self, block: bool = True, timeout: int = 0) -> UUID:
        """Removes and returns an item from the queue.

        If blocking is enabled, it will wait for an item.
        """
        _, item = await self.__db.blpop([self.key], timeout=timeout)
        return UUID(item)

    async def size(self) -> int:
        """Returns the number of items in the queue."""
        return await self.__db.llen(self.key)

=======
        _, item = await self.__db.blpop([self.key], timeout=timeout)
        return UUID(item.decode())

    async def size(self) -> int:
        """Returns the number of items in the queue."""
        return await self.__db.llen(self.key)

>>>>>>> 17a3757a5ba77813845053c05474f48ecb6a29bc
    async def clear(self) -> None:
        """Deletes all items from the queue."""
        await self.__db.delete(self.key)
