import jwt
import os
import dotenv

from fastapi import APIRouter, HTTPException
from fastapi import Body, status
from pydantic import EmailStr
from schemas.schemas import Token
from datetime import timedelta, datetime, timezone


dotenv.load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", default=86400))

auth_router = APIRouter()


@auth_router.post("/obtain_token", response_model=Token, status_code=status.HTTP_200_OK)
def obtain_token(
    wallet_id: str = Body(default=None),
    email: EmailStr = Body(default=None),
) -> Token:
    """
    Obtain an access token based on either wallet_id or email.

    Args:
        wallet_id (str, optional): The wallet ID to generate the token for. Defaults to None.
        email (EmailStr, optional): The email to generate the token for. Defaults to None.

    Returns:
        Token: The generated access token.

    Raises:
        HTTPException: If neither wallet_id nor email is provided, raises a 400 Bad Request error.
    """
    if wallet_id:
        token = create_access_token({"wallet_id": wallet_id})
    elif email:
        token = create_access_token({"email": email})
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either wallet_id or email must be provided")

    return token


def create_access_token(data: dict) -> Token:
    """
    Generates a new access token with an expiration time.

    Args:
        data (dict): The data to be encoded into the token.

    Returns:
        Token: An object containing the encoded JWT access token and its expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return Token(access_token=encoded_jwt, expiration_date=expire)
