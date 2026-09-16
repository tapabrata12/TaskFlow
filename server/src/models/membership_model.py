from datetime import datetime, timezone
from typing import Any
from bson import ObjectId


def create_membership_model(
    user_id: ObjectId,
    project_id: ObjectId,
    role: str,
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "project_id": project_id,
        "role": role,
        "created_at": datetime.now(timezone.utc),
    }