"""src.audio.schemas — Esquemas de datos para el módulo de grabaciones de voz/audio."""
from __future__ import annotations

from typing import Optional

from src.contracts import (
    ActionItem,
    ActionItemPriority,
    AudioNoteDocument,
    DiarizedSpeaker,
    MindMapDiagram,
    TranscriptSegment,
)

__all__ = [
    "ActionItem",
    "ActionItemPriority",
    "AudioNoteDocument",
    "DiarizedSpeaker",
    "MindMapDiagram",
    "TranscriptSegment",
    "format_ms_to_timestamp",
    "parse_timestamp_to_ms",
]


def format_ms_to_timestamp(ms: Optional[int]) -> str:
    """Convierte milisegundos a formato [MM:SS] o [HH:MM:SS]."""
    if ms is None or ms < 0:
        return "00:00"
    seconds = int(ms // 1000)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def parse_timestamp_to_ms(ts: str) -> int:
    """Parsea cadenas tipo 'MM:SS', 'HH:MM:SS' o segundos float a milisegundos."""
    if not ts:
        return 0
    ts = ts.strip().strip("[]()")
    try:
        parts = [float(p) for p in ts.split(":")]
        if len(parts) == 1:
            return int(parts[0] * 1000)
        elif len(parts) == 2:
            return int((parts[0] * 60 + parts[1]) * 1000)
        elif len(parts) == 3:
            return int((parts[0] * 3600 + parts[1] * 60 + parts[2]) * 1000)
    except Exception:
        pass
    return 0
