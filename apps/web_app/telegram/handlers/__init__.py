from aiogram import Router

from .command import cmd_router
from .menu import menu_router

# Create the main router to simplify imports
index_router = Router()
index_router.include_router(cmd_router)
index_router.include_router(menu_router)
