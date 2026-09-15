import logging
import jwt
from fastapi import APIRouter, status, HTTPException,Depends
from src.schema.Auth import (
    TokenMessage,
    SignupCompleteMessage,
    LoginCompleteMessage,
    Profile,
    Logout,
    Signup,
    Login,
    RefreshToken,
)
from src.db.connect_db import MongoDB
from src.auth.password import HashPassword
from src.models.auth_model import create_user_model
from src.auth.dependency import get_current_user
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
async def login(user: Login):
    try:
        db = MongoDB.get_db()
        collection = db[settings.COLLECTION]

        email = user.email.lower()

        existing_user = collection.find_one({"email": email})

        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        password_correct = HashPassword.check_password(
            user.password,
            existing_user["password_hash"],
        )

        if not password_correct:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token, refresh_token = Token.create_tokens(email)

        tokens = TokenMessage(
            access_token=access_token,
            refresh_token=refresh_token,
        )

        return LoginCompleteMessage(
            email=email,
            token=tokens,
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception("Login failed for email=%s", user.email)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

@router.get(
    "/profile",
    response_model=Profile,
    status_code=status.HTTP_200_OK,
)
async def profile(current_user: dict = Depends(get_current_user)):
    return Profile(
        user_name=current_user["user_name"],
        email=current_user["email"],
    )


@router.post(
    "/refresh",
    response_model=TokenMessage,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(data: RefreshToken):
    try:
        payload = Token.decode_token(data.refresh_token)

        token_type = payload.get("type")
        email = payload.get("sub")

        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if not email:
            jti = payload.get("jti")

            if not jti:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            db = MongoDB.get_db()

            revoked_token = db["revoked_tokens"].find_one({
                "jti": jti
            })

            if revoked_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been revoked",
                )

        db = MongoDB.get_db()
        users = db[settings.COLLECTION]

        user = users.find_one({"email": email})

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        access_token = Token.create_access_token(email)

        return TokenMessage(
            access_token=access_token,
            refresh_token=data.refresh_token,
        )

    except HTTPException:
        raise

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    except Exception:
        logger.exception("Refresh token failed")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
@router.post(
    "/logout",
    response_model=Logout,
    status_code=status.HTTP_200_OK,
)
async def logout(data: RefreshToken):
    try:
        payload = Token.decode_token(data.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        jti = payload.get("jti")

        if not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        db = MongoDB.get_db()

        db["revoked_tokens"].insert_one(
            {
                "jti": jti,
                "expires_at": payload["exp"],
            }
        )

        return Logout(
            message="User successfully logged out"
        )

    except HTTPException:
        raise

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    except Exception:
        logger.exception("Logout failed")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
