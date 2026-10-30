# Build and publish release-team

## Current state

The repository is private. No package is published by this change.
The new `Package` workflow builds on pull requests and pushes to `main` or `dev`.
A manual run also builds by default. Its upload job stays off while `PUBLISH_PYPI`
is unset or `false`.

Packages uploaded to PyPI are public. Keeping GitHub private does not hide the
package source or README. Review the archive before approving an upload.
The workflow creates no GitHub Release, tag, deployment, or announcement.
The eight inherited release/promotion/publish workflows must remain disabled.

## 1. Check the package locally

Run these commands from the repository folder. They do not upload anything.

```sh
make ci
uv build --out-dir dist
uvx --from twine==7.0.0 twine check --strict dist/*
```

The `dist` folder contains a wheel (`.whl`) and source archive (`.tar.gz`).
The workflow installs that wheel into a fresh Python 3.11 environment and checks
that the CLI, Python imports, and bundled agent/skill files work.

## 2. Connect PyPI to GitHub (one-time owner setup)

Use [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/).
It gives this workflow a short-lived login; no saved PyPI API token is needed.

In PyPI, add a pending publisher for a new project, or a trusted publisher if you
already own the project. Use these exact values:

| Field | Value |
|---|---|
| Project name | `release-team` |
| GitHub owner | `emmanuel-defreitas` |
| Repository | `release-team` |
| Workflow filename | `package.yml` |
| Environment | `pypi` |

Confirm that this name is available or belongs to you. If someone else owns it,
choose an available name in a reviewed metadata change before publishing.
Create the `pypi` environment in GitHub Settings → Environments. Restrict it to
`main` and add a required reviewer if your GitHub plan supports these controls.
The workflow also checks the branch and explicit opt-in itself.

## 3. Prepare a version for review

The scaffold version `0.0.0` cannot be uploaded by this workflow. Prepare the next
version on a branch using the existing tool, then refresh the lockfile:

```sh
bash scripts/version.sh set 0.1.0
uv lock
```

`0.1.0` is an example, not a promised release. Review the changes and package
contents. Merge the approved version into `main` through the repository's PR
process. Keep the old automated release and `next` promotion paths disabled.

## 4. Publish only after explicit owner approval

1. Obtain approval for the exact version and commit. Confirm account billing lets GitHub Actions run.
2. In GitHub Settings → Secrets and variables → Actions → Variables, set `PUBLISH_PYPI` to `true`.
3. Open Actions → Package → Run workflow. Choose `main`, select `publish`, and enter the exact committed version.
4. Review and approve the environment job if prompted. A failed build or version check blocks the upload.
5. Verify the registry page and set `PUBLISH_PYPI` back to `false`.

Do not set this variable or run an upload as part of installing the library.
Do not use the old `publish.yml` workflow. Re-running an upload of an existing
version fails; fix the cause or prepare a new version rather than skipping errors.

## 5. Check installation after publication

Use a new test project or environment. Install the exact version you just approved.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install release-team==0.1.0
release-team validate
```

Use `python -m pip install "release-team[openai]==0.1.0"` for optional OpenAI support.
Replace `0.1.0` with the version that was actually published.

If GitHub says jobs cannot start because of billing, the package has not been
built or uploaded by that run. Local checks can validate the files, but they
do not prove that registry authentication works.
