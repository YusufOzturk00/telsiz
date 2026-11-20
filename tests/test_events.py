"""Tests for the WebSocket/console event schema (CLAUDE.md section 4)."""

import json
import uuid

from telsiz.events import VoiceEvent

SCHEMA_KEYS = [
    "type",
    "id",
    "ts",
    "source_lang",
    "source_lang_confidence",
    "original",
    "translated",
    "target_lang",
    "speaker",
    "latency_ms",
]


def make_event(**overrides):
    fields = {
        "source_lang": "ru",
        "source_lang_confidence": 0.93,
        "original": "Они идут на Б",
        "translated": "B'ye geliyorlar",
        "target_lang": "tr",
        "latency_ms": 1450,
        "ts": 1732100000.123,
    }
    fields.update(overrides)
    return VoiceEvent(**fields)


def test_event_serializes_to_the_documented_schema():
    data = json.loads(make_event().to_json())

    assert list(data) == SCHEMA_KEYS
    assert data["type"] == "voice"
    assert data["speaker"] is None
    assert data["original"] == "Они идут на Б"
    uuid.UUID(data["id"])


def test_events_get_unique_ids():
    assert make_event().id != make_event().id


def test_json_keeps_non_ascii_text_readable():
    assert "Они идут" in make_event().to_json()
