from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def create_task_model(
    project_id: ObjectId,
    title: str,
    description: str,
    status: str,
    priority: str,
    due_date,
    assignee_id: ObjectId | None,
    created_by: ObjectId,
) -> dict[str, Any]:

    now = datetime.now(timezone.utc)

    completed_at = None

    if status == "done":
        completed_at = now

    return {
        "project_id": project_id,
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "due_date": due_date,
        "assignee_id": assignee_id,
        "created_by": created_by,
        "completed_at": completed_at,
        "created_at": now,
        "updated_at": now,
    }