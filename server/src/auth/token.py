import jwt

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.config.Env import settings


class Token:
    ALGORITHM: str = settings.ALGORITHM
    SECRET_KEY: str = settings.JWT_SECRET_KEY

    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @classmethod
    def create_access_token(cls, email: str):
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        payload = {
            "sub": email,
            "type": "access",
            "exp": expire,
        }

        return jwt.encode(
            payload,
            cls.SECRET_KEY,
            algorithm=cls.ALGORITHM,
        )

    @classmethod
    def create_refresh_token(cls, email: str):
        expire = datetime.now(timezone.utc) + timedelta(
            days=cls.REFRESH_TOKEN_EXPIRE_DAYS
        )

        jti = str(uuid4())

        payload = {
            "sub": email,
            "type": "refresh",
            "jti": jti,
            "exp": expire,
        }

        return jwt.encode(
            payload,
            cls.SECRET_KEY,
            algorithm=cls.ALGORITHM,
        )

    @classmethod
    def create_tokens(cls, email: str):
        access_token = cls.create_access_token(email)
        refresh_token = cls.create_refresh_token(email)

        return access_token, refresh_token

    @classmethod
    def decode_token(cls, token: str):
        return jwt.decode(
            token,
            cls.SECRET_KEY,
            algorithms=[cls.ALGORITHM],
        )