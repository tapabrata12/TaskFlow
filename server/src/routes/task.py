import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.auth.dependency import get_current_user
from src.auth.project_permission import get_project_membership
from src.db.connect_db import MongoDB
from src.models.task_model import create_task_model
from src.schema.Task import CreateTask, TaskResponse, UpdateTask


router = APIRouter(
    prefix="/projects",
    tags=["Tasks"],
)

logger = logging.getLogger(__name__)


def validate_project_id(project_id: str) -> ObjectId:

    if not ObjectId.is_valid(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID",
        )

    return ObjectId(project_id)


def validate_user_id(user_id: str) -> ObjectId:

    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID",
        )

    return ObjectId(user_id)


def task_to_response(task: dict) -> TaskResponse:

    return TaskResponse(
        id=str(task["_id"]),
        project_id=str(task["project_id"]),
        title=task["title"],
        description=task["description"],
        status=task["status"],
        priority=task["priority"],
        due_date=task.get("due_date"),
        assignee_id=(
            str(task["assignee_id"])
            if task.get("assignee_id")
            else None
        ),
        created_by=str(task["created_by"]),
        completed_at=task.get("completed_at"),
        created_at=task["created_at"],
        updated_at=task["updated_at"],
    )


@router.post(
    "/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: str,
    data: CreateTask,
    current_user: dict = Depends(get_current_user),
):

    project_object_id = validate_project_id(project_id)

    db = MongoDB.get_db()

    projects = db["projects"]
    memberships = db["memberships"]
    users = db["users"]
    tasks = db["tasks"]

    # Check project exists
    project = projects.find_one({
        "_id": project_object_id
    })

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check current user belongs to project
    get_project_membership(
        project_id=project_object_id,
        user_id=current_user["_id"],
    )

    # Validate status
    allowed_statuses = {
        "to-do",
        "progress",
        "done",
    }

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task status",
        )

    # Validate priority
    allowed_priorities = {
        "low",
        "medium",
        "high",
    }

    if data.priority not in allowed_priorities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task priority",
        )

    # Due date cannot be in the past
    if data.due_date:

        now = datetime.now(timezone.utc)

        if data.due_date < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be in the past",
            )

    # Validate assignee
    assignee_object_id = None

    if data.assignee_id:

        assignee_object_id = validate_user_id(
            data.assignee_id
        )

        # User must exist
        user = users.find_one({
            "_id": assignee_object_id
        })

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee user not found",
            )

        # Assignee must be a member of this project
        membership = memberships.find_one({
            "project_id": project_object_id,
            "user_id": assignee_object_id,
        })

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of this project",
            )

    task = create_task_model(
        project_id=project_object_id,
        title=data.title.strip(),
        description=data.description.strip(),
        status=data.status,
        priority=data.priority,
        due_date=data.due_date,
        assignee_id=assignee_object_id,
        created_by=current_user["_id"],
    )

    result = tasks.insert_one(task)

    task["_id"] = result.inserted_id

    return task_to_response(task)

@router.get(
    "/{project_id}/tasks",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
)
async def get_tasks(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):

    project_object_id = validate_project_id(project_id)

    db = MongoDB.get_db()

    projects = db["projects"]
    tasks = db["tasks"]

    project = projects.find_one({
        "_id": project_object_id
    })

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Only project members can see tasks
    get_project_membership(
        project_id=project_object_id,
        user_id=current_user["_id"],
    )

    project_tasks = tasks.find({
        "project_id": project_object_id
    })

    return [
        task_to_response(task)
        for task in project_tasks
    ]

@router.put(
    "/{project_id}/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def update_task(
    project_id: str,
    task_id: str,
    data: UpdateTask,
    current_user: dict = Depends(get_current_user),
):
    project_object_id = validate_project_id(project_id)

    if not ObjectId.is_valid(task_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID",
        )

    task_object_id = ObjectId(task_id)

    db = MongoDB.get_db()

    projects = db["projects"]
    memberships = db["memberships"]
    users = db["users"]
    tasks = db["tasks"]

    # Check project exists
    project = projects.find_one({
        "_id": project_object_id
    })

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check current user is a project member
    membership = get_project_membership(
        project_id=project_object_id,
        user_id=current_user["_id"],
    )

    # Find task
    task = tasks.find_one({
        "_id": task_object_id,
        "project_id": project_object_id,
    })

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Validate title
    if "title" in update_data:
        title = update_data["title"].strip()

        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task title cannot be empty",
            )

        update_data["title"] = title

    # Validate description
    if "description" in update_data:
        update_data["description"] = update_data["description"].strip()

    # Validate status
    allowed_statuses = {
        "to-do",
        "progress",
        "done",
    }

    if "status" in update_data:
        if update_data["status"] not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid task status",
            )

    # Validate priority
    allowed_priorities = {
        "low",
        "medium",
        "high",
    }

    if "priority" in update_data:
        if update_data["priority"] not in allowed_priorities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid task priority",
            )

    # Validate due date
    if "due_date" in update_data and update_data["due_date"] is not None:
        now = datetime.now(timezone.utc)

        if update_data["due_date"] < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be in the past",
            )

    # Validate assignee
    if "assignee_id" in update_data:

        if update_data["assignee_id"] is None:
            update_data["assignee_id"] = None

        else:
            assignee_object_id = validate_user_id(
                update_data["assignee_id"]
            )

            user = users.find_one({
                "_id": assignee_object_id
            })

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignee user not found",
                )

            assignee_membership = memberships.find_one({
                "project_id": project_object_id,
                "user_id": assignee_object_id,
            })

            if not assignee_membership:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee must be a member of this project",
                )

            update_data["assignee_id"] = assignee_object_id

    # Handle completed_at
    if "status" in update_data:

        new_status = update_data["status"]

        if new_status == "done":
            update_data["completed_at"] = datetime.now(timezone.utc)

        elif task["status"] == "done":
            update_data["completed_at"] = None

    update_data["updated_at"] = datetime.now(timezone.utc)

    tasks.update_one(
        {
            "_id": task_object_id,
            "project_id": project_object_id,
        },
        {
            "$set": update_data
        },
    )

    updated_task = tasks.find_one({
        "_id": task_object_id
    })

    return task_to_response(updated_task)

@router.delete(
    "/{project_id}/tasks/{task_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_task(
    project_id: str,
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    project_object_id = validate_project_id(project_id)

    if not ObjectId.is_valid(task_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID",
        )

    task_object_id = ObjectId(task_id)

    db = MongoDB.get_db()

    projects = db["projects"]
    tasks = db["tasks"]

    # Check project exists
    project = projects.find_one({
        "_id": project_object_id
    })

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check current user is a project member
    get_project_membership(
        project_id=project_object_id,
        user_id=current_user["_id"],
    )

    # Check task exists inside this project
    task = tasks.find_one({
        "_id": task_object_id,
        "project_id": project_object_id,
    })

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    result = tasks.delete_one({
        "_id": task_object_id,
        "project_id": project_object_id,
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task could not be deleted",
        )

    return {
        "message": "Task deleted successfully"
    }