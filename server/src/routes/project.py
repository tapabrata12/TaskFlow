import logging

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.dependency import get_current_user
from src.db.connect_db import MongoDB
from src.models.membership_model import create_membership_model
from src.models.project_model import create_project_model
from src.schema.Project import (
    CreateProject,
    ProjectResponse,
    UpdateProject,
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)

logger = logging.getLogger(__name__)


def project_to_response(project: dict) -> ProjectResponse:
    return ProjectResponse(
        id=str(project["_id"]),
        name=project["name"],
        description=project.get("description", ""),
        created_by=str(project["created_by"]),
        created_at=project["created_at"].isoformat(),
        updated_at=project["updated_at"].isoformat(),
    )


def validate_project_id(project_id: str) -> ObjectId:
    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID",
        )

    return ObjectId(project_id)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    data: CreateProject,
    current_user: dict = Depends(get_current_user),
):
    try:
        db = MongoDB.get_db()

        projects = db["projects"]
        memberships = db["memberships"]

        user_id = current_user["_id"]

        project = create_project_model(
            name=data.name.strip(),
            description=data.description.strip(),
            user_id=user_id,
        )

        result = projects.insert_one(project)

        project_id = result.inserted_id

        membership = create_membership_model(
            user_id=user_id,
            project_id=project_id,
            role="owner",
        )

        memberships.insert_one(membership)

        project["_id"] = project_id

        return project_to_response(project)

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to create project for user=%s",
            current_user.get("_id"),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )


@router.get(
    "",
    response_model=list[ProjectResponse],
)
async def get_projects(
    current_user: dict = Depends(get_current_user),
):
    try:
        db = MongoDB.get_db()

        memberships = db["memberships"]
        projects = db["projects"]

        user_id = current_user["_id"]

        user_memberships = memberships.find(
            {"user_id": user_id}
        )

        project_ids = [
            membership["project_id"]
            for membership in user_memberships
        ]

        if not project_ids:
            return []

        user_projects = projects.find(
            {"_id": {"$in": project_ids}}
        )

        return [
            project_to_response(project)
            for project in user_projects
        ]

    except Exception:
        logger.exception(
            "Failed to get projects for user=%s",
            current_user.get("_id"),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get projects",
        )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = MongoDB.get_db()

    project_object_id = validate_project_id(project_id)

    memberships = db["memberships"]
    projects = db["projects"]

    user_id = current_user["_id"]

    membership = memberships.find_one(
        {
            "user_id": user_id,
            "project_id": project_object_id,
        }
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )

    project = projects.find_one(
        {"_id": project_object_id}
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project_to_response(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def update_project(
    project_id: str,
    data: UpdateProject,
    current_user: dict = Depends(get_current_user),
):
    db = MongoDB.get_db()

    project_object_id = validate_project_id(project_id)

    projects = db["projects"]
    memberships = db["memberships"]

    user_id = current_user["_id"]

    membership = memberships.find_one(
        {
            "user_id": user_id,
            "project_id": project_object_id,
        }
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )

    if membership["role"] != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can update the project",
        )

    project = projects.find_one(
        {"_id": project_object_id}
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    update_data = {}

    if data.name is not None:
        update_data["name"] = data.name.strip()

    if data.description is not None:
        update_data["description"] = data.description.strip()

    if not update_data:
        return project_to_response(project)

    from datetime import datetime, timezone

    update_data["updated_at"] = datetime.now(timezone.utc)

    projects.update_one(
        {"_id": project_object_id},
        {"$set": update_data},
    )

    updated_project = projects.find_one(
        {"_id": project_object_id}
    )

    return project_to_response(updated_project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = MongoDB.get_db()

    project_object_id = validate_project_id(project_id)

    projects = db["projects"]
    memberships = db["memberships"]

    user_id = current_user["_id"]

    membership = memberships.find_one(
        {
            "user_id": user_id,
            "project_id": project_object_id,
        }
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )

    if membership["role"] != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can delete the project",
        )

    project = projects.find_one(
        {"_id": project_object_id}
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Tasks will be deleted here later.
    # We will add that when the Task API is implemented.

    memberships.delete_many(
        {"project_id": project_object_id}
    )

    projects.delete_one(
        {"_id": project_object_id}
    )

    return None