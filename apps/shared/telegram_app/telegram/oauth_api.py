from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
import hashlib
import hmac
import time
from .config import TELEGRAM_TOKEN
from .crud import get_async_sessionmaker, TelegramCrud
from .bot import bot
from aiogram.exceptions import TelegramAPIError

app = FastAPI()

def verify_telegram_auth(data: dict, bot_token: str) -> bool:
    # Extract and validate hash
    check_hash = data.pop('hash', None)
    if not check_hash:
        return False
    
    # Build data string for verification
    data_check_arr = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = '\n'.join(data_check_arr)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    # Verify hash matches
    if hmac_hash != check_hash:
        return False
    
    # Check if auth is not too old (1 day limit)
    auth_date = int(data.get('auth_date', 0))
    if time.time() - auth_date > 86400:
        return False
    return True

def get_crud():
    sessionmaker = get_async_sessionmaker()
    return TelegramCrud(sessionmaker)

@app.post("/auth/telegram-oauth")
async def telegram_oauth(request: Request, crud: TelegramCrud = Depends(get_crud)):
    form = await request.form()
    data = dict(form)
    
    # Verify Telegram OAuth data
    data_for_check = data.copy()
    if not verify_telegram_auth(data_for_check, TELEGRAM_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram OAuth data")
    
    # Extract user info
    user_id = data.get('id')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing user id")
    ip_address = request.client.host if request.client else None

    from derisk-research.apps.dashboard_app.app.models.watcher import NotificationData
    
    # Update existing user or create new one
    obj = await crud.get_objects_by_filter(NotificationData, 0, 1, telegram_id=str(user_id))
    if obj:
        await crud.update_values(NotificationData, obj.id, ip_address=ip_address)
    else:
        notif = NotificationData(telegram_id=str(user_id), ip_address=ip_address)
        await crud.write_to_db(notif)
    
    # Send welcome message
    try:
        await bot.send_message(chat_id=user_id, text="Hello! You are now authenticated via Telegram.")
    except TelegramAPIError:
        pass  
    
    return JSONResponse({"status": "ok"}, status_code=200) 