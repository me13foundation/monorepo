"""
Request Data Transfer Objects for authentication operations.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from ...domain.entities.user import UserRole


class LoginRequest(BaseModel):
    """Request for user login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    class Config:
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "SecurePassword123!"}
        }


class RegisterUserRequest(BaseModel):
    """Request for user registration."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.VIEWER

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "username": "new_user",
                "full_name": "New User",
                "password": "SecurePassword123!",
                "role": "researcher",
            }
        }


class UpdateUserRequest(BaseModel):
    """Request for updating user profile."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None

    class Config:
        json_schema_extra = {
            "example": {"full_name": "Updated Name", "role": "curator"}
        }


class ChangePasswordRequest(BaseModel):
    """Request for changing user password."""

    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "OldPassword123!",
                "new_password": "NewSecurePassword456!",
            }
        }


class ForgotPasswordRequest(BaseModel):
    """Request for password reset."""

    email: EmailStr

    class Config:
        json_schema_extra = {"example": {"email": "user@example.com"}}


class ResetPasswordRequest(BaseModel):
    """Request for resetting password with token."""

    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset-token-from-email",
                "new_password": "NewSecurePassword456!",
            }
        }


class UpdateProfileRequest(BaseModel):
    """Request for updating user profile."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=100)

    class Config:
        json_schema_extra = {"example": {"full_name": "Updated Full Name"}}


class CreateUserRequest(BaseModel):
    """Request for admin creating a user."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.VIEWER

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin-created@example.com",
                "username": "admin_created",
                "full_name": "Admin Created User",
                "password": "SecurePassword123!",
                "role": "researcher",
            }
        }


class AdminUpdateUserRequest(BaseModel):
    """Request for admin updating a user."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[str] = None  # Will be validated by service

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Updated by Admin",
                "role": "admin",
                "status": "active",
            }
        }
