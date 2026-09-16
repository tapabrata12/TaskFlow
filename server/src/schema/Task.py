from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class CreateTask(BaseModel):
    title: Annotated[
        str,
        Field(
            ...,
            min_length=1,
            max_length=200,
            description="Task title",
        ),
    ]

    description: Annotated[
        str,
        Field(
            default="",
            max_length=2000,
            description="Task description",
        ),
    ]

    status: Annotated[
        str,
        Field(
            default="to-do",
            description="Task status",
        ),
    ]

    priority: Annotated[
        str,
        Field(
            default="medium",
            description="Task priority",
        ),
    ]

    due_date: datetime | None = None

    assignee_id: str | None = None


class UpdateTask(BaseModel):
    title: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=200,
        ),
    ]

    description: Annotated[
        str | None,
        Field(
            default=None,
            max_length=2000,
        ),
    ]

    status: str | None = None

    priority: str | None = None

    due_date: datetime | None = None

    assignee_id: str | None = None


class TaskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: str
    status: str
    priority: str
    due_date: datetime | None
    assignee_id: str | None
    created_by: str
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
