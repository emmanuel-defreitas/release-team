import hashlib
import json
from importlib.resources import files
from pathlib import Path
from typing import Any
from uuid import uuid4

import jsonschema
import pytest
import yaml
from pydantic import ValidationError

from release_team.cli import SCHEMAS, main
from release_team.contracts import Action, Approval, Artifact, Draft, Status, Task
from release_team.engine import Engine, approval_matches, plan
from release_team.runtime import OfflineRuntime, OpenAIRuntime
from release_team.specs import AgentSpec, Registry, load_registry


class RecordingRuntime:
    name = "test"

    def __init__(self) -> None:
        self.tasks: list[Task] = []

    def generate(self, agent: AgentSpec, task: Task) -> Draft:
        self.tasks.append(task)
        return Draft(
            summary=agent.metadata.id,
            artifacts=[Artifact(name="draft.md", content=task.objective)],
            warnings=[],
        )


def test_registry_has_five_independent_agents() -> None:
    registry = load_registry()
    assert {a.metadata.id for a in registry.agents} == {
        "orchestrator",
        "release-analyst",
        "documentation",
        "media-capture",
        "social-publisher",
    }
    engine = Engine(registry, OfflineRuntime())
    for task in plan("Prepare a release draft"):
        task.dependencies = []
        result = engine.run(task)
        assert result.status == Status.COMPLETED
        assert result.task_id == task.task_id
        assert "Offline" in result.summary


def test_registry_rejects_duplicate_ids_and_unknown_skills() -> None:
    raw = load_registry().model_dump(mode="json")
    raw["agents"].append(raw["agents"][0])
    with pytest.raises(ValidationError, match="unique"):
        Registry.model_validate(raw)
    raw = load_registry().model_dump(mode="json")
    raw["agents"][0]["spec"]["skills"] = ["unknown"]
    with pytest.raises(ValidationError, match="unknown skills"):
        Registry.model_validate(raw)


def test_registry_cannot_enable_publication() -> None:
    raw = load_registry().model_dump(mode="json")
    raw["agents"][0]["spec"]["permissions"]["public_publish"] = True
    with pytest.raises(ValidationError):
        Registry.model_validate(raw)


def test_portable_schemas_match_models_and_registry() -> None:
    for name, model in SCHEMAS.items():
        schema = json.loads(
            files("release_team").joinpath(f"assets/schemas/{name}.schema.json").read_text()
        )
        assert schema == model.model_json_schema()
        jsonschema.Draft202012Validator.check_schema(schema)
    registry = load_registry()
    jsonschema.validate(registry.model_dump(mode="json"), Registry.model_json_schema())
    for path in files("release_team").joinpath("assets/agents").iterdir():
        AgentSpec.model_validate(yaml.safe_load(path.read_text()))


def test_task_rejects_unknown_fields_and_invalid_publish_payload() -> None:
    with pytest.raises(ValidationError):
        Task(agent="social-publisher", action=Action.PUBLISH, objective="Publish")
    with pytest.raises(ValidationError):
        Task.model_validate(
            {"agent": "orchestrator", "action": "plan", "objective": "Plan", "approved": True}
        )


def test_task_rejects_self_dependency() -> None:
    identifier = uuid4()
    with pytest.raises(ValidationError, match="itself"):
        Task(
            task_id=identifier,
            agent="orchestrator",
            action=Action.PLAN,
            objective="Plan",
            dependencies=[identifier],
        )


def publication() -> tuple[Task, Approval]:
    task = Task(
        agent="social-publisher",
        action=Action.PUBLISH,
        objective="Publish",
        content="Release draft",
        destination="channel:test",
    )
    approval = Approval(
        task_id=task.task_id,
        workflow_id=task.workflow_id,
        destination=task.destination or "",
        approved_by="human-reviewer",
        content_sha256=hashlib.sha256((task.content or "").encode()).hexdigest(),
    )
    return task, approval


@pytest.mark.parametrize(
    "field,value",
    [
        ("content", "Altered"),
        ("destination", "other"),
        ("task_id", uuid4()),
        ("workflow_id", uuid4()),
    ],
)
def test_approval_is_bound_to_exact_payload(field: str, value: Any) -> None:
    task, approval = publication()
    assert approval_matches(task, approval)
    assert not approval_matches(task.model_copy(update={field: value}), approval)


def test_publication_never_calls_model_even_with_approval() -> None:
    runtime = RecordingRuntime()
    engine = Engine(load_registry(), runtime)
    task, approval = publication()
    assert engine.run(task).status == Status.APPROVAL_REQUIRED
    assert engine.run(task, approval=approval).status == Status.BLOCKED
    assert runtime.tasks == []


def test_workflow_sorts_dag_and_hands_off_artifacts() -> None:
    runtime = RecordingRuntime()
    tasks = plan("Prepare release")
    results = Engine(load_registry(), runtime).workflow(list(reversed(tasks)))
    assert [r.agent for r in results] == [t.agent for t in tasks]
    assert len(runtime.tasks[1].artifacts) == 1
    assert all(r.status == Status.COMPLETED for r in results)


def test_invalid_dag_is_rejected_before_model_calls() -> None:
    runtime = RecordingRuntime()
    engine = Engine(load_registry(), runtime)
    tasks = plan("Prepare release")
    tasks[0].dependencies = [tasks[-1].task_id]
    with pytest.raises(ValueError, match="cycle"):
        engine.workflow(tasks)
    with pytest.raises(ValueError, match="duplicate"):
        engine.workflow([tasks[0], tasks[0]])
    assert runtime.tasks == []


def test_dependency_from_another_workflow_does_not_authorize_run() -> None:
    engine = Engine(load_registry(), OfflineRuntime())
    first, second = plan("Prepare release")[:2]
    result = engine.run(first)
    second.workflow_id = uuid4()
    assert engine.run(second, [result]).status == Status.BLOCKED


def test_failed_runtime_blocks_dependent_tasks() -> None:
    class BrokenRuntime(RecordingRuntime):
        def generate(self, agent: AgentSpec, task: Task) -> Draft:
            raise RuntimeError("private-provider-error")

    results = Engine(load_registry(), BrokenRuntime()).workflow(plan("Prepare release"))
    assert results[0].status == Status.FAILED
    assert "private-provider-error" not in results[0].model_dump_json()
    assert all(r.status == Status.BLOCKED for r in results[1:])


def test_agent_action_allowlist() -> None:
    task = Task(agent="documentation", action=Action.ANALYZE, objective="Wrong action")
    assert Engine(load_registry(), OfflineRuntime()).run(task).status == Status.BLOCKED


def test_cli_offline_run_and_validation(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate"]) == 0
    assert json.loads(capsys.readouterr().out)["agents"] == 5
    assert main(["run", "examples/analyze.json"]) == 0
    assert json.loads(capsys.readouterr().out)["runtime"] == "offline"


def test_cli_invalid_task_has_nonzero_exit(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"unrecognized":true}')
    with pytest.raises(SystemExit) as exc:
        main(["run", str(path)])
    assert exc.value.code == 2


def test_openai_requires_explicit_model() -> None:
    with pytest.raises(ValueError, match="requires"):
        OpenAIRuntime("")
