from typing import Any

from pydantic import BaseModel, field_validator


class RegisterRequest(BaseModel):
    username: str
    password: str

    @classmethod
    @field_validator("password")
    def password_strength(cls, v: Any) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v