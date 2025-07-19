from dashboard_app.app.telegram_app.telegram import bot, dp
from fastapi import APIRouter, Header
from aiogram import types
from typing import Annotated
import os
import logging
from dotenv import load_dotenv
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

X_TELEGRAM_BOT_API_SECRET_TOKEN = os.getenv("X_TELEGRAM_BOT_API_SECRET_TOKEN")

router = APIRouter()

@router.post("/telegram/webhook")
async def bot_webhook(
    update: dict,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> None | dict:
    """Register webhook endpoint for telegram bot"""
    if x_telegram_bot_api_secret_token != X_TELEGRAM_BOT_API_SECRET_TOKEN:
        logger.error("Wrong secret token !")
        return {"status": "error", "message": "Wrong secret token !"}
    telegram_update = types.Update(**update)
    await dp.feed_webhook_update(bot=bot, update=telegram_update)

