# Development branch history repair

The original `main` and `dev` branches were initialized independently from two
different generic templates. They had no common ancestor, so a scaffold feature
branch based on `main` could not open a normal pull request into `dev`.

## Preserved roots

- Previous `dev` root: `c02812de6aaedb4f3bc8888145ed980d7d9d1dc0`.
- Canonical `main` root: `c9777f017315b93011e50af8829c98ada88bf1be`.

The repair commit joins both roots, with previous `dev` as its first parent and
canonical `main` as its second parent. The `dev` reference advances normally;
neither root nor any intervening commit is rewritten or deleted.

## Working tree choice

The baseline uses the canonical `main` template, which the tested scaffold was
built on. The independently initialized older template remains available through
the first-parent history, rather than mixing two competing automation systems.
This choice changes the active template files on `dev`; it does not erase them
from Git history.

The baseline also carries the scaffold's release/publish/preview false guards,
the matching actionlint exceptions and policy documentation, and the tested
cross-platform file-permission assertion. No product package or new feature is
merged into `dev` by this repair. The scaffold and beginner README stay in PR #3.

Release, Publish, release-tag and automatic promotion workflows are disabled in
GitHub settings. The repository is public for skills.sh distribution, but releases,
tags, deployments, previews, and public announcements still require explicit approval.

## Remaining lane

`next` still points to an unrelated legacy template. This repair deliberately
does not advance `next`, change the default branch, publish a release, or merge
the scaffold PR. Reconcile `next` separately before enabling promotion again.
