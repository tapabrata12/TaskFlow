from typing import Annotated

from pydantic import BaseModel, EmailStr, Field


class AddMember(BaseModel):
    email: Annotated[
        EmailStr,
        Field(..., description="Email of the registered user to add")
    ]


class MemberResponse(BaseModel):
    user_id: str
    user_name: str
    email: EmailStr
    role: str
    joined_at: str


class MembersResponse(BaseModel):
    members: list[MemberResponse]