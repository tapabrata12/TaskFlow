import logging

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.dependency import get_current_user
from src.auth.project_permission import (
    get_project_membership,
    require_project_owner
)
from src.db.connect_db import MongoDB
from src.models.membership_model import create_membership_model
from src.schema.Membership import (
    AddMember,
    MemberResponse,
    MembersResponse
)


router = APIRouter(
    prefix="/projects",
    tags=["Project Memberships"]
)

logger = logging.getLogger(__name__)


def validate_project_id(project_id: str) -> ObjectId:

    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID"
        )

    return ObjectId(project_id)


@router.post(
    "/{project_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_member(
    project_id: str,
    data: AddMember,
    current_user: dict = Depends(get_current_user)
):

    project_object_id = validate_project_id(project_id)

    db = MongoDB.get_db()

    projects = db["projects"]
    users = db["users"]
    memberships = db["memberships"]

    project = projects.find_one({
        "_id": project_object_id
    })

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    require_project_owner(
        project_id=project_object_id,
        user_id=current_user["_id"]
    )

    email = data.email.lower()

    user = users.find_one({
        "email": email
    })

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email is not registered"
        )

    existing_membership = memberships.find_one({
        "project_id": project_object_id,
        "user_id": user["_id"]
    })

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project"
        )

    membership = create_membership_model(
        user_id=user["_id"],
        project_id=project_object_id,
        role="member"
    )

    memberships.insert_one(membership)

    return MemberResponse(
        user_id=str(user["_id"]),
        user_name=user["user_name"],
        email=user["email"],
        role="member",
        joined_at=membership["created_at"].isoformat()
    )

@router.get(
    "/{project_id}/members",
    response_model=MembersResponse,
    status_code=status.HTTP_200_OK
)
async def get_members(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):

    project_object_id = validate_project_id(project_id)

    db = MongoDB.get_db()

    projects = db["projects"]
    users = db["users"]
    memberships = db["memberships"]

    project = projects.find_one({
        "_id": project_object_id
    })

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    get_project_membership(
        project_id=project_object_id,
        user_id=current_user["_id"]
    )

    project_memberships = memberships.find({
        "project_id": project_object_id
    })

    members = []

    for membership in project_memberships:

        user = users.find_one({
            "_id": membership["user_id"]
        })

        if not user:
            continue

        members.append(
            MemberResponse(
                user_id=str(user["_id"]),
                user_name=user["user_name"],
                email=user["email"],
                role=membership["role"],
                joined_at=membership["created_at"].isoformat()
            )
        )

    return MembersResponse(
        members=members
    )

@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    project_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):

    project_object_id = validate_project_id(project_id)

    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

    member_object_id = ObjectId(user_id)

    db = MongoDB.get_db()

    projects = db["projects"]
    memberships = db["memberships"]

    project = projects.find_one({
        "_id": project_object_id
    })

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    require_project_owner(
        project_id=project_object_id,
        user_id=current_user["_id"]
    )

    membership = memberships.find_one({
        "project_id": project_object_id,
        "user_id": member_object_id
    })

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this project"
        )

    if membership["role"] == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project owner cannot be removed"
        )

    memberships.delete_one({
        "project_id": project_object_id,
        "user_id": member_object_id
    })

    return None