from aiogram import Router

from dashboard_app.app.telegram_app.telegram.handlers.command import cmd_router
from dashboard_app.app.telegram_app.telegram.handlers.menu import menu_router
from dashboard_app.app.telegram_app.telegram.handlers.create_notification import create_notification_router

# Create the main router to simplify imports
index_router = Router()
index_router.include_router(cmd_router)
index_router.include_router(menu_router)
index_router.include_router(create_notification_router)
