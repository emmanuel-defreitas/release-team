"""JSON in/out CLI; offline by default and safe to run without credentials."""

import argparse
import json
import os
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from .contracts import Approval, Contract, Result, Status, Task
from .engine import Engine, plan
from .report import render_markdown
from .runtime import OfflineRuntime, OpenAIRuntime, Runtime
from .specs import AgentSpec, Registry, SkillSpec, load_registry

SCHEMAS: dict[str, type[Contract]] = {
    "task": Task,
    "result": Result,
    "approval": Approval,
    "agent": AgentSpec,
    "skill": SkillSpec,
    "registry": Registry,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("agents")
    sub.add_parser("validate")
    schema = sub.add_parser("schema")
    schema.add_argument("kind", choices=SCHEMAS)
    planning = sub.add_parser("plan")
    planning.add_argument("objective")
    planning.add_argument(
        "--evidence", action="append", default=[], help="evidence for every step (repeatable)"
    )
    report = sub.add_parser("report", help="render workflow results as Markdown")
    report.add_argument("file", type=Path)
    report.add_argument("--request", default="", help="the request shown above the drafts")
    report.add_argument("--footer", default="", help="a closing line, such as a run link")
    for name in ("run", "workflow"):
        run = sub.add_parser(name)
        run.add_argument("file", type=Path)
        run.add_argument("--runtime", choices=["offline", "openai"], default="offline")
        run.add_argument("--model", default=os.environ.get("OPENAI_MODEL", ""))
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            print(json.dumps(SCHEMAS[args.kind].model_json_schema(), indent=2))
            return 0
        registry = load_registry(args.registry)
        if args.command == "agents":
            print(json.dumps([a.metadata.id for a in registry.agents]))
            return 0
        if args.command == "validate":
            print(
                json.dumps(
                    {"valid": True, "agents": len(registry.agents), "skills": len(registry.skills)}
                )
            )
            return 0
        if args.command == "plan":
            tasks = plan(args.objective, args.evidence)
            print(TypeAdapter(list[Task]).dump_json(tasks, indent=2).decode())
            return 0
        if args.command == "report":
            results = TypeAdapter(list[Result]).validate_json(args.file.read_text())
            print(render_markdown(results, args.request, args.footer), end="")
            return 0
        runtime: Runtime = (
            OpenAIRuntime(args.model) if args.runtime == "openai" else OfflineRuntime()
        )
        engine = Engine(registry, runtime)
        raw = args.file.read_text()
        if args.command == "run":
            result = engine.run(Task.model_validate_json(raw))
            print(result.model_dump_json(indent=2))
            return 0 if result.status == Status.COMPLETED else 1
        results = engine.workflow(TypeAdapter(list[Task]).validate_json(raw))
        print(TypeAdapter(list[Result]).dump_json(results, indent=2).decode())
        return 0 if all(r.status == Status.COMPLETED for r in results) else 1
    except (ValueError, ValidationError, OSError) as exc:
        parser.exit(2, f"release-team: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
