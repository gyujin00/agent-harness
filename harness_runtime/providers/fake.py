from __future__ import annotations

from collections import deque
from collections.abc import Sequence

from .base import AgentRequest, AgentResult, ProviderError


class FakeProvider:
    name = "fake"

    def __init__(self, results: Sequence[AgentResult]) -> None:
        self._results = deque(results)
        self.requests: list[AgentRequest] = []

    @classmethod
    def passing(cls, summary: str = "fake pass") -> FakeProvider:
        return cls([AgentResult.pass_(summary)])

    def run(self, request: AgentRequest) -> AgentResult:
        self.requests.append(request)
        if not self._results:
            raise ProviderError("fake provider script is exhausted")
        return self._results.popleft()

