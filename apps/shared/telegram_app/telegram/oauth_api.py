from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
import hashlib
import hmac
import time
from .config import TELEGRAM_TOKEN
from .crud import get_async_sessionmaker, TelegramCrud
from .bot import bot
from aiogram.exceptions import TelegramAPIError
from apps.dashboard_app.app.models.base import Base
from sqlalchemy import Mapped, mapped_column, String, IPAddressType, DateTime
from datetime import datetime

app = FastAPI()

class TelegramUser(Base):
    telegram_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(IPAddressType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

def verify_telegram_auth(data: dict, bot_token: str) -> bool:
    check_hash = data.pop('hash', None)
    if not check_hash: 
        return False
    
    data_check_arr = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = '\n'.join(data_check_arr)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if hmac_hash != check_hash:
        return False
    
    auth_date = int(data.get('auth_date', 0))
    if time.time() - auth_date > 86400:
        return False
    return True

def get_crud():
    sessionmaker = get_async_sessionmaker()
    return TelegramCrud(sessionmaker)

@app.post("/auth/telegram-oauth")
async def telegram_oauth(request: Request, crud: TelegramCrud = Depends(get_crud)):
    if not TELEGRAM_TOKEN:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Telegram token not configured")
    
    form = await request.form()
    data = dict(form)
    
    data_for_check = data.copy()
    if not verify_telegram_auth(data_for_check, TELEGRAM_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram OAuth data")
    
    user_id = data.get('id')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing user id")
    ip_address = request.client.host if request.client else None

    existing_user = await crud.get_objects_by_filter(TelegramUser, 0, 1, telegram_id=str(user_id))  # type: ignore
    if existing_user:
        await crud.update_values(TelegramUser, existing_user.id, ip_address=ip_address)  # type: ignore
    else:
        telegram_user = TelegramUser(
            telegram_id=str(user_id),
            ip_address=ip_address
        )
        await crud.write_to_db(telegram_user)  # type: ignore 
    
    if bot is not None:  
        try:
            await bot.send_message(chat_id=user_id, text="Hello! You are now authenticated via Telegram.")  # type: ignore
        except TelegramAPIError:
            pass  
    
    return JSONResponse({"status": "ok"}, status_code=200) 