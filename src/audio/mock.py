"""src.audio.mock — Mock determinista para análisis de audio sin dependencias externas."""
from __future__ import annotations

import os
from typing import Callable, Optional

from src.contracts import (
    ActionItem,
    ActionItemPriority,
    AudioNoteDocument,
    DiarizedSpeaker,
    MindMapDiagram,
    TranscriptSegment,
)


class MockAudioProcessor:
    """Procesador simulado de grabaciones de voz para tests y desarrollo offline."""

    def __init__(self, model: str = "mock-gemini-audio"):
        self.model = model

    def process_audio(
        self,
        audio_path: str,
        context: str = "",
        *,
        enable_diarization: bool = True,
        enable_action_items: bool = True,
        enable_mind_map: bool = True,
        enable_summary: bool = True,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> AudioNoteDocument:
        def notify(msg: str):
            if status_callback:
                status_callback(msg)

        filename = os.path.basename(audio_path) if audio_path else "audio_sample.m4a"
        notify(f"[Mock] Ingestando grabación: {filename}")
        notify("[Mock] Analizando interlocutores y extrayendo compromisos...")

        speakers = [
            DiarizedSpeaker(speaker_id="speaker_1", display_name="Michel", role="Líder de Proyecto"),
            DiarizedSpeaker(speaker_id="speaker_2", display_name="Dev Lead", role="Desarrollador"),
        ] if enable_diarization else []

        segments = [
            TranscriptSegment(
                segment_id="seg_1",
                start_ms=0,
                end_ms=4500,
                speaker="Michel" if enable_diarization else None,
                text="Hola a todos, arrancamos la reunión para definir el soporte de audio móvil en Doc Squad v2.",
            ),
            TranscriptSegment(
                segment_id="seg_2",
                start_ms=4800,
                end_ms=9200,
                speaker="Dev Lead" if enable_diarization else None,
                text="Perfecto. Tenemos que soportar .m4a directamente de las grabadoras de voz y extraer tareas automáticas.",
            ),
            TranscriptSegment(
                segment_id="seg_3",
                start_ms=9500,
                end_ms=15000,
                speaker="Michel" if enable_diarization else None,
                text="De acuerdo. Yo me encargo de revisar la arquitectura y tú implementas el selector dinámico en Streamlit antes del viernes.",
            ),
        ]

        action_items = [
            ActionItem(
                item_id="act_1",
                task="Revisar arquitectura de contratos y esquemas para audio",
                assignee="Michel",
                due_date="Esta semana",
                priority=ActionItemPriority.HIGH,
                context="Definir esquemas DiarizedSpeaker y ActionItem",
                source_timestamp_ms=9500,
            ),
            ActionItem(
                item_id="act_2",
                task="Implementar selector dinámico en la interfaz Streamlit",
                assignee="Dev Lead",
                due_date="Viernes",
                priority=ActionItemPriority.HIGH,
                context="Soporte para .m4a y pestañas interactivas",
                source_timestamp_ms=12000,
            ),
            ActionItem(
                item_id="act_3",
                task="Verificar batería de pruebas con pytest en Docker",
                assignee="Equipo",
                due_date=None,
                priority=ActionItemPriority.MEDIUM,
                context="Garantizar 100% de tests en verde",
                source_timestamp_ms=14000,
            ),
        ] if enable_action_items else []

        mermaid_code = """mindmap
  root((Doc Squad Audio v2))
    Ingesta
      Formato m4a
      Multilingue
    Analisis
      Diarizacion de interlocutores
      Resumen ejecutivo
    Entregables
      Action Items
      Mapa mental Mermaid"""

        mind_map = MindMapDiagram(
            title="Mapa Mental: Doc Squad Audio v2",
            diagram_type="mindmap",
            mermaid_code=mermaid_code,
            summary="Estructura de la evolución multimodal para notas de voz.",
        ) if enable_mind_map else None

        summary_text = (
            "Reunión de planificación para la evolución de Doc Squad v2 enfocada en audio móvil. "
            "Se definieron los requisitos para ficheros .m4a, diarización de interlocutores, "
            "extracción de tareas pendientes con responsables y generación de mapas conceptuales en Mermaid."
        ) if enable_summary else "Audio procesado."

        doc = AudioNoteDocument(
            title=f"Notas de Grabación: {filename}",
            language="es",
            executive_summary=summary_text,
            key_topics=["Soporte m4a móvil", "Diarización de voz", "Action Items", "Diagramas Mermaid"],
            key_decisions=[
                "Priorizar la fase exclusiva de audio móvil antes de la reorganización de vídeo",
                "Mantener compatibilidad 100% con los contratos existentes del pipeline",
            ],
            speakers=speakers,
            transcript_segments=segments,
            action_items=action_items,
            mind_map=mind_map,
        )
        from src.audio.pipeline import export_audio_to_markdown
        doc.raw_markdown = export_audio_to_markdown(doc)
        notify("[Mock] ✅ Análisis completado con éxito.")
        return doc
