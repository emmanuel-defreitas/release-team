"""Versioned handoff contracts, independent of any model provider."""

from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Action(StrEnum):
    ANALYZE = "analyze"
    DRAFT = "draft"
    PLAN = "plan"
    PUBLISH = "publish"


class Status(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    APPROVAL_REQUIRED = "approval_required"


class Artifact(Contract):
    name: str = Field(min_length=1)
    media_type: str = "text/markdown"
    content: str


class Task(Contract):
    schema_version: Literal["1"] = "1"
    task_id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID = Field(default_factory=uuid4)
    source: str = "user"
    agent: str = Field(min_length=1)
    action: Action
    objective: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    dependencies: list[UUID] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    destination: str | None = None
    content: str | None = None

    @model_validator(mode="after")
    def publication_payload(self) -> "Task":
        if self.action == Action.PUBLISH and (not self.destination or not self.content):
            raise ValueError("publish requires exact content and destination")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("duplicate dependencies")
        if self.task_id in self.dependencies:
            raise ValueError("a task cannot depend on itself")
        return self


class Draft(Contract):
    """Model-owned fields only; models cannot mint identity or approval records."""

    summary: str
    artifacts: list[Artifact]
    warnings: list[str]


class Result(Contract):
    schema_version: Literal["1"] = "1"
    task_id: UUID
    workflow_id: UUID
    agent: str
    status: Status
    summary: str
    artifacts: list[Artifact] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    runtime: str


class Approval(Contract):
    """A record supplied by a trusted host, never by a model or task payload."""

    task_id: UUID
    workflow_id: UUID
    destination: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approved_by: str = Field(min_length=1)
