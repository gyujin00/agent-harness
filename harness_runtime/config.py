from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml


class RuntimeConfigError(ValueError):
    """Raised when harness/runtime.yaml cannot safely control a run."""


@dataclass(frozen=True)
class ProviderRuntimeConfig:
    worker_budget_usd: float | None = None
    verifier_budget_usd: float | None = None


@dataclass(frozen=True)
class RuntimeConfig:
    version: int = 1
    providers: Mapping[str, ProviderRuntimeConfig] = field(
        default_factory=lambda: {
            "claude": ProviderRuntimeConfig(5.0, 2.0),
            "codex": ProviderRuntimeConfig(),
        }
    )

    def budget(self, provider: str, role: str) -> float | None:
        if role not in {"worker", "verifier"}:
            raise RuntimeConfigError(f"unsupported role: {role}")
        try:
            provider_config = self.providers[provider]
        except KeyError as exc:
            raise RuntimeConfigError(f"unsupported provider: {provider}") from exc
        return (
            provider_config.worker_budget_usd
            if role == "worker"
            else provider_config.verifier_budget_usd
        )


def _budget(value: Any, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise RuntimeConfigError(f"{field_name} must be a positive number or null")
    return float(value)


def load_runtime_config(root: Path) -> RuntimeConfig:
    path = root / "harness" / "runtime.yaml"
    if not path.is_file():
        return RuntimeConfig()
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RuntimeConfigError(f"invalid runtime config YAML: {exc}") from exc
    if not isinstance(loaded, dict):
        raise RuntimeConfigError("runtime config must be a mapping")
    if loaded.get("version") != 1:
        raise RuntimeConfigError("runtime config version must be 1")
    raw_providers = loaded.get("providers")
    if not isinstance(raw_providers, dict):
        raise RuntimeConfigError("runtime config providers must be a mapping")

    providers: dict[str, ProviderRuntimeConfig] = {}
    for name in ("claude", "codex"):
        raw = raw_providers.get(name, {})
        if not isinstance(raw, dict):
            raise RuntimeConfigError(f"provider {name} config must be a mapping")
        providers[name] = ProviderRuntimeConfig(
            worker_budget_usd=_budget(
                raw.get("worker_budget_usd"),
                f"providers.{name}.worker_budget_usd",
            ),
            verifier_budget_usd=_budget(
                raw.get("verifier_budget_usd"),
                f"providers.{name}.verifier_budget_usd",
            ),
        )
    return RuntimeConfig(version=1, providers=providers)

