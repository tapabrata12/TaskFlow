from bson import ObjectId
from fastapi import HTTPException, status

from src.db.connect_db import MongoDB


def get_project_membership(
    project_id: ObjectId,
    user_id: ObjectId
):
    db = MongoDB.get_db()

    membership = db["memberships"].find_one({
        "project_id": project_id,
        "user_id": user_id
    })

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project"
        )

    return membership


def require_project_owner(
    project_id: ObjectId,
    user_id: ObjectId
):
    membership = get_project_membership(
        project_id=project_id,
        user_id=user_id
    )

    if membership["role"] != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can perform this action"
        )

    return membership