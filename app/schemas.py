from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    bio: str = Field(default="", max_length=800)
    specialty: str = Field(default="", max_length=120)


class QuestionCreate(BaseModel):
    title: str = Field(min_length=10, max_length=180)
    description: str = Field(min_length=20, max_length=5_000)
    tags: list[str] = Field(default_factory=list, max_length=5)


class CommentCreate(BaseModel):
    content: str = Field(min_length=10, max_length=2_000)


class ArticleCreate(BaseModel):
    title: str = Field(min_length=10, max_length=180)
    summary: str = Field(min_length=20, max_length=320)
    content: str = Field(min_length=100, max_length=20_000)
    tags: list[str] = Field(default_factory=list, max_length=5)


class DoctorApplicationCreate(BaseModel):
    license_number: str = Field(min_length=4, max_length=100)
    specialty: str = Field(min_length=3, max_length=120)
    document_url: str = Field(min_length=8, max_length=500)
    motivation: str = Field(min_length=30, max_length=2_000)


class DoctorApplicationReview(BaseModel):
    status: Literal["approved", "rejected"]
    admin_note: str = Field(default="", max_length=1_000)
