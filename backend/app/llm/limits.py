from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelLimits:
    rpm: int
    tpm: int
    rpd: int


DEFAULT_LIMITS = ModelLimits(rpm=1000, tpm=1_000_000, rpd=10_000)
GEMINI_3_PRO_LIMITS = ModelLimits(rpm=250, tpm=1_000_000, rpd=1_000)


def get_model_limits(full_model_name: str) -> ModelLimits:
    name = (full_model_name or "").lower()
    if "gemini-3-pro" in name:
        return GEMINI_3_PRO_LIMITS
    return DEFAULT_LIMITS
