import logging

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.auth.dependency import get_current_user
from src.db.connect_db import MongoDB
from src.models.membership_model import create_membership_model
from src.models.project_model import create_project_model
from src.schema.Project import CreateProject, ProjectResponse


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

        user_id = str(current_user["_id"])

        project = create_project_model(
            name=data.name.strip(),
            description=data.description.strip(),
            user_id=user_id,
        )

        result = projects.insert_one(project)

        project_id = result.inserted_id

        membership = create_membership_model(
            user_id=user_id,
            project_id=str(project_id),
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