import json
from pathlib import Path
from uuid import uuid4

import pytest

from release_team.cli import main
from release_team.contracts import Artifact, Result, Status
from release_team.engine import Engine, plan
from release_team.report import MARKER, MAX_CHARS, render_markdown
from release_team.runtime import OfflineRuntime
from release_team.specs import load_registry


def offline_results(objective: str = "Prepare release") -> list[Result]:
    return Engine(load_registry(), OfflineRuntime()).workflow(plan(objective))


def test_report_lists_every_helper_and_draft() -> None:
    body = render_markdown(offline_results(), "Notes for #12", "Run link")
    assert body.startswith(MARKER)
    assert "**Request:** Notes for #12" in body
    assert "**5 of 5** helpers finished" in body
    assert "placeholder drafts" in body
    for agent in ("orchestrator", "release-analyst", "documentation", "media-capture"):
        assert f"| `{agent}` | ✅ completed |" in body
        assert f"<summary>{agent} · {agent}.md</summary>" in body
    assert body.count("<details>") == body.count("</details>") == 5
    assert body.rstrip().endswith("Run link")


def test_report_cannot_ping_people_or_break_the_table() -> None:
    result = Result(
        task_id=uuid4(),
        workflow_id=uuid4(),
        agent="social-publisher",
        status=Status.FAILED,
        summary="Ping @octocat | and @org/team",
        artifacts=[Artifact(name="post.md", content="cc @maintainers")],
        errors=["RuntimeError"],
        runtime="openai",
    )
    body = render_markdown([result], "ask @someone")
    assert "@octocat" not in body and "@maintainers" not in body and "@someone" not in body
    assert "@​octocat \\| and @​org/team" in body
    assert "❌ failed" in body and "Error: `RuntimeError`" in body
    assert "placeholder" not in body


def test_report_stays_under_the_github_comment_limit() -> None:
    results = offline_results()
    for r in results:
        r.artifacts = [Artifact(name="huge.md", content="x" * 30_000)]
    body = render_markdown(results, footer="Run link")
    assert len(body) <= MAX_CHARS
    assert body.count("… [truncated]") == 5
    assert body.rstrip().endswith("Run link")


def test_report_limits_large_header_components() -> None:
    result = offline_results()[0]
    result.summary = "s" * 70_000
    body = render_markdown([result], request="r" * 70_000, footer="f" * 70_000)
    assert len(body) <= MAX_CHARS
    assert "… [truncated]" in body or "Additional draft content omitted" in body


def test_plan_passes_evidence_to_every_step() -> None:
    tasks = plan("Prepare release", ["PR #3: add login", "Changed files:\n- app.py"])
    assert all(t.evidence == ["PR #3: add login", "Changed files:\n- app.py"] for t in tasks)


def test_cli_plan_workflow_and_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["plan", "--evidence", "PR #3", "--", "-leading dash request"]) == 0
    tasks = json.loads(capsys.readouterr().out)
    assert tasks[0]["objective"] == "-leading dash request"
    assert tasks[-1]["evidence"] == ["PR #3"]
    workflow = tmp_path / "workflow.json"
    workflow.write_text(json.dumps(tasks))
    assert main(["workflow", str(workflow)]) == 0
    results = tmp_path / "results.json"
    results.write_text(capsys.readouterr().out)
    assert main(["report", str(results), "--request=-leading dash request"]) == 0
    out = capsys.readouterr().out
    assert out.startswith(MARKER) and "**5 of 5**" in out
