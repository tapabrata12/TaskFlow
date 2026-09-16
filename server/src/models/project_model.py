from datetime import datetime, timezone
from typing import Any
from bson import ObjectId


def create_project_model(
    name: str,
    description: str,
    user_id: ObjectId,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)

    return {
        "name": name,
        "description": description,
        "created_by": user_id,
        "created_at": now,
        "updated_at": now,
    }