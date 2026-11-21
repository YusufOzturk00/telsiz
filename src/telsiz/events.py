"""Events published by the pipeline (console, WebSocket)."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VoiceEvent:
    """One translated utterance; serializes to the schema in CLAUDE.md section 4."""

    source_lang: str
    source_lang_confidence: float
    original: str
    translated: str | None  # None when no translation was possible
    target_lang: str
    latency_ms: int
    ts: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    speaker: str | None = None  # speaker identification is future work
    type: str = "voice"

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "id": self.id,
            "ts": self.ts,
            "source_lang": self.source_lang,
            "source_lang_confidence": self.source_lang_confidence,
            "original": self.original,
            "translated": self.translated,
            "target_lang": self.target_lang,
            "speaker": self.speaker,
            "latency_ms": self.latency_ms,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
