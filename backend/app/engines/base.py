"""Base types shared across analysis engines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EngineOutput:
    """Standard output of every analysis engine.

    - score: in [-1, +1]. Negative = bearish, positive = bullish, 0 = neutral.
    - confidence: in [0, 1]. How sure the engine is.
    - signals: structured per-engine details (patterns, levels, indicators).
    - notes: human-readable summary lines for the UI.
    """
    name: str
    score: float = 0.0
    confidence: float = 0.0
    signals: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def clamp(self) -> "EngineOutput":
        self.score = max(-1.0, min(1.0, float(self.score)))
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        return self

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 4),
            "confidence": round(self.confidence, 4),
            "signals": self.signals,
            "notes": self.notes,
        }
