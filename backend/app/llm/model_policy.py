from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelLimits:
    rpm: int
    tpm: int
    rpd: int
    tpm_burst: int


# Per-model quota overrides. Any missing value falls back to global defaults.
# Keys are canonical model keys (e.g. google-vertex/<model>, openrouter/<model>).
MODEL_LIMIT_OVERRIDES: dict[str, dict[str, int]] = {
    "google-vertex/gemini-2.5-flash-lite-preview-09-2025": {
        "rpm": 4000,
        "tpm": 4_000_000,
        "rpd": 100_000,
        "tpm_burst": 400_000,
    },
    "google-api/gemini-2.5-flash-lite-preview-09-2025": {
        "rpm": 4000,
        "tpm": 4_000_000,
        "rpd": 100_000,
        "tpm_burst": 400_000,
    },
    "openrouter/google/gemini-2.5-flash-lite-preview-09-2025": {
        "rpm": 16_000,
        "tpm": 16_000_000,
        "rpd": 400_000,
        "tpm_burst": 1_600_000,
    },
    "google-vertex/gemini-3-flash-preview": {
        "rpm": 1000,
        "tpm": 1_000_000,
        "rpd": 10_000,
        "tpm_burst": 150_000,
    },
    "google-api/gemini-3-flash-preview": {
        "rpm": 1000,
        "tpm": 1_000_000,
        "rpd": 10_000,
        "tpm_burst": 150_000,
    },
    "openrouter/google/gemini-3-flash-preview": {
        "rpm": 4000,
        "tpm": 4_000_000,
        "rpd": 40_000,
        "tpm_burst": 400_000,
    },
}

# Ordered per-model fallback chains (primary excluded from list).
MODEL_FALLBACK_CHAINS: dict[str, list[str]] = {
    "google-vertex/gemini-2.5-flash-lite-preview-09-2025": [
        "google-api/gemini-2.5-flash-lite-preview-09-2025",
    ],
}

# Requeue backoff defaults when no retry-after is available.
RATE_LIMIT_BACKOFF_SECONDS: tuple[int, ...] = (15, 45, 120)


def canonicalize_model_key(model_key: str) -> str:
    if "/" not in model_key:
        return model_key
    provider, remainder = model_key.split("/", 1)
    if provider == "google":
        return f"google-vertex/{remainder}"
    return model_key


def get_model_fallback_chain(model_key: str) -> list[str]:
    primary = canonicalize_model_key(model_key)
    out: list[str] = [primary]
    configured = MODEL_FALLBACK_CHAINS.get(primary, [])
    for item in configured:
        candidate = canonicalize_model_key(item)
        if candidate not in out:
            out.append(candidate)
    return out


def resolve_model_limits(model_key: str, settings: Any) -> ModelLimits:
    canonical = canonicalize_model_key(model_key)
    override = MODEL_LIMIT_OVERRIDES.get(canonical, {})
    return ModelLimits(
        rpm=int(override.get("rpm", settings.LLM_MODEL_GLOBAL_RPM)),
        tpm=int(override.get("tpm", settings.LLM_MODEL_GLOBAL_TPM)),
        rpd=int(override.get("rpd", settings.LLM_MODEL_GLOBAL_RPD)),
        tpm_burst=int(override.get("tpm_burst", settings.LLM_MODEL_GLOBAL_TPM_BURST)),
    )
