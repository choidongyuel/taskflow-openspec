import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

TASK_STATUSES = ("TODO", "DOING", "DONE")


# ---- Auth ----
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    team_id: int | None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    token: str
    user: UserOut


# ---- Team ----
class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=30)


class TeamJoinRequest(BaseModel):
    invite_code: str


class TeamOut(BaseModel):
    id: int
    name: str
    invite_code: str
    owner_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class TeamMemberOut(BaseModel):
    id: int
    email: str
    is_owner: bool
    created_at: datetime.datetime


# ---- Task ----
class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    assignee_id: int | None = None


class TaskUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    assignee_id: int | None = None


class TaskStatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in TASK_STATUSES:
            raise ValueError("invalid status")
        return value


class TaskOut(BaseModel):
    id: int
    team_id: int
    title: str
    status: str
    creator_id: int
    assignee_id: int | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ---- Chat ----
class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)


class MessageOut(BaseModel):
    id: int
    team_id: int
    user_id: int
    content: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
