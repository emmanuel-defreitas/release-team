# Release Team

[![CI](https://github.com/emmanuel-defreitas/release-team/actions/workflows/scaffold-ci.yml/badge.svg?branch=main)](https://github.com/emmanuel-defreitas/release-team/actions/workflows/scaffold-ci.yml?query=branch%3Amain)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](pyproject.toml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Release Team has five AI helpers for preparing a software release. They help plan
the work and draft release notes, documentation, and announcements.

This is an early version. It creates drafts and plans. It does not edit your
project, take screenshots, or post announcements. Package publishing is manual and disabled until the first upload is approved.

[Setup](#set-up-your-computer) · [Free demo](#run-the-free-demo) ·
[Workflow](#try-a-five-step-workflow) · [OpenAI](#optional-use-openai) · [Help](#get-help)

## Public distribution

This repository is public so reviewed Agent Skills can be distributed through
[skills.sh](https://skills.sh/). The package workflow only builds and checks by
default. PyPI uploads, GitHub releases and tags, deployments, previews, and
announcements remain manual and require explicit approval. See [Publishing](docs/publishing.md)
for the maintainer workflow.

## Install from PyPI (after the first release)

The workflow is ready for review. This change does **not** publish a package.
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
The check should report `"valid": true`, five agents, and seven skills.

To use this library inside another Python project:

```python
from release_team.contracts import Task

task = Task(
    agent="release-analyst",
    action="analyze",
    objective="Review the supplied changes",
)
```

For OpenAI support, install `"release-team[openai]"` instead. The source tutorials
below use uv and include the example files; a pip install does not download those files.
See [Publishing](docs/publishing.md) for the maintainer setup.

## Set up your computer

Allow 10–15 minutes if the tools below are already installed. First-time tool
downloads may take another 20–30 minutes. You need an internet connection for setup.

### 1. Open Terminal

Terminal is the app where you type commands.

- **macOS:** open Spotlight with Command + Space, type `Terminal`, and press Return.
- **Ubuntu:** press Ctrl + Alt + T.

Paste one command block at a time. Wait until it finishes before starting the next.
Do not copy the surrounding backticks.

### 2. Install the tools for your computer

Choose the instructions for your system. You only need to do this once.

#### macOS

Install [Homebrew](https://brew.sh/) if you do not have it. Follow its installer’s
“Next steps” instructions, then open a new Terminal window.

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

You should see:

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

Open `results.json` in a text editor. It should contain five results, each with
`"status": "completed"` and `"runtime": "offline"`.

To try your own single task, copy `examples/analyze.json` and edit its `objective`
and `evidence`. Evidence is the information you want the helper to use.

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

## Check your work

Run the same checks used by continuous integration (CI), the automatic checks on GitHub:

```sh
make ci
```

The command should finish without an error. It checks the code, runs tests,
and builds local package files. It does not publish them.

If you plan to change the code, see [Contributing](CONTRIBUTING.md) for the
developer setup, including Git hooks that check changes before a commit.

## If something goes wrong

| What you see | What to try |
|---|---|
| `uv: command not found` | Open a new Terminal window after installing uv. Follow the installer’s PATH instructions if it is still missing. |
| `pyproject.toml` or an example file is missing | Enter the `release-team` folder and check that you are on `main`. |
| A tool is missing | Run `make doctor`. Install the tool it names, then retry. |
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
