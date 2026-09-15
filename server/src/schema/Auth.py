from pydantic import BaseModel, Field, EmailStr
from typing import Annotated

class TokenMessage(BaseModel):
    access_token : Annotated[str, Field(..., min_length=3, description="This is for access token")]
    refresh_token : Annotated[str, Field(..., min_length=3, description="This is for refresh token")]
    token_type: str = "bearer"

class AccessToken(BaseModel):
    access_token : Annotated[str, Field(..., min_length=3, max_length=100, description="This is for access token")]

class RefreshToken(BaseModel):
    refresh_token : Annotated[str, Field(..., min_length=3, description="This is for access token")]

class Signup(BaseModel):
    user_name : Annotated[str, Field(...,min_length=3, max_length=100, description="This is for user name")]
    email : Annotated[EmailStr, Field(..., description="This is for email address")]
    password : Annotated[str, Field(..., min_length=6, max_length=20, description="This is for password")]

class SignupCompleteMessage(BaseModel):
    message : Annotated[str, Field("User successfully signed up", description="This is for user name")]
    email : Annotated[EmailStr, Field(..., description="This is for email address")]
    token : Annotated[TokenMessage, Field(..., description="Authentication tokens")]

class Login(BaseModel):
    email : Annotated[EmailStr, Field(..., description="This is for email address")]
    password : Annotated[str, Field(..., min_length=6, max_length=20, description="This is for password")]

class LoginCompleteMessage(BaseModel):
    message : Annotated[str, Field("User successfully Logged in", description="This is for user name")]
    email : Annotated[EmailStr, Field(..., description="This is for email address")]
    token : Annotated[TokenMessage, Field(..., description="Authentication tokens")]

class Profile(BaseModel):
    user_name : Annotated[str, Field(..., min_length=3, max_length=100, description="This is for user name")]
    email : Annotated[EmailStr, Field(..., description="This is for email address")]

class Logout(BaseModel):
    message : Annotated[str,Field(..., min_length=3, description="Logout message after user logged out")]
