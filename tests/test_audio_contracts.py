"""Tests para los contratos y pipeline de audio móvil (Doc Squad v2)."""
from __future__ import annotations

import pytest
from src.contracts import (
    ActionItem,
    ActionItemPriority,
    AudioNoteDocument,
    DiarizedSpeaker,
    MindMapDiagram,
    TranscriptSegment,
    PipelineResult,
    IngestResult,
)
from src.audio import MockAudioProcessor, export_audio_to_markdown, format_ms_to_timestamp, parse_timestamp_to_ms


def test_format_and_parse_timestamp():
    assert format_ms_to_timestamp(0) == "00:00"
    assert format_ms_to_timestamp(65000) == "01:05"
    assert format_ms_to_timestamp(3665000) == "01:01:05"
    assert format_ms_to_timestamp(None) == "00:00"

    assert parse_timestamp_to_ms("01:05") == 65000
    assert parse_timestamp_to_ms("[00:12]") == 12000
    assert parse_timestamp_to_ms("01:00:00") == 3600000
    assert parse_timestamp_to_ms("") == 0


def test_audio_contracts_models():
    speaker = DiarizedSpeaker(speaker_id="spk_1", display_name="Michel", role="Líder")
    assert speaker.speaker_id == "spk_1"
    assert speaker.display_name == "Michel"

    action = ActionItem(
        item_id="a1",
        task="Implementar soporte .m4a",
        assignee="Michel",
        priority=ActionItemPriority.HIGH,
    )
    assert action.priority == ActionItemPriority.HIGH

    diagram = MindMapDiagram(
        title="Mapa Mental",
        mermaid_code="mindmap\n  root((Audio))\n    Mobile",
    )
    assert diagram.diagram_type == "mindmap"
    assert "mindmap" in diagram.mermaid_code

    doc = AudioNoteDocument(
        title="Test Audio",
        executive_summary="Resumen de audio",
        speakers=[speaker],
        action_items=[action],
        mind_map=diagram,
    )
    assert len(doc.speakers) == 1
    assert len(doc.action_items) == 1
    assert doc.mind_map is not None


def test_mock_audio_processor_execution():
    processor = MockAudioProcessor()
    logs = []

    doc = processor.process_audio(
        "/tmp/fake_recording.m4a",
        context="Reunión técnica sobre v2",
        enable_diarization=True,
        enable_action_items=True,
        enable_mind_map=True,
        enable_summary=True,
        status_callback=logs.append,
    )

    assert isinstance(doc, AudioNoteDocument)
    assert doc.title == "Notas de Grabación: fake_recording.m4a"
    assert len(doc.speakers) == 2
    assert len(doc.action_items) == 3
    assert doc.mind_map is not None
    assert "mindmap" in doc.mind_map.mermaid_code
    assert len(doc.transcript_segments) == 3
    assert any("Completado" in log or "Iniciando" in log or "Analizando" in log for log in logs)

    # Verificar que el markdown se generó correctamente
    md = export_audio_to_markdown(doc)
    assert "# Notas de Grabación: fake_recording.m4a" in md
    assert "## 📋 Resumen Ejecutivo" in md
    assert "## ✅ Tareas Pendientes (Action Items)" in md
    assert "```mermaid" in md
    assert "## 🎙️ Transcripción Diarizada" in md
    assert "[00:00] Michel:" in md


def test_pipeline_result_with_audio_doc():
    processor = MockAudioProcessor()
    doc = processor.process_audio("voice_note.m4a")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    result = PipelineResult(
        run_id="run_audio_123",
        started_at=now,
        ingest=IngestResult(),
        audio_document=doc,
        status="ok",
    )
    assert result.audio_document is not None
    assert result.audio_document.title == "Notas de Grabación: voice_note.m4a"
    assert len(result.audio_document.action_items) == 3
