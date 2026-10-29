# Runtime and contract boundaries

The registry in `src/release_team/assets/registry.yaml` is the canonical portable
YAML document. Its API identifier is an internal proposal, not an industry standard.
Agent identity, role, instructions, skills, allowed actions, contracts and permissions
are declarative. Skill declarations distinguish draft generation from planned host
adapters. No YAML tag loads Python code and no adapter name executes a command.

Standalone agent/skill YAML files and six JSON Schemas are exported alongside it.
After changing the registry or Pydantic models, run
`uv run python scripts/export-specs.py`; verify with `--check`. These assets are
included in wheels and source distributions, so the installed CLI works outside
the checkout. A different registry can be passed with `--registry path.yaml`.

`Task` identifies the task, workflow, source, destination agent, action, objective,
evidence, artifacts, dependencies and execution requirements. `Result` carries
the same identity plus status, artifacts, errors, warnings and runtime trace.
Unknown fields are rejected. The engine validates the entire dependency DAG before
execution and passes direct predecessor artifacts into dependent tasks. A failed
prerequisite blocks its descendants. The scaffold is sequential and in-memory;
there is no durable queue, retry scheduler, database or distributed worker yet.

Each agent runs independently through the same engine. The orchestrator plan command
builds a five-task draft workflow; it does not let a model execute arbitrary handoffs.
Allowed actions are enforced before invoking a runtime. `completed` means the
requested **draft or plan** was generated, not that an application was changed.
Task requirements are host-facing metadata; they do not provision environments.

The Python `Runtime` protocol has a `name` and `generate(agent, task) -> Draft`.
To add another provider, implement it and supply it to `Engine`. The portable
specs and contracts do not change. The CLI currently selects `offline` or `openai`.
Offline output is a marked placeholder for testing the plumbing. OpenAI is the
first live provider, using the Responses API and a small Pydantic structured-output
schema. It receives no tools, filesystem handles or publication credentials.
Task identity and status are assigned by the engine, never the model.

OpenAI uses an explicit model, a 60-second request timeout, no automatic retries,
an output-token bound and `store=False`. Refusals, incomplete responses and API
failures become failed results; raw provider error text is not emitted. Inputs
are sent to the selected provider only when `--runtime openai` is requested.
Normal CI uses mocked SDK responses and makes no paid model calls.

The implementation follows the official [OpenAI structured output guide](https://developers.openai.com/api/docs/guides/structured-outputs).

## Publication

A publish task must contain exact content and destination. A trusted host can
provide an `Approval` bound to task ID, workflow ID, destination and SHA-256 of
the exact UTF-8 content. The CLI has no approval-creation command. Approval records
are not cryptographic credentials; the host must authenticate reviewers and protect
record storage before a real publisher can be enabled. Models never supply them.

Without a matching record, the engine returns `approval_required`. Even with a
matching record, it returns `blocked`: all publication adapters are disabled.
The scaffold therefore cannot publish through model instructions or task parameters.
GitHub release, package publication, deployment and preview jobs inherited from the
template are also disabled unconditionally. Re-enabling requires a separately
reviewed change and explicit approval. This does not change repository visibility.

## GPUI integration

The sibling `gpui-automation` repository owns a Rust contract core. It offers
validated IDs, snapshots, interactions, scenarios and a runner. A future local
host adapter can expose that bridge to a media worker. The current Python media
agent produces a capture plan only. No Rust subprocess, graphical app, screenshot
or video encoder is connected yet. The existing GPUI application remains untouched.
