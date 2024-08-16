import asyncio
import logging
from uuid import UUID

from aiogram import exceptions

from .crud import TelegramCrud
from database.models import TelegramLog, NotificationData
from telegram import bot
from .config import REDIS_URL
from .utils import RedisUUIDQueue, AsyncRedisUUIDQueue


DEFAULT_MESSAGE_TEMPLATE = (
    "Warning. Your health ratio is too low for wallet_id {wallet_id}"
)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TelegramNotifications:
    """
    Class for sending Telegram notifications.

    Example:
         from database.crud import DBConnector

         telegram_notifications = TelegramNotifications(db_connector=DBConnector())

         scheduler.add_job(telegram_notifications, "interval", seconds=0.05)
         # or
         asyncio.run(telegram_notifications(is_infinity=True))

    Minimal interval 0.05 seconds, 20 messages per second (Limit: 30 messages per second)
    """

    __queue_to_send = RedisUUIDQueue('telegram_notifications_queue', REDIS_URL)
    __aqueue_to_send = AsyncRedisUUIDQueue('telegram_notifications_queue', REDIS_URL)

    @classmethod
    def send_notification(cls, notification_id: UUID) -> None:
        """
        Add a Telegram ID to the queue for sending a notification.

        :param notification_id: Unique identifier of the NotificationData.id, which will be added to the queue for sending via Telegram.
        """
        logger.info(f"Telegram: send notification: {notification_id}")
        cls.__queue_to_send.enqueue(notification_id)

    @classmethod
    async def asend_notification(cls, notification_id: UUID) -> None:
        """
        Add a Telegram ID to the queue for sending a notification.

        :param notification_id: Unique identifier of the NotificationData.id, which will be added to the queue for sending via Telegram.
        """
        logger.info(f"Telegram: send notification: {notification_id}")
        await cls.__aqueue_to_send.enqueue(notification_id)

    async def log_send(self, notification_id: UUID, text: str, is_succesfully: bool):
        """
        Logs the sending status of a message.

        :param notification_id: The UUID identifying the notification data.
        :param text: The message text that was sent.
        :param is_succesfully: A boolean indicating whether the message was sent successfully or not.
        """
        await self.crud.create_object(
            TelegramLog(
                notification_data_id=notification_id,
                is_succesfully=is_succesfully,
                message=text,
            )
        )

    def __init__(
            self, crud: TelegramCrud, text: str = DEFAULT_MESSAGE_TEMPLATE
    ) -> None:
        """
        Initialize the TelegramNotifier instance.

        :param crud: Instance of crud to handle database operations.
        :param text: The text content of the notification (which will be formatted when sent).
        """
        self.crud = crud
        self.text = text

    async def __call__(
            self, is_infinity: bool = False, sleep_time: float = 0.05
    ) -> None:
        """
        Process the queue and send notifications.

        This method processes the queue of Notifiication ID and sends notifications to each user.

        :param is_infinity: A boolean indicating whether the processing loop should continue indefinitely.
                    If set to True, the method will continuously process notifications.
                    Defaults to False.
        :param sleep_time: The time interval (in seconds) to wait between processing notifications.
                   This parameter is effective only when is_infinity is set to True.
                   Defaults to 0.05 seconds.
        """
        logger.info("Telegram: start sending notifications")
        while notification_id := await self.__aqueue_to_send.dequeue():
            logger.info(f"Telegram: send notification: {notification_id}")
            # Retrieve notification data from the database based on its ID
            notification = self.crud.get_object(
                NotificationData, notification_id
            )
            logger.info(f"Telegram: notification: {notification} class")
            if notification is None:
                continue  # skip is not valid notification_id
            is_succesfully = False
            # create text message
            text = self.text.format(wallet_id=notification.wallet_id)

            try:
                logger.info(f"Check notification.telegram_id: {notification.telegram_id}")
                # Check if the notification has a Telegram ID and send the message
                if notification.telegram_id:
                    await bot.send_message(
                        chat_id=notification.telegram_id,
                        text=text,
                    )
                    is_succesfully = True
            except exceptions.TelegramRetryAfter as e:
                logger.info(f"Telegram retry after error continue of {e.retry_after} sec.")
                # If Telegram returns a RetryAfter exception, wait for the specified time and then retry
                await asyncio.sleep(e.retry_after)
                # Ignore QueueFull exception to prevent it from being raised when the queue is explicitly limited
                await self.__aqueue_to_send.enqueue_front(notification_id)
            except exceptions.TelegramAPIError:
                logger.error(f"Telegram notification({notification_id}) error from send to {notification.telegram_id}")
            finally:
                # Log the sending status of the message
                await self.log_send(notification_id, text, is_succesfully)

            # If the loop is not set to infinity, break out after processing one notification
            if not is_infinity:
                break
            await asyncio.sleep(sleep_time)

    def __await__(self):
        return self(is_infinity=True).__await__()