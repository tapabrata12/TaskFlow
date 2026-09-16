from typing import Annotated

from pydantic import BaseModel, Field


class CreateProject(BaseModel):
    name: Annotated[
        str,
        Field(
            ...,
            min_length=1,
            max_length=100,
            description="Project name",
        ),
    ]

    description: Annotated[
        str,
        Field(
            default="",
            max_length=500,
            description="Project description",
        ),
    ]


class UpdateProject(BaseModel):
    name: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=100,
        ),
    ]

    description: Annotated[
        str | None,
        Field(
            default=None,
            max_length=500,
        ),
    ]


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    created_by: str
    created_at: str
    updated_at: str