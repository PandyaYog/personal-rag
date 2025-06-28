# (imports remain the same: uuid, BaseModel, EmailStr, Field)
import uuid
from pydantic import BaseModel, EmailStr, Field

# --- Base Schemas ---
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$", example="john_doe")
    full_name: str | None = Field(None, example="John Doe")

# --- Schemas for Creating Users ---
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="a_strong_password")

class GoogleIdToken(BaseModel):
    id_token: str = Field(..., description="The ID token received from Google Sign-In on the frontend.")
    
# --- Schemas for Updating Users ---
class UserUpdate(BaseModel):
    # Only full_name and username can be updated directly like this.
    # Email and password changes have their own dedicated flows.
    full_name: str | None = None
    username: str | None = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class EmailUpdate(BaseModel):
    new_email: EmailStr
    password: str # Require password to change email for security

# --- Schemas for Reading User Data (API Response) ---
class User(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True