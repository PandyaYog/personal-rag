import uuid
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$", example="john_doe")
    full_name: str | None = Field(None, example="John Doe")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="a_strong_password")

class GoogleIdToken(BaseModel):
    id_token: str = Field(..., description="The ID token received from Google Sign-In on the frontend.")
    
class UserUpdate(BaseModel):
    full_name: str | None = None
    username: str | None = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class EmailUpdate(BaseModel):
    new_email: EmailStr
    password: str 
    
class User(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True