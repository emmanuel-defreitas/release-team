# Copilot instructions

## Scaffold publication policy (takes precedence over inherited release instructions)

Public releases, package publication, deployments, previews and announcements are
disabled for this scaffold. The inherited release/publish workflow jobs and the
next-lane preview job have unconditional false guards. Tags and repository variables
are not approval. Do not re-enable these jobs, push local work to a public repository,
or announce the project without explicit approval. Existing template automation is
retained for future reviewed adoption; do not run `make tag-release` or bootstrap
remote repository settings as part of local setup.

Feature branches and local checks remain supported. `make ci` verifies the package
and inherited template tests. The added `scaffold-ci.yml` runs read-only checks on
pushes and pull requests without requiring release-app credentials. It publishes
no artifacts. The current remote default is `main`; the template's `dev`/`next`
lanes have not been bootstrapped.


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
