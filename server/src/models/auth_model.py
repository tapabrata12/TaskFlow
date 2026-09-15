from typing import Any
from datetime import datetime, timezone


def create_user_model(user: dict) -> dict[str, Any]:
    return {
        "user_name": user["user_name"],
        "email": user["email"].lower(),
        "password_hash": user["password_hash"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }