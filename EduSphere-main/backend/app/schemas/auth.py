from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PathChoice = Literal["own_materials", "learn_new"]


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@") or value.count("@") != 1:
            raise ValueError("Invalid email")
        local, domain = value.rsplit("@", 1)
        if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("Invalid email")
        return value

    @model_validator(mode="after")
    def password_not_email(self) -> "SignupRequest":
        if self.password == self.email:
            raise ValueError("Invalid password")
        return self


class LoginRequest(SignupRequest):
    pass


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    created_at: str


class NotificationConsent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    push: bool = False
    email: bool = False
    in_app: bool = False


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    display_name: str | None
    goal: str | None
    timezone: str
    locale: str
    path_preference: PathChoice | None
    notification_consent: NotificationConsent
    onboarding_completed: bool


class MeResponse(BaseModel):
    user: UserResponse
    profile: ProfileResponse


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str | None = Field(default=None, max_length=60)
    goal: str | None = Field(default=None, max_length=280)
    timezone: str | None = None
    locale: str | None = Field(default=None, max_length=10)
    notification_consent: NotificationConsent | None = None

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str | None) -> str | None:
        if value is not None:
            try:
                ZoneInfo(value)
            except (ZoneInfoNotFoundError, ValueError) as exc:
                raise ValueError("Invalid timezone") from exc
        return value


class OnboardingComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path_choice: PathChoice
