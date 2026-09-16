from datetime import datetime, timezone
from typing import Any


def create_membership_model(
    user_id: str,
    project_id: str,
    role: str,
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "project_id": project_id,
        "role": role,
        "created_at": datetime.now(timezone.utc),
    }