"""Deterministic routing, dependency checks, and publication boundaries."""

import hashlib
from collections.abc import Sequence

from .contracts import Action, Approval, Result, Status, Task
from .runtime import Runtime
from .specs import Registry


def approval_matches(task: Task, approval: Approval | None) -> bool:
    return bool(
        approval
        and task.action == Action.PUBLISH
        and approval.task_id == task.task_id
        and approval.workflow_id == task.workflow_id
        and approval.destination == task.destination
        and approval.content_sha256 == hashlib.sha256((task.content or "").encode()).hexdigest()
    )


class Engine:
    def __init__(self, registry: Registry, runtime: Runtime) -> None:
        self.registry = registry
        self.runtime = runtime

    def run(
        self, task: Task, prior: Sequence[Result] = (), approval: Approval | None = None
    ) -> Result:
        def result(status: Status, summary: str, errors: list[str] | None = None) -> Result:
            return Result(
                task_id=task.task_id,
                workflow_id=task.workflow_id,
                agent=task.agent,
                status=status,
                summary=summary,
                errors=errors or [],
                runtime=self.runtime.name,
            )

        agent = self.registry.agent(task.agent)
        if task.action not in agent.spec.actions:
            return result(Status.BLOCKED, "Action is not allowed for this agent")
        completed = {
            r.task_id
            for r in prior
            if r.status == Status.COMPLETED and r.workflow_id == task.workflow_id
        }
        if not set(task.dependencies).issubset(completed):
            return result(Status.BLOCKED, "Dependencies have not completed in this workflow")
        if task.action == Action.PUBLISH:
            if not approval_matches(task, approval):
                return result(
                    Status.APPROVAL_REQUIRED,
                    "Explicit approval of exact content and destination required",
                )
            return result(Status.BLOCKED, "Publication adapter is disabled in this scaffold")
        try:
            draft = self.runtime.generate(agent, task)
        except Exception as exc:
            # Avoid leaking provider error text (which can contain request data or credentials).
            return result(Status.FAILED, "Runtime failed", [type(exc).__name__])
        output = result(Status.COMPLETED, draft.summary)
        output.artifacts = draft.artifacts
        output.warnings = draft.warnings
        return output

    def workflow(self, tasks: Sequence[Task]) -> list[Result]:
        """Validate a DAG before any provider call, then execute in stable topological order."""
        pending = {t.task_id: t for t in tasks}
        if len(pending) != len(tasks):
            raise ValueError("duplicate task IDs")
        if len({t.workflow_id for t in tasks}) > 1:
            raise ValueError("workflow IDs must match")
        ordered: list[Task] = []
        while pending:
            ready = [
                t
                for t in pending.values()
                if set(t.dependencies).issubset({x.task_id for x in ordered})
            ]
            if not ready:
                raise ValueError("workflow contains a cycle or missing dependency")
            for task in ready:
                self.registry.agent(task.agent)
                ordered.append(task)
                del pending[task.task_id]
        results: list[Result] = []
        for task in ordered:
            context = task.model_copy(deep=True)
            context.artifacts.extend(
                a for r in results if r.task_id in task.dependencies for a in r.artifacts
            )
            results.append(self.run(context, results))
        return results


def plan(objective: str) -> list[Task]:
    root = Task(agent="orchestrator", action=Action.PLAN, objective=objective)
    tasks = [root]
    for agent, action in [
        ("release-analyst", Action.ANALYZE),
        ("documentation", Action.DRAFT),
        ("media-capture", Action.PLAN),
        ("social-publisher", Action.DRAFT),
    ]:
        tasks.append(
            Task(
                workflow_id=root.workflow_id,
                source="orchestrator",
                agent=agent,
                action=action,
                objective=objective,
                dependencies=[tasks[-1].task_id],
            )
        )
    return tasks
