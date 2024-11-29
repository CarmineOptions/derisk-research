from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.models import NotificationData
from database.schemas import NotificationForm
from telegram.crud import TelegramCrud
from utils.values import ProtocolIDs
from fastapi import status

create_notification_router = Router()

class NotificationFormStates(StatesGroup):
    wallet_id = State()
    health_ratio_level = State()
    protocol_id = State()

@create_notification_router.callback_query(F.data == "create_subscription")
async def start_form(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(NotificationFormStates.wallet_id)
    await callback.message.edit_text(
        "Please enter your wallet ID:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Cancel", callback_data="cancel_form")]
        ])
    )

@create_notification_router.message(NotificationFormStates.wallet_id)
async def process_wallet_id(message: types.Message, state: FSMContext):
    await state.update_data(wallet_id=message.text)
    await state.set_state(NotificationFormStates.health_ratio_level)
    await message.answer(
        "Please enter your health ratio level (between 0 and 10):",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Cancel", callback_data="cancel_form")]
        ])
    )

@create_notification_router.message(NotificationFormStates.health_ratio_level)
async def process_health_ratio(message: types.Message, state: FSMContext):
    try:
        health_ratio = float(message.text)
        if not (0 <= health_ratio <= 10):
            raise ValueError
        
        await state.update_data(health_ratio_level=health_ratio)
        await state.set_state(NotificationFormStates.protocol_id)
        
        # Create protocol selection buttons
        protocol_buttons = []
        for protocol in ProtocolIDs:
            protocol_buttons.append([
                types.InlineKeyboardButton(
                    text=protocol.value,
                    callback_data=f"protocol_{protocol.value}"
                )
            ])
        protocol_buttons.append([
            types.InlineKeyboardButton(text="Cancel", callback_data="cancel_form")
        ])
        
        await message.answer(
            "Please select your protocol:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=protocol_buttons)
        )
    except ValueError:
        await message.answer(
            "Please enter a valid number between 0 and 10.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="Cancel", callback_data="cancel_form")]
            ])
        )

@create_notification_router.callback_query(F.data.startswith("protocol_"))
async def process_protocol(callback: types.CallbackQuery, state: FSMContext, crud: TelegramCrud):
    protocol_id = callback.data.replace("protocol_", "")
    form_data = await state.get_data()
    
    notification = NotificationForm(
        wallet_id=form_data["wallet_id"],
        health_ratio_level=form_data["health_ratio_level"],
        protocol_id=protocol_id,
        telegram_id=str(callback.from_user.id),
        email=""
    )
    
    subscription = NotificationData(**notification.model_dump())
    subscription_id = crud.write_to_db(obj=subscription)
    
    await state.clear()
    await callback.message.edit_text(
        "Subscription created successfully!",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Go to menu", callback_data="go_menu")]
        ])
    )

@create_notification_router.callback_query(F.data == "cancel_form")
async def cancel_form(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Form cancelled.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Go to menu", callback_data="go_menu")]
        ])
    ) 