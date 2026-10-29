from types import SimpleNamespace
from typing import Any

import pytest

from release_team.engine import Engine, plan
from release_team.runtime import OpenAIResponse, OpenAIRuntime
from release_team.specs import load_registry


@pytest.mark.parametrize(
    "status,parsed,expected",
    [
        (
            "completed",
            OpenAIResponse(summary="Draft", content="Verified draft", warnings=[]),
            "completed",
        ),
        ("incomplete", None, "failed"),
        ("completed", None, "failed"),
    ],
)
def test_openai_structured_output_without_network(
    monkeypatch: pytest.MonkeyPatch, status: str, parsed: OpenAIResponse | None, expected: str
) -> None:
    openai = pytest.importorskip("openai")
    calls: list[dict[str, Any]] = []

    class FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            assert kwargs == {"timeout": 60.0, "max_retries": 0}
            self.responses = self

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: Any) -> None:
            pass

        def parse(self, **kwargs: Any) -> SimpleNamespace:
            calls.append(kwargs)
            return SimpleNamespace(status=status, output_parsed=parsed)

    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    task = plan("Prepare release")[0]
    result = Engine(load_registry(), OpenAIRuntime("test-model")).run(task)
    assert result.status == expected
    assert result.task_id == task.task_id
    assert calls[0]["store"] is False
    assert "tools" not in calls[0]
