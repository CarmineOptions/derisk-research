from asyncio.queues import Queue
from uuid import UUID

from aiogram.utils.deep_linking import create_deep_link

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


class TelegramNotifications:
    """
    Class for sending Telegram notifications.

    Example:
         scheduler.add_job(TelegramNotifications(), "interval", seconds=0.05)

    Minimal interval 0.05 seconds, 20 messages per second (Limit: 30 messages per second)
    """

    __queue_to_send = Queue()

    @classmethod
    async def send_notification(cls, telegram_id: int):
        """
        Add a Telegram ID to the queue for sending a notification.

        :param telegram_id: The ID of the Telegram user to send the notification to.
        """
        await cls.__queue_to_send.put(telegram_id)

    async def __call__(self):
        """
        Process the queue and send notifications.

        This method processes the queue of Telegram IDs and sends notifications to each user.
        """
        while ident := await self.__queue_to_send.get():
            await bot.send_message(chat_id=ident, text="Test message")
