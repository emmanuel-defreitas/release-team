---
name: release-team-actions
description: Wire the five-agent Release Team (release-team CLI) into GitHub Actions - a manual Run workflow button that plans, runs the agents offline or with OpenAI opt-in, and posts the drafts as a PR comment. Use whenever someone wants the release team, release agents or release-notes drafts to run in CI, Actions, a workflow, on a PR, or on a button, even if they never say "workflow".
---

# Release Team in GitHub Actions

**When to use:** adding, changing or debugging the workflow that runs the `release-team` agents
(orchestrator, release-analyst, documentation, media-capture, social-publisher) on GitHub.

The team only writes drafts. The workflow you add must keep it that way: it reads the repo,
runs the agents and posts a comment. It never releases, tags, pushes or publishes anything,
and it does not touch the disabled jobs in `release.yml`, `publish.yml` or `next.yml`.

## What to build

Start from the reviewed templates bundled with this plugin instead of writing a workflow from
scratch. Every line in them answers a security or reliability problem that is easy to miss.

The plugin bundles these files under `assets/`:

- `assets/release-team.yml` -> `.github/workflows/release-team.yml`
- `assets/release-team-comment.sh` -> `scripts/release-team-comment.sh`

Copy those bundled files into the target repository, then make the comment script executable.

What the template does, so you can adapt it without breaking it:

| Part | Why |
| --- | --- |
| `workflow_dispatch` with `objective`, `pr_number`, `runtime` inputs | A manual button. A blank PR number writes to the run summary only. |
| Runtime `auto` | OpenAI only when the `OPENAI_API_KEY` secret **and** `OPENAI_MODEL` variable exist; otherwise offline, so the workflow never fails for lack of a key. |
| `plan` then `jq` injects evidence, then `workflow` | `release-team plan` leaves evidence empty. The PR title, description, commits and file list give the agents something real to work from. |
| Two jobs: `draft` (read-only, holds the OpenAI key) and `comment` (`pull-requests: write`, no key) | Least privilege: the job that sees model output and the API key cannot write; the writer never sees the key. |
| Inputs passed through `env:` and checked (`^[1-9][0-9]*$`) | `${{ inputs.* }}` inside `run:` is script injection. |
| `scripts/release-team-comment.sh` | Renders results as a table plus collapsible drafts, breaks up `@mentions` from model text, caps size under GitHub's 65,536-char limit. |
| Hidden marker `<!-- release-team-drafts -->` | Re-runs update one comment instead of stacking new ones. |
| Comment job runs `if: !cancelled()` and `draft` fails last | A failed task still shows up on the PR, and the run is still red. |
| Actions pinned to full SHAs with a version comment | Matches the rest of `.github/workflows/`. Reuse the pins already in the repo. |

## Adapting it

- **Other triggers** (only if asked): add `pull_request` (never `pull_request_target`, which runs
  with write access on untrusted fork code). Fork PRs get no secrets and a read-only token, so
  skip the comment job for them: `github.event.pull_request.head.repo.full_name == github.repository`.
  Default the objective and PR number from the event (`inputs.objective || github.event.pull_request.title`).
  Every PR run with OpenAI costs money; say so.
- **Different evidence:** edit the `jq` list in "Collect PR evidence". Keep each item short;
  everything in it is sent to OpenAI when that runtime is on.
- **No PR comment wanted:** delete the `comment` job; the run summary still shows the drafts.

## Wiring up OpenAI (user does this)

The workflow runs offline until both values exist. Give the user these commands to run themselves.
Never ask them to paste the key into chat, and never set it for them.

```sh
gh secret set OPENAI_API_KEY          # prompts for the value; nothing lands in shell history
gh variable set OPENAI_MODEL --body "<a model id your account can use>"
```

## Verify before you hand it over

```sh
actionlint .github/workflows/release-team.yml
uv run --locked release-team plan "Draft notes" > /tmp/wf.json
uv run --locked release-team workflow /tmp/wf.json > /tmp/results.json
bash scripts/release-team-comment.sh /tmp/results.json | head -20
make agents-check && make ci
```

## Change docs in the same PR

Rule 6 in `AGENTS.md`: workflows and docs move together. Update:

- `README.md`: a short beginner section, "Run the team on GitHub": where the Run workflow button
  is, what each input means, where the drafts appear, and that OpenAI is optional and billed.
- `.github/WORKFLOW.md` and the workflow list in the `AGENTS.md` repository map.
- `.github/copilot-instructions.md` if it lists workflows.

Then propose a branch such as `ci/release-team-workflow`, PR into `dev`, title
`ci(workflows): run the release team from a manual workflow`. Do not push or open the PR
without the user's go-ahead.

## Pitfalls

- The Run workflow button only appears once the file is on the default branch (`main` here).
  Until it is promoted, nobody can click it, even though the PR into `dev` is green.
- Hosted Actions may be blocked on this account. A run that never starts is an account or
  billing problem, not a workflow bug.
- `release-team workflow` exits 1 when any task is not `completed` and 2 on bad input
  (empty `results.json`). The template keeps going so the comment can explain it.
- Do not loosen the top-level `permissions: contents: read` or move `pull-requests: write`
  into the job that has the OpenAI key.
- Do not use repository variables or tags to flip publication on. That needs a separately
  reviewed change and explicit approval (see `docs/architecture.md`, "Publication").
