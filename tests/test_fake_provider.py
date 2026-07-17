from __future__ import annotations

from pathlib import Path

import pytest

from harness_runtime.providers.base import AgentRequest, AgentResult, AgentRole, ProviderError
from harness_runtime.providers.fake import FakeProvider


def request(tmp_path: Path) -> AgentRequest:
    schema = tmp_path / "schema.json"
    schema.write_text("{}", encoding="utf-8")
    return AgentRequest(
        role=AgentRole.WORKER,
        agent_name="backend-worker",
        prompt="work",
        workdir=tmp_path,
        output_schema=schema,
        raw_output_dir=tmp_path / "raw",
        timeout_seconds=30,
    )


def test_fake_provider_returns_scripted_results_in_order(tmp_path: Path) -> None:
    provider = FakeProvider(
        [AgentResult.fail("broken"), AgentResult.pass_("fixed")]
    )

    assert provider.run(request(tmp_path)).status == "fail"
    assert provider.run(request(tmp_path)).status == "pass"
    assert len(provider.requests) == 2


def test_fake_provider_fails_when_script_is_exhausted(tmp_path: Path) -> None:
    provider = FakeProvider([AgentResult.pass_("once")])
    provider.run(request(tmp_path))

    with pytest.raises(ProviderError, match="exhausted"):
        provider.run(request(tmp_path))
