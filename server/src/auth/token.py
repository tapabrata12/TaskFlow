import jwt
from datetime import datetime, timedelta
from src.config.Env import settings

class Token:
    ALGORITHM: str = settings.ALGORITHM
    SECRET_KEY: str = settings.JWT_SECRET_KEY

    @classmethod
    def create_tokens(cls,email: str):
        # Access Token (Expires in 15 minutes)
        access_expire = datetime.utcnow() + timedelta(minutes=15)
        access_token = jwt.encode({"sub": email, "type": "access", "exp": access_expire}, cls.SECRET_KEY,
                                  algorithm=cls.ALGORITHM)

        # Refresh Token (Expires in 7 days)
        refresh_expire = datetime.utcnow() + timedelta(days=7)
        refresh_token = jwt.encode({"sub": email, "type": "refresh", "exp": refresh_expire}, cls.SECRET_KEY,
                                   algorithm=cls.ALGORITHM)

        return access_token, refresh_token
