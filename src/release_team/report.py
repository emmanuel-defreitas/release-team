"""Render workflow results as one Markdown comment for a pull request."""

import re
from collections.abc import Sequence

from .contracts import Result, Status

MARKER = "<!-- release-team-drafts -->"
# GitHub rejects comment bodies over 65,536 characters; leave room for the footer.
MAX_CHARS = 60_000
_MENTION = re.compile(r"@(?=[A-Za-z0-9])")
_ICONS = {
    Status.COMPLETED: "✅",
    Status.BLOCKED: "⛔",
    Status.FAILED: "❌",
    Status.APPROVAL_REQUIRED: "✋",
}


def _quiet(text: str) -> str:
    """Stop drafts from pinging people or teams: `@name` becomes `@​name`."""
    return _MENTION.sub("@​", text)


def _cell(text: str) -> str:
    return _quiet(" ".join(text.split())).replace("|", "\\|")


def render_markdown(results: Sequence[Result], request: str = "", footer: str = "") -> str:
    done = sum(r.status == Status.COMPLETED for r in results)
    runtimes = sorted({r.runtime for r in results}) or ["none"]
    head = [MARKER, "### Release Team drafts", ""]
    if request.strip():
        head += [f"**Request:** {_cell(request)}", ""]
    head += [
        f"**{done} of {len(results)}** helpers finished · runtime `{', '.join(runtimes)}`",
        "",
        "> Drafts only. Nothing was edited, captured or published. Review before using.",
    ]
    if "offline" in runtimes:
        head.append("> Offline runtime: these are placeholder drafts, not AI output.")
    head += ["", "| Helper | Status | Summary |", "|---|---|---|"]
    for r in results:
        head.append(f"| `{r.agent}` | {_ICONS[r.status]} {r.status} | {_cell(r.summary)} |")

    tail = ["", "---", _quiet(footer)] if footer.strip() else []
    budget = MAX_CHARS - len("\n".join(head + tail))
    sections: list[str] = []
    for r in results:
        notes = [f"> ⚠️ {_quiet(w)}" for w in r.warnings]
        notes += [f"> Error: `{_cell(e)}`" for e in r.errors]
        drafts = [(f"{r.agent} · {a.name}", _quiet(a.content)) for a in r.artifacts]
        for label, body in drafts or [(r.agent, "_No draft produced._")]:
            summary = f"<details><summary>{_cell(label)}</summary>"
            block = "\n".join(["", summary, "", body, "", *notes, "</details>"])
            if len(block) > budget:
                sections.append(f"\n_{_cell(label)}: omitted because the comment is too long._")
                budget = 0
                continue
            sections.append(block)
            budget -= len(block)
            notes = []
    return "\n".join(head + sections + tail) + "\n"
