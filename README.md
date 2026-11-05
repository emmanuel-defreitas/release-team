# Release Team

[![CI](https://github.com/emmanuel-defreitas/release-team/actions/workflows/scaffold-ci.yml/badge.svg?branch=main)](https://github.com/emmanuel-defreitas/release-team/actions/workflows/scaffold-ci.yml?query=branch%3Amain)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](pyproject.toml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Release Team has five AI helpers for preparing a software release. They help plan
the work and draft release notes, documentation, and announcements.

This is an early version. It creates drafts and plans. It does not edit your
project, take screenshots, or post announcements. Package publishing is manual. The first upload needs owner approval.

[Getting started](#getting-started) · [Free demo](#run-the-free-demo) ·
[Workflow](#try-a-five-step-workflow) · [OpenAI](#optional-use-openai) ·
[GitHub](#run-the-team-on-github) · [Codex plugin](#codex-plugin) · [Help](#get-help)

## Key features

- Five agents prepare release plans, analysis, documentation, media plans, and announcement drafts.
- A portable YAML registry defines agents, skills, actions, contracts, and permissions.
- Strict task and result contracts reject unknown fields.
- A workflow passes artifacts between tasks and blocks tasks when prerequisites fail.
- Offline mode produces test drafts. Optional OpenAI support produces model-generated drafts.

## Technology stack

The current package uses Python. The inherited automation also supports other stacks when their manifests exist.

| Component | Technology | Purpose |
|---|---|---|
| Runtime | Python 3.11+ | CLI and workflow engine |
| Contracts | Pydantic 2.10 to below 3 | Task, result, and approval validation |
| Registry | PyYAML 6 to below 7 | Portable YAML definitions |
| Optional provider | OpenAI Python SDK 2 to below 3 | Draft generation |
| Development | uv, pytest, Ruff, mypy, Hatchling | Dependencies, tests, linting, types, and packaging |

[pyproject.toml](pyproject.toml) defines dependency ranges. [uv.lock](uv.lock) records resolved versions.

## Project architecture

The CLI loads task data and registry definitions. The engine validates actions and dependencies before it calls a runtime.

```text
CLI + YAML registry + task data
              |
              v
     Engine and contracts
              |
              v
     Offline or OpenAI runtime
              |
              v
     Results and draft artifacts
```

The engine assigns task identity and status. It passes artifacts from direct predecessors to dependent tasks.
Execution is sequential and uses memory. There is no durable queue, retry scheduler, database, or distributed worker.

OpenAI receives no tools, filesystem handles, or publication credentials.
A publish task needs approval for its exact content and destination.
The engine returns `approval_required` without matching approval. It returns `blocked` even with approval because publication adapters are disabled.

The [architecture guide](docs/architecture.md) describes contracts, runtime boundaries, approval records, and provider extensions.

## Project structure

| Path | Contents |
|---|---|
| [src/release_team/](src/release_team/) | CLI, contracts, engine, runtimes, and registry loading |
| [src/release_team/assets/](src/release_team/assets/) | Canonical registry, exported agent and skill definitions, and six JSON Schemas |
| [examples/](examples/) | Task inputs for local trials |
| [tests/](tests/) | Package tests and inherited automation tests |
| [scripts/](scripts/) and [makefile](makefile) | Stack detection, local commands, and specification exports |
| [.github/](.github/) | Workflows, rulesets, and agent skills |
| [docs/](docs/) | Architecture, publishing policy, and branch history |

## Public distribution

This repository is public so reviewed Agent Skills can be distributed through
[skills.sh](https://skills.sh/). The package workflow only builds and checks by
default. PyPI uploads need explicit owner approval. GitHub releases, tags, deployments, previews, promotion, and announcements remain disabled. See [Publishing](docs/publishing.md)
for the maintainer workflow.

An approved package upload uses `.github/workflows/package.yml` from `main`.
It needs `publish=true`, an exact non-placeholder version, and `PUBLISH_PYPI=true`.
Keep that variable unset or false until the owner approves the upload. Do not use the inherited `publish.yml`.

## Codex plugin

The repository also contains a skills-only Codex plugin at
[`plugins/release-team-actions/`](plugins/release-team-actions/). It bundles the
Release Team Actions skill, the reviewed workflow template, and the mention-safe
comment renderer. It does not include an MCP server, credentials, or the
`release-team` Python package.

Before installing the bundled workflow in another repository, verify that the
target provides Python 3.11+, `uv`, `jq`, `gh`, and `bash`; a locked `uv.lock`
that makes `uv run --locked release-team` available; and a compatible
`.github/actions/setup` action. That action may depend on the target repository's
`scripts/stack.sh` and `scripts/lib.sh`. Copying only the workflow and comment
script is not sufficient when those prerequisites are absent. See the plugin's
[`SKILL.md`](plugins/release-team-actions/skills/release-team-actions/SKILL.md)
for the complete installation checklist.

## Install from PyPI (after the first release)

The package workflow builds and checks packages by default. It does **not** publish a package automatically.
Until the owner announces an approved version here, use the source setup below.
Do not install an unverified package that happens to use this name.

After an approved version is available, open Terminal and run:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install release-team
release-team validate
```

You need Python 3.11 or newer. On Windows, activate with `.venv\Scripts\activate`.
The output reports `"valid": true`, five agents, and seven skills.

To use this library inside another Python project:

```python
from release_team.contracts import Task

task = Task(
    agent="release-analyst",
    action="analyze",
    objective="Review the supplied changes",
)
```

For OpenAI support, install `"release-team[openai]"` instead. The source tutorials below use uv and include the example files. A pip install does not download those files.
See [Publishing](docs/publishing.md) for the maintainer setup.

## Getting started

Allow 10–15 minutes if the tools below are already installed. First-time tool
downloads may take another 20–30 minutes. You need an internet connection for setup.

### 1. Open Terminal

Terminal is the app where you type commands.

- **macOS:** open Spotlight with Command + Space. Type `Terminal`. Press Return.
- **Ubuntu:** press Ctrl + Alt + T.

Paste one command block at a time. Wait until it finishes before starting the next.
Do not copy the surrounding backticks.

### 2. Install the tools for your computer

Choose the instructions for your system. You only need to do this once.

#### macOS

Install [Homebrew](https://brew.sh/) if you do not have it. Complete its installer’s
“Next steps” instructions. Open a new Terminal window.

Install Git, jq, and uv:

```sh
brew install git jq uv
```

Git downloads the project. jq helps check data. uv installs Python and the
project’s Python packages. Apple’s command-line tools also provide `make`.
If an Apple tools installer appears, finish it before continuing.

#### Ubuntu

Install the basic tools:

```sh
sudo apt-get update
sudo apt-get install -y git make jq curl ca-certificates
```

Install uv using its [official installer](https://docs.astral.sh/uv/getting-started/installation/):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open a new Terminal window so it can find uv.

#### Check that the tools are ready

```sh
git --version
make --version
jq --version
uv --version
```

Each command should print a version number. You do not need to install Python
separately: uv downloads the Python version recorded by this project when needed.

### 3. Download Release Team

```sh
git clone --branch main https://github.com/emmanuel-defreitas/release-team.git
cd release-team
```

The `main` branch contains the reviewed library.
Run the remaining commands inside the `release-team` folder.

### 4. Install the project’s packages

```sh
uv sync --locked
```

`--locked` uses the package versions saved with the project. uv creates a local
`.venv` folder for them. You do not need to activate that folder yourself.

Check the setup:

```sh
uv run --locked release-team validate
```

The command prints:

```json
{"valid": true, "agents": 5, "skills": 7}
```

Your setup is ready when `valid` is `true`.

## Run the free demo

No API key or paid AI account is needed for this demo.

### 1. List the helpers

```sh
uv run --locked release-team agents
```

| Helper | What it prepares |
|---|---|
| `orchestrator` | A plan for the release work |
| `release-analyst` | A draft review of the supplied changes |
| `documentation` | A documentation draft |
| `media-capture` | A plan for screenshots or videos |
| `social-publisher` | An announcement draft for review |

### 2. Run the example task

```sh
uv run --locked release-team run examples/analyze.json
```

The result is JSON: text with named fields. Look for `"status": "completed"`
and `"runtime": "offline"`.

Offline mode returns placeholder drafts so you can try the steps. It does not
use an AI model or inspect a Git repository. Here, `completed` means the demo
draft was produced, not that a real release was prepared.

## Try a five-step workflow

A workflow passes work from one helper to the next.

### 1. Save a plan

```sh
uv run --locked release-team plan "Prepare a demo release" > workflow.json
```

This creates `workflow.json` in the current folder. Change the words inside
the quotes to change the goal.

### 2. Run the plan and save the results

```sh
uv run --locked release-team workflow workflow.json > results.json
```

Open `results.json` in a text editor. It contains five results, each with
`"status": "completed"` and `"runtime": "offline"`.

To try your own single task, copy `examples/analyze.json`. Edit its `objective` and `evidence`. Evidence is the information you want the helper to use.

## Optional: use OpenAI

This option sends the task text, supplied evidence, and task artifacts to OpenAI.
API calls can cost money. You need an OpenAI API key and a model your account can use.

### 1. Enable the OpenAI option

```sh
uv sync --locked --extra openai
```

### 2. Create your settings file

```sh
make env-init
```

This creates `.env` if it does not already exist. Open `.env` in a text editor.
Replace the `REPLACE_ME` values on these two lines:

```dotenv
OPENAI_API_KEY=REPLACE_ME
OPENAI_MODEL=REPLACE_ME
```

Use your own API key and an available model ID. Leave the other settings alone;
this tool does not need them. Keep `.env` private. Git is set to ignore it.

### 3. Ask OpenAI for a draft

```sh
uv run --locked --env-file .env release-team run examples/analyze.json --runtime openai
```

`--env-file .env` loads your settings. Without that flag, putting values in `.env`
alone does not load them for this command.

A successful result has `"status": "completed"` and `"runtime": "openai"`.
Read the draft before using it. This option still cannot publish or change your project.

## Run local Release Team drafts

Run `make release-team-drafts OBJECTIVE="Draft notes"` to produce the same five-agent
draft workflow locally. It uses offline mode unless both `OPENAI_API_KEY` and
`OPENAI_MODEL` are set, and writes `plan.json`, `workflow.json`, `results.json`, and
`summary.md` under the ignored `release-team-out/` directory. The runner never posts,
publishes, tags, releases, or deploys.

## Run the team on GitHub

You can also run the five helpers on GitHub, without installing anything, and get
their drafts as a comment on a pull request (PR).

Prerequisite: the repository must contain `.github/workflows/release-team.yml` and
`scripts/release-team-comment.sh`. In a generated repository, copy both from
`.github/skills/release-team-actions/assets/` as documented in that skill before
using the button.

### 1. Press the button

1. Open the repository on GitHub and select the **Actions** tab.
2. Select **Release Team** in the list on the left.
3. Select **Run workflow**, fill in the boxes below, and press the green **Run workflow** button.

| Box | What to enter |
|---|---|
| **objective** | What the team should prepare, for example `Draft notes for v0.2.0`. |
| **pr_number** | The number of the PR to read and comment on, for example `42`. Leave it blank to see the drafts only on the run's page. |
| **runtime** | Leave it on `auto`. `offline` always gives free placeholder drafts. `openai` uses OpenAI and fails if it is not set up. |

The button appears only once `.github/workflows/release-team.yml` is on the
default branch (`main`). Until then the **Release Team** entry is missing.

### 2. Read the drafts

After a minute or two, the drafts appear in two places:

- **On the PR:** one comment titled "Release Team drafts", with a table of the five
  helpers and a section you can expand for each draft. Running it again updates
  the same comment instead of adding a new one.
- **On the run's page:** under **Summary**, even when you left the PR number blank.

If a helper fails, the comment still appears and shows the error, and the run is marked red.
The workflow only reads the repository and writes that comment. It never releases,
tags, pushes, or publishes anything.

### 3. Optional: use OpenAI on GitHub

On `auto`, the workflow gives free offline placeholder drafts until a repository
owner adds both settings below. Run these yourself in Terminal, inside the
`release-team` folder. The first command asks you to paste the key, so it never
appears on screen or in your command history.

```sh
gh secret set OPENAI_API_KEY
gh variable set OPENAI_MODEL --body "REPLACE_ME"
```

Replace `REPLACE_ME` with a model ID your account can use. After that, each run on
`auto` sends the objective and the PR's title, description, commit titles, and
changed file names to OpenAI. API calls can cost money.

## Development workflow

The current repository policy names `main` as the default branch. Feature pull requests target `dev`.
The repaired `dev` branch shares the canonical `main` history. The `next` branch still has separate legacy history.
Do not promote `next` before reconciliation. See the [branch-history record](docs/branch-history.md).

1. Create a `<type>/<slug>` branch from `dev`, such as `docs/readme-update`.
2. Run `make doctor` to identify missing tools.
3. Run `make setup` once per clone.
4. Make the change.
5. Run `make fmt`, then `make ci`, before opening a pull request into `dev`.

`make setup` installs dependencies, Git hooks, a commit template, and local skill links. It also creates `.env` when absent.
Use a Conventional Commit title, such as `docs: clarify setup`.
The current publication policy overrides inherited instructions about automatic promotion and releases.
See [AGENTS.md](AGENTS.md) and the [operations guide](.github/WORKFLOW.md) for that policy.

## Coding standards

- Match existing names and patterns. Keep changes focused on the task.
- Use Ruff for Python formatting and linting. The configured line length is 100 characters.
- Use strict mypy validation for `src` and `tests`.
- Keep credentials in the ignored `.env` file. Use `REPLACE_ME` placeholders in `.env.example`.
- Never bypass Git hooks. Do not edit version numbers, generated changelog sections, or tags by hand.

Keep template automation generic. Put stack behavior in `scripts/stack.sh` or an agent skill.
Update the policy documentation with changes to automation or conventions, as specified in [AGENTS.md](AGENTS.md).

## Testing

Run the full local validation:

```sh
make fmt
make ci
```

`make ci` installs dependencies, tests template scripts, validates agent assets, runs linting and type validation, runs tests, and builds packages.
It does not publish packages. Normal CI mocks OpenAI responses and makes no paid model calls.

| Command | Purpose |
|---|---|
| `make test` | Run Python tests with pytest |
| `make selftest` | Test inherited automation scripts |
| `make agents-check` | Validate agent instructions and skill metadata |
| `make lint-check` | Verify formatting and lint rules |
| `make typecheck` | Validate Python types |

After changing the registry or Pydantic models, regenerate the exported specifications:

```sh
uv run python scripts/export-specs.py
```

Verify the exports:

```sh
uv run python scripts/export-specs.py --check
```

## Contributing

Read [Contributing](CONTRIBUTING.md) for setup, commit conventions, and pull request guidance.
Apply the current publication policy above when inherited release instructions conflict.
Use [examples/analyze.json](examples/analyze.json) as a task example.
Consult [.github/copilot-instructions.md](.github/copilot-instructions.md) for the short agent guide.

Run `make ci` before submitting changes. Include relevant tests when behavior changes.
Report vulnerabilities through [SECURITY.md](SECURITY.md).
Participation follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## If something goes wrong

| What you see | What to try |
|---|---|
| `uv: command not found` | Open a new Terminal window after installing uv. Use the installer’s PATH instructions if it is still missing. |
| `pyproject.toml` or an example file is missing | Enter the `release-team` folder. Check that you are on `main`. |
| A tool is missing | Run `make doctor`. Install the tool it names. Retry the command. |
| OpenAI reports `Runtime failed` | Check the two settings in `.env`, your model access, and the `--env-file .env` flag. Do not paste your API key into an issue. |
| A task is `blocked` or `approval_required` | Read its `summary`. Earlier tasks must finish first; publication is intentionally disabled. |

## Get help

Read [How it works](docs/architecture.md) for the task format, approval rules,
and instructions for adding another AI provider. The agent and skill definitions
live in [the assets folder](src/release_team/assets/).

The separate [GPUI Automation](https://github.com/emmanuel-defreitas/gpui-automation/tree/feat/initial-automation-scaffold)
library is the planned connection to desktop apps. The two projects are not connected yet.

Found a problem? [Open an issue](https://github.com/emmanuel-defreitas/release-team/issues).
Include the command you ran and the error message. Remove keys and private information first.

## License

Release Team uses the [MIT license](LICENSE).
