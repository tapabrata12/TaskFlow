import logging

from fastapi import APIRouter, status, HTTPException
from src.schema.Auth import TokenMessage,SignupCompleteMessage, LoginCompleteMessage, Profile, Logout, Signup
from src.db.connect_db import MongoDB
from src.auth.password import HashPassword
from src.models.auth_model import create_user_model
from src.auth.token import Token
from src.config.Env import settings
router = APIRouter(prefix='/auth', tags=["User Authentication"])
logger = logging.getLogger(__name__)

@router.post("/signup", response_model= SignupCompleteMessage, status_code=status.HTTP_201_CREATED)
async def register(user: Signup):
    try:
        db = MongoDB.get_db()
        collection = db[settings.COLLECTION]
        email = user.email.lower()
        existing_user = collection.find_one({"email": email})

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered",
            )

        user_dict = user.model_dump()
        user_dict["password_hash"] = HashPassword.hash_password(user.password)
        del user_dict["password"]
        user_model = create_user_model(user_dict)
        collection.insert_one(user_model)
        # Generate the tokens
        access_token, refresh_token = Token.create_tokens(user.email)
        tokens = TokenMessage(access_token=access_token, refresh_token=refresh_token)
        return SignupCompleteMessage(email=user.email, token=tokens)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Signup failed for email=%s", user.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

@router.post("/login", response_model= LoginCompleteMessage, status_code=status.HTTP_200_OK)
async def login():
    pass

@router.get("/profile", response_model= Profile, status_code=status.HTTP_200_OK)
async def profile():
    pass

@router.get("/logout", response_model= Logout, status_code=status.HTTP_200_OK)
async def logout():
    pass
