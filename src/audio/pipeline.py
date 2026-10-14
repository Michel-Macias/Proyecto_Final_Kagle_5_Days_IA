"""src.audio.pipeline — Pipeline de procesamiento y análisis de grabaciones de audio."""
from __future__ import annotations

import os
import time
from typing import Callable, Optional

from src.contracts import (
    ActionItem,
    ActionItemPriority,
    AudioNoteDocument,
    DiarizedSpeaker,
    MindMapDiagram,
    TranscriptSegment,
)
from src.audio.prompts import (
    AUDIO_ANALYSIS_SYSTEM_PROMPT,
    AUDIO_ANALYSIS_USER_TEMPLATE,
)
from src.audio.schemas import format_ms_to_timestamp


def export_audio_to_markdown(doc: AudioNoteDocument) -> str:
    """Genera un documento Markdown elegante y estructurado a partir de un AudioNoteDocument."""
    lines = []
    lines.append(f"# {doc.title}\n")

    # Resumen Ejecutivo
    if doc.executive_summary:
        lines.append("## 📋 Resumen Ejecutivo\n")
        lines.append(f"> {doc.executive_summary}\n")

    # Puntos Clave y Decisiones
    if doc.key_topics or doc.key_decisions:
        lines.append("## 📌 Puntos Clave & Decisiones\n")
        if doc.key_topics:
            lines.append("### Temas Tratados")
            for topic in doc.key_topics:
                lines.append(f"- **{topic}**")
            lines.append("")
        if doc.key_decisions:
            lines.append("### Decisiones Acordadas")
            for decision in doc.key_decisions:
                lines.append(f"- ✅ {decision}")
            lines.append("")

    # Tareas Pendientes (Action Items)
    if doc.action_items:
        lines.append("## ✅ Tareas Pendientes (Action Items)\n")
        lines.append("| Prioridad | Tarea | Responsable | Plazo | Contexto |")
        lines.append("|:---:|:---|:---|:---|:---|")
        priority_icons = {
            ActionItemPriority.HIGH: "🔴 Alta",
            ActionItemPriority.MEDIUM: "🟡 Media",
            ActionItemPriority.LOW: "🟢 Baja",
        }
        for item in doc.action_items:
            p_label = priority_icons.get(item.priority, str(item.priority))
            assignee = item.assignee or "Sin asignar"
            due = item.due_date or "--"
            ctx = item.context or "--"
            lines.append(f"| {p_label} | {item.task} | {assignee} | {due} | {ctx} |")
        lines.append("")

    # Mapa Mental (Mermaid)
    if doc.mind_map and doc.mind_map.mermaid_code:
        lines.append("## 🧠 Mapa Mental Conceptual\n")
        if doc.mind_map.summary:
            lines.append(f"{doc.mind_map.summary}\n")
        lines.append("```mermaid")
        lines.append(doc.mind_map.mermaid_code.strip())
        lines.append("```\n")

    # Interlocutores identificados
    if doc.speakers:
        lines.append("## 👥 Interlocutores Identificados\n")
        for spk in doc.speakers:
            info = f"**{spk.display_name or spk.speaker_id}**"
            if spk.role:
                info += f" ({spk.role})"
            lines.append(f"- {info}")
        lines.append("")

    # Transcripción Diarizada
    if doc.transcript_segments:
        lines.append("## 🎙️ Transcripción Diarizada\n")
        for seg in doc.transcript_segments:
            ts = format_ms_to_timestamp(seg.start_ms)
            speaker_tag = f"**[{ts}] {seg.speaker or 'Voz'}:**"
            lines.append(f"{speaker_tag} {seg.text}\n")

    return "\n".join(lines)


class AudioProcessor:
    """Procesador multimodal de audio con Gemini 2.0 / 1.5 y salida estructurada."""

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        *,
        timeout_seconds: int = 600,
    ):
        self.api_key = api_key or self._resolve_api_key()
        self.model = model or os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)
        self.timeout_seconds = timeout_seconds
        self._client = None

    @staticmethod
    def _resolve_api_key() -> Optional[str]:
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    @property
    def client(self):
        if self._client is None:
            from google import genai
            if not self.api_key:
                raise RuntimeError("No se detectó GEMINI_API_KEY ni GOOGLE_API_KEY.")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

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
            else:
                print(msg)

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")

        from google.genai import types

        filename = os.path.basename(audio_path)
        notify(f"🤖 AudioAgent: Subiendo grabación {filename}...")

        # 1. Subida del fichero a Gemini Files API
        uploaded_file = self.client.files.upload(file=audio_path)
        start_wait = time.time()
        while uploaded_file.state.name == "PROCESSING":
            if time.time() - start_wait > self.timeout_seconds:
                raise TimeoutError(f"Tiempo agotado procesando audio: {filename}")
            time.sleep(2)
            uploaded_file = self.client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise RuntimeError(f"Fallo al procesar el audio en Gemini: {filename}")

        notify("✅ AudioAgent: Audio listo. Extrayendo notas y diarización...")

        # 2. Generación estructurada con Pydantic AudioNoteDocument
        context_block = f"Contexto adicional del usuario: {context}" if context else ""
        user_prompt = AUDIO_ANALYSIS_USER_TEMPLATE.format(
            context_block=context_block,
            enable_diarization="Sí" if enable_diarization else "No",
            enable_action_items="Sí" if enable_action_items else "No",
            enable_mind_map="Sí" if enable_mind_map else "No",
            enable_summary="Sí" if enable_summary else "No",
        )

        notify("🤖 AudioAgent: Generando resumen, action items y mapa mental...")
        response = self.client.models.generate_content(
            model=self.model,
            contents=[uploaded_file, user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=AUDIO_ANALYSIS_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=AudioNoteDocument,
                temperature=0.2,
            ),
        )

        # 3. Limpieza del archivo remoto en Gemini (best-effort)
        try:
            self.client.files.delete(name=uploaded_file.name)
        except Exception:
            pass

        result_doc: AudioNoteDocument = response.parsed
        if not result_doc.title:
            result_doc.title = f"Notas de Audio: {filename}"

        # Adjuntar versión Markdown completa renderizada
        result_doc.raw_markdown = export_audio_to_markdown(result_doc)
        notify("✅ AudioAgent: Proceso completado con éxito.")
        return result_doc
