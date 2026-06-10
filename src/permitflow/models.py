from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Validity(StrEnum):
    ONE_MONTH = "1个月"
    THREE_MONTHS = "3个月"
    SIX_MONTHS = "6个月"
    TWELVE_MONTHS = "12个月"
    PERMANENT = "永久"


class UserProfile(BaseModel):
    open_id: str
    name: str
    department: str = ""
    email: str
    manager_open_id: str | None = None


class IntentSlots(BaseModel):
    permission_query: str = ""
    system: str | None = None
    project: str | None = None
    role: str | None = None
    reason: str | None = None
    validity: Validity | None = None
    fields: dict[str, str] = Field(default_factory=dict)


class PermissionItem(BaseModel):
    id: int | None = None
    name: str
    category: str
    jira_project_key: str
    issue_type: str = "Service Request"
    approver_group: str
    required_fields: list[str]
    prerequisites: list[str] = Field(default_factory=list)
    validity_options: list[Validity]
    aliases: list[str]
    sensitive: bool = False
    description: str = ""


class ApplicationDraft(BaseModel):
    permission: PermissionItem
    applicant: UserProfile
    values: dict[str, str] = Field(default_factory=dict)
    validity: Validity | None = None

    @model_validator(mode="after")
    def validate_validity(self) -> "ApplicationDraft":
        if self.validity and self.validity not in self.permission.validity_options:
            raise ValueError("该权限不支持所选有效期")
        if self.permission.sensitive and self.validity == Validity.PERMANENT:
            raise ValueError("敏感权限不能选择永久有效")
        return self

    @property
    def missing_fields(self) -> list[str]:
        missing = [key for key in self.permission.required_fields if not self.values.get(key)]
        if self.validity is None:
            missing.append("validity")
        return missing


class JiraResult(BaseModel):
    success: bool
    ticket_key: str | None = None
    ticket_url: str | None = None
    fallback_text: str | None = None
    fallback_url: str | None = None


class ConversationState(BaseModel):
    user: UserProfile | None = None
    user_input: str = Field(default="", max_length=500)
    slots: IntentSlots | None = None
    candidates: list[PermissionItem] = Field(default_factory=list)
    selected: PermissionItem | None = None
    draft: ApplicationDraft | None = None
    status: str = "new"
    response: dict[str, Any] = Field(default_factory=dict)
