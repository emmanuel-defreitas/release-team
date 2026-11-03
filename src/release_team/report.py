"""Render workflow results as one Markdown comment for a pull request."""

import re
from collections.abc import Sequence

from .contracts import Result, Status

MARKER = "<!-- release-team-drafts -->"
# GitHub rejects comment bodies over 65,536 characters; leave room for the footer.
MAX_CHARS = 60_000
MAX_COMPONENT_CHARS = 4_000
MAX_SUMMARY_CHARS = 2_000
OMISSION_NOTICE = "_Additional draft content omitted because the comment is too long._"
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


def _clip(text: str, limit: int) -> tuple[str, bool]:
    suffix = "… [truncated]"
    if len(text) <= limit:
        return text, False
    keep = max(0, limit - len(suffix))
    return text[:keep] + suffix, True


def render_markdown(results: Sequence[Result], request: str = "", footer: str = "") -> str:
    done = sum(r.status == Status.COMPLETED for r in results)
    runtimes = sorted({r.runtime for r in results}) or ["none"]
    head = [MARKER, "### Release Team drafts", ""]
    if request.strip():
        request_text, _ = _clip(_cell(request), MAX_COMPONENT_CHARS)
        head += [f"**Request:** {request_text}", ""]
    head += [
        f"**{done} of {len(results)}** helpers finished · runtime `{', '.join(runtimes)}`",
        "",
        "> Drafts only. Nothing was edited, captured or published. Review before using.",
    ]
    if "offline" in runtimes:
        head.append("> Offline runtime: these are placeholder drafts, not AI output.")
    head += ["", "| Helper | Status | Summary |", "|---|---|---|"]
    for r in results:
        summary, _ = _clip(_cell(r.summary), MAX_SUMMARY_CHARS)
        head.append(f"| `{r.agent}` | {_ICONS[r.status]} {r.status} | {summary} |")

    footer_text, _ = _clip(_quiet(footer), MAX_COMPONENT_CHARS)
    tail = ["", "---", footer_text] if footer.strip() else []
    reserved_notice = len("\n\n" + OMISSION_NOTICE)
    budget = MAX_CHARS - len("\n".join(head + tail)) - reserved_notice
    sections: list[str] = []
    for r in results:
        notes = []
        for warning in r.warnings:
            warning_text, _ = _clip(_quiet(warning), MAX_COMPONENT_CHARS)
            notes.append(f"> ⚠️ {warning_text}")
        for error in r.errors:
            error_text, _ = _clip(_cell(error), MAX_COMPONENT_CHARS)
            notes.append(f"> Error: `{error_text}`")
        drafts = []
        for artifact in r.artifacts:
            content, _ = _clip(_quiet(artifact.content), MAX_COMPONENT_CHARS)
            drafts.append((f"{r.agent} · {artifact.name}", content))
        for label, body in drafts or [(r.agent, "_No draft produced._")]:
            summary = f"<details><summary>{_cell(label)}</summary>"
            block = "\n".join(["", summary, "", body, "", *notes, "</details>"])
            if len(block) > budget:
                if budget >= len("\n" + OMISSION_NOTICE):
                    sections.append("\n" + OMISSION_NOTICE)
                budget = 0
                continue
            sections.append(block)
            budget -= len(block)
            notes = []
    body = "\n".join(head + sections + tail) + "\n"
    if len(body) > MAX_CHARS:
        suffix = "\n\n" + OMISSION_NOTICE + "\n"
        body = body[: MAX_CHARS - len(suffix)] + suffix
    return body
