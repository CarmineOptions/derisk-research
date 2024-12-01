from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.models import NotificationData
from telegram.crud import TelegramCrud
from .utils import kb

create_notification_router = Router()


class NotificationFormStates(StatesGroup):
    """States for the notification form process."""

    wallet_id = State()
    health_ratio_level = State()
    protocol_id = State()


# Define constants for health ratio limits
HEALTH_RATIO_MIN = 0
HEALTH_RATIO_MAX = 10


@create_notification_router.callback_query(F.data == "create_subscription")
async def start_form(callback: types.CallbackQuery, state: FSMContext):
    """Initiates the notification creation form by asking for the wallet ID."""
    await state.set_state(NotificationFormStates.wallet_id)
    return callback.message.edit_text(
        "Please enter your wallet ID:",
        reply_markup=kb.cancel_form(),
    )


@create_notification_router.message(NotificationFormStates.wallet_id)
async def process_wallet_id(message: types.Message, state: FSMContext):
    """Processes the wallet ID input from the user."""
    await state.update_data(wallet_id=message.text)
    await state.set_state(NotificationFormStates.health_ratio_level)
    return message.answer(
        "Please enter your health ratio level (between 0 and 10):",
        reply_markup=kb.cancel_form(),
    )


@create_notification_router.message(NotificationFormStates.health_ratio_level)
async def process_health_ratio(message: types.Message, state: FSMContext):
    """Processes the health ratio level input from the user."""
    try:
        health_ratio = float(message.text)
        if not (HEALTH_RATIO_MIN <= health_ratio <= HEALTH_RATIO_MAX):
            raise ValueError
    except ValueError:
        return message.answer(
            "Please enter a valid number between 0 and 10.",
            reply_markup=kb.cancel_form(),
        )

    await state.update_data(health_ratio_level=health_ratio)
    await state.set_state(NotificationFormStates.protocol_id)

    return message.answer(
        "Please select your protocol:",
        reply_markup=kb.protocols(),
    )


@create_notification_router.callback_query(F.data.startswith("protocol_"))
async def process_protocol(
    callback: types.CallbackQuery, state: FSMContext, crud: TelegramCrud
):
    """Processes the selected protocol and saves the subscription data."""
    protocol_id = callback.data.replace("protocol_", "")
    data = await state.get_data()

    subscription = NotificationData(
        wallet_id=data["wallet_id"],
        health_ratio_level=data["health_ratio_level"],
        protocol_id=protocol_id,
        telegram_id=str(callback.from_user.id),
        email=None,
        ip_address=None,
    )
    await crud.write_to_db(subscription)

    await state.clear()
    return callback.message.edit_text(
        "Subscription created successfully!",
        reply_markup=kb.go_menu(),
    )


@create_notification_router.callback_query(F.data == "cancel_form")
async def cancel_form(callback: types.CallbackQuery, state: FSMContext):
    """Cancels the form and clears the state."""
    await state.clear()
    return callback.message.edit_text(
        "Form cancelled.",
        reply_markup=kb.go_menu(),
    )
