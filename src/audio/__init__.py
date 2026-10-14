"""src.audio — Paquete de análisis de grabaciones de voz, notas móviles y reuniones."""
from __future__ import annotations

from src.audio.mock import MockAudioProcessor
from src.audio.pipeline import AudioProcessor, export_audio_to_markdown
from src.audio.schemas import (
    ActionItem,
    ActionItemPriority,
    AudioNoteDocument,
    DiarizedSpeaker,
    MindMapDiagram,
    TranscriptSegment,
    format_ms_to_timestamp,
    parse_timestamp_to_ms,
)

__all__ = [
    "AudioProcessor",
    "MockAudioProcessor",
    "export_audio_to_markdown",
    "ActionItem",
    "ActionItemPriority",
    "AudioNoteDocument",
    "DiarizedSpeaker",
    "MindMapDiagram",
    "TranscriptSegment",
    "format_ms_to_timestamp",
    "parse_timestamp_to_ms",
]
