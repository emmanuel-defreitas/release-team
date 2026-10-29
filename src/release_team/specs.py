"""Validated YAML registry and portable declarations."""

from importlib.resources import files
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, model_validator

from .contracts import Action, Contract


class Metadata(Contract):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    name: str
    version: str


class Permissions(Contract):
    repository: Literal["read", "none"] = "read"
    artifacts: Literal["draft"] = "draft"
    public_publish: Literal[False] = False


class AgentBody(Contract):
    role: str
    instructions: str
    skills: list[str]
    actions: list[Action]
    runtime: str = "provider-neutral"
    input_contract: Literal["task.schema.json"] = "task.schema.json"
    output_contract: Literal["result.schema.json"] = "result.schema.json"
    permissions: Permissions = Field(default_factory=Permissions)


class AgentSpec(Contract):
    apiVersion: Literal["release-team.dev/v1alpha1"]
    kind: Literal["Agent"]
    metadata: Metadata
    spec: AgentBody


class SkillBody(Contract):
    description: str
    adapter: str
    implementation_status: Literal["draft-only", "planned"]
    capabilities: list[str]
    requirements: list[str]
    permissions: Permissions = Field(default_factory=Permissions)


class SkillSpec(Contract):
    apiVersion: Literal["release-team.dev/v1alpha1"]
    kind: Literal["Skill"]
    metadata: Metadata
    spec: SkillBody


class Registry(Contract):
    apiVersion: Literal["release-team.dev/v1alpha1"]
    kind: Literal["Registry"]
    agents: list[AgentSpec]
    skills: list[SkillSpec]

    @model_validator(mode="after")
    def references(self) -> "Registry":
        agent_ids = [a.metadata.id for a in self.agents]
        skill_ids = [s.metadata.id for s in self.skills]
        if len(set(agent_ids)) != len(agent_ids) or len(set(skill_ids)) != len(skill_ids):
            raise ValueError("registry IDs must be unique within each kind")
        for agent in self.agents:
            missing = set(agent.spec.skills) - set(skill_ids)
            if missing:
                raise ValueError(f"unknown skills for {agent.metadata.id}: {sorted(missing)}")
        return self

    def agent(self, agent_id: str) -> AgentSpec:
        for agent in self.agents:
            if agent.metadata.id == agent_id:
                return agent
        raise ValueError(f"unknown agent: {agent_id}")


def load_registry(path: Path | None = None) -> Registry:
    text = (
        path.read_text()
        if path
        else files("release_team").joinpath("assets/registry.yaml").read_text()
    )
    return Registry.model_validate(yaml.safe_load(text))
