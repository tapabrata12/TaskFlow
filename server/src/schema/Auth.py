from pydantic import BaseModel, Field, EmailStr
from typing import Annotated

class Signup(BaseModel):
    user_name = Annotated[str, Field(...,min_length=3, max_length=100, description="This is for user name")]
    email = Annotated[EmailStr, Field(..., description="This is for email address")]
    password = Annotated[str, Field(..., min_length=6, max_length=20, description="This is for password")]

class Login(BaseModel):
    email = Annotated[EmailStr, Field(..., description="This is for email address")]
    password = Annotated[str, Field(..., min_length=6, max_length=20, description="This is for password")]

class Profile(BaseModel):
    user_name = Annotated[str, Field(..., min_length=3, max_length=100, description="This is for user name")]
    email = Annotated[EmailStr, Field(..., description="This is for email address")]