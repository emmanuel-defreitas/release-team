# Copilot instructions

## Package publishing (current policy)

The reviewed package workflow is `.github/workflows/package.yml`. PRs and pushes
build and check packages without publishing them. Publication is manual-only,
from `main`, with `publish=true`, an exact non-placeholder version, and repository
variable `PUBLISH_PYPI=true`. Leave that variable unset or false until the owner
explicitly approves a public package upload. Never dispatch publication on the
owner's behalf without that approval.

The repository is public to support distribution of the reviewed agent skills.
Registry packages are public, including their bundled source files. GitHub Releases,
tags, previews, promotion and announcements remain disabled. Keep all inherited
workflows and their false guards disabled; do not use `publish.yml`. See
`docs/publishing.md` for setup and first-publication steps.

## Scaffold publication policy (takes precedence over inherited release instructions)

Public releases, deployments, previews and announcements are disabled. Package
publication follows the manual approval policy above. The inherited release/publish workflow jobs and the
next-lane preview job have unconditional false guards. Tags and repository variables
are not approval. Do not re-enable these jobs, create releases or tags, deploy
previews, or announce the project without explicit approval. Existing template
automation is retained for future reviewed adoption; do not run `make tag-release` or bootstrap
remote repository settings as part of local setup.

Feature branches and local checks remain supported. `make ci` verifies the package
and inherited template tests. The added `scaffold-ci.yml` runs read-only checks on
pushes and pull requests without requiring release-app credentials. It publishes
no artifacts. The remote default is `main`. The repaired `dev` lane now shares
the canonical `main` history; its previous template remains in the merge history.
`next` still has a separate legacy history and must not be promoted until reconciled.
Release, publishing, tag creation, and automatic promotion workflows are disabled
in GitHub settings. Scaffold feature PRs target `dev`.

See [the branch-history record](../docs/branch-history.md) for the repair details.


Full rules are in [`AGENTS.md`](../AGENTS.md); this is the short form. This repository is a **generic
template** for Rust + GPUI, Python, TypeScript, React, Expo, SwiftUI and AI-agent projects.

## Commands (run from the repository root)

| Task                           | Command                                                        |
| ------------------------------ | -------------------------------------------------------------- |
| Check tools / first-time setup | `make doctor` / `make setup`                                   |
| Format and autofix             | `make fmt`                                                     |
| Lint, types, tests, build      | `make lint-check`, `make typecheck`, `make test`, `make build` |
| End-to-end tests               | `make e2e`                                                     |
| Everything CI runs on a PR     | `make ci`                                                      |
| Test the repo's own automation | `make selftest`                                                |
| Validate skills / instructions | `make agents-check`                                            |
| Scan for secrets               | `make secrets-scan`                                            |

Targets detect the stack from `pyproject.toml`, `package.json`, `Cargo.toml` or `Package.swift` /
`.xcodeproj` (`scripts/stack.sh`). Override any task with `<TASK>_CMD`, e.g. `make test TEST_CMD="..."`.
`copilot-setup-steps.yml` prepares the same toolchains for the coding agent.

## Conventions

- **Branches:** `<type>/<slug>` with type `feat|fix|chore|docs|ci|refactor|test|perf|build|style|revert|ai`,
  opened as PRs into `dev` (the default branch). Promotion: `dev` -> `next` -> `release/vX.Y.Z` -> `main`.
- **PR titles:** Conventional Commits, `feat(scope)!: summary`. They set the SemVer bump (`!` major,
  `feat` minor, else patch). Do not edit versions, tags or `CHANGELOG.md` by hand.
- **Workflows:** `.github/workflows/*.yml` are plain workflows; steps call `make` targets. Pin third-party
  actions to a commit SHA with a version comment. Keep jobs least-privilege.
  `release-team.yml` is a manual button that runs the agents and posts drafts as a PR comment; it never
  publishes, and only its `comment` job (which has no OpenAI key) may write to PRs.
- **Release Team runner:** `make release-team-drafts OBJECTIVE="..."` runs draft-only agents locally;
  it uses offline mode unless OpenAI settings are explicitly present and writes only ignored output.
- **Docs move with automation:** update `AGENTS.md`, `README.md`, and `.github/WORKFLOW.md` in the same PR.
- **Template stays generic:** stack specifics go behind `scripts/stack.sh` or `.github/skills/`.
- **Skills:** `.github/skills/<name>/SKILL.md`, frontmatter `name` equal to the directory and a one-line
  `description`. `make agents-check` enforces it.

## Secrets

- Never commit credentials, tokens or keys, including in tests, fixtures, docs and examples.
- Real values belong in `.env` (gitignored); commit `.env.example` with `REPLACE_ME` placeholders.
- `gitleaks` runs as a pre-commit hook and as the required `Secret Scan` workflow. Never use
  `--no-verify`; if it fires, remove the secret and rotate it.
- Do not commit `.claude/`, `.agents/`, `.codex/`, `.worktrees/` or workflow logs.
