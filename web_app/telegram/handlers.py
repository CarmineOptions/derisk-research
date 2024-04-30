from aiogram import types
from aiogram.dispatcher.router import Router
from aiogram.filters import CommandStart, CommandObject
from sqlalchemy.orm import Session
from sqlalchemy.sql import update

from database.models import NotificationData

base_router = Router()


@base_router.message(CommandStart(deep_link=True, deep_link_encoded=True))
async def start(message: types.Message, db: Session, command: CommandObject):
    ident = command.args
    stmp = (
        update(NotificationData)
        .where(NotificationData.id == ident)
        .values(telegram_id=message.from_user.id)
    )
    db.execute(stmp)
    db.commit()
    await message.answer("You are subscribed to notifications.")
