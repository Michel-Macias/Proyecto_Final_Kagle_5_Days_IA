import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import google.generativeai as genai

from src.doc_squad import run_documentation_pipeline, run_audio_pipeline
from src.audio.schemas import format_ms_to_timestamp
from src.contracts import ActionItemPriority

# --------------------------------------------------------------------------- #
# Configuración de la página
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Doc Squad v2 | Multimodal AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        color: #1a73e8;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .badge-high {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-medium {
        background-color: #fef3c7;
        color: #92400e;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-low {
        background-color: #dcfce7;
        color: #166534;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Barra Lateral
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.image("https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg", width=45)
    st.title("Configuración")
    
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        user_api_key = st.text_input("Google API Key", type="password", help="Introduce tu API Key de Google AI Studio")
        if user_api_key:
            os.environ["GOOGLE_API_KEY"] = user_api_key
            os.environ["GEMINI_API_KEY"] = user_api_key
            genai.configure(api_key=user_api_key)
            st.success("API Key configurada!")
    else:
        os.environ["GEMINI_API_KEY"] = api_key
        st.success("✅ API Key detectada en entorno")

    st.markdown("### ⚙️ Modelo")
    model_selected = st.selectbox(
        "Modelo de Gemini",
        ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        index=0,
        help="Gemini 2.0 Flash ofrece la mejor velocidad y precisión multimodal."
    )
    os.environ["GEMINI_MODEL"] = model_selected

    st.markdown("--- ")
    st.markdown("### 🤖 Módulos Especializados")
    st.markdown("- 🎙️ **Audio Móvil**: .m4a, diarización, action items y mapas conceptuales Mermaid")
    st.markdown("- 📹 **Vídeo & Terminal**: Grounding, comandos y validación sintáctica")
    st.markdown("- 🔍 **Critic & Validator**: Detección determinista de errores")
    
    st.markdown("--- ")
    st.markdown("Creado por [Michel Macias](https://github.com/Michel-Macias)")

# --------------------------------------------------------------------------- #
# Funciones auxiliares
# --------------------------------------------------------------------------- #
def render_mermaid(code: str, height: int = 420):
    """Embebe un diagrama Mermaid interactivo vía iframe HTML."""
    clean_code = code.strip()
    html = f"""
    <div style="background: #fafafa; border-radius: 8px; padding: 16px; border: 1px solid #e0e0e0; display: flex; justify-content: center;">
        <pre class="mermaid">
        {clean_code}
        </pre>
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'neutral', securityLevel: 'loose' }});
    </script>
    """
    components.html(html, height=height, scrolling=True)


# --------------------------------------------------------------------------- #
# Contenido Principal
# --------------------------------------------------------------------------- #
st.markdown('<h1 class="main-header">🤖 Doc Squad AI v2</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Convierte grabaciones de voz del móvil (.m4a) y vídeos técnicos en documentación profesional, tareas y mapas conceptuales.</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

audio_extensions = {"m4a", "mp3", "wav", "aac", "ogg", "flac"}
video_extensions = {"mp4", "webm", "png", "jpg", "jpeg"}
all_supported = list(audio_extensions | video_extensions)

with col1:
    st.markdown("### 1. Entrada de Medios")
    uploaded_file = st.file_uploader(
        "Sube una nota de voz (.m4a), reunión, vídeo tutorial o imagen",
        type=all_supported,
        help="Soporta grabaciones de móvil en .m4a directamente de la app de notas de voz."
    )
    
    context = st.text_area(
        "Contexto adicional (Opcional)",
        placeholder="Ej: Reunión de sincronización de proyecto, notas de voz sobre arquitectura...",
        height=80
    )

    is_audio = False
    opt_diarization = True
    opt_summary = True
    opt_actions = True
    opt_mindmap = True
    if uploaded_file:
        ext = uploaded_file.name.split(".")[-1].lower()
        is_audio = ext in audio_extensions

        if is_audio:
            st.success(f"🎙️ **Grabación de audio detectada:** `{uploaded_file.name}`")
            st.markdown("**Alcance modular por bloques (selecciona lo que deseas procesar):**")
            mc1, mc2 = st.columns(2)
            with mc1:
                opt_diarization = st.checkbox("👥 Diarización (interlocutores y marcas)", value=True)
                opt_summary = st.checkbox("📋 Resumen ejecutivo & decisiones", value=True)
            with mc2:
                opt_actions = st.checkbox("✅ Tareas pendientes (Action Items)", value=True)
                opt_mindmap = st.checkbox("🧠 Mapa mental interactivo (Mermaid)", value=True)
            
            btn_label = "🎙️ Procesar Grabación de Audio"
        else:
            st.info(f"📹 **Medio técnico detectado:** `{uploaded_file.name}`")
            btn_label = "🚀 Generar Documentación Técnica"
    else:
        btn_label = "Generar Documentación"

    generate_btn = st.button(btn_label, type="primary", disabled=not uploaded_file)

with col2:
    st.markdown("### 2. Resultados")
    output_container = st.empty()

    if generate_btn and uploaded_file:
        active_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not active_key:
            st.error("⚠️ Por favor configura tu Google API Key en la barra lateral.")
        else:
            file_suffix = f".{uploaded_file.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            try:
                status_box = st.container()
                def update_status(msg: str):
                    with status_box:
                        if "✅" in msg:
                            st.success(msg)
                        elif "⚠️" in msg:
                            st.warning(msg)
                        elif "🤖" in msg or "🎙️" in msg:
                            st.info(msg)
                        else:
                            st.write(msg)

                with st.spinner('Procesando archivo con Gemini...'):
                    if is_audio:
                        # Pipeline especializado de audio móvil
                        audio_doc = run_audio_pipeline(
                            file_path=tmp_path,
                            request_context=context,
                            enable_diarization=opt_diarization,
                            enable_action_items=opt_actions,
                            enable_mind_map=opt_mindmap,
                            enable_summary=opt_summary,
                            status_callback=update_status,
                        )

                        with output_container.container():
                            st.success(f"✨ **{audio_doc.title}** procesado con éxito.")
                            
                            tab_res, tab_act, tab_map, tab_trn, tab_md = st.tabs([
                                "📋 Resumen & Puntos",
                                "✅ Tareas (Action Items)",
                                "🧠 Mapa Mental",
                                "🎙️ Transcripción",
                                "📝 Markdown Completo"
                            ])

                            with tab_res:
                                st.subheader("📋 Resumen Ejecutivo")
                                st.info(audio_doc.executive_summary)
                                
                                if audio_doc.key_topics:
                                    st.markdown("#### 📌 Temas Principales")
                                    for t in audio_doc.key_topics:
                                        st.markdown(f"- **{t}**")
                                
                                if audio_doc.key_decisions:
                                    st.markdown("#### 🎯 Decisiones Acordadas")
                                    for d in audio_doc.key_decisions:
                                        st.markdown(f"- ✅ {d}")

                            with tab_act:
                                st.subheader("✅ Tareas Pendientes extraídas")
                                if audio_doc.action_items:
                                    for item in audio_doc.action_items:
                                        with st.container():
                                            badge_cls = f"badge-{item.priority.value if hasattr(item.priority, 'value') else item.priority}"
                                            st.markdown(f"**{item.task}** <span class='{badge_cls}'>{item.priority.upper() if isinstance(item.priority, str) else item.priority.value.upper()}</span>", unsafe_allow_html=True)
                                            cols_info = st.columns([1, 1, 2])
                                            cols_info[0].caption(f"👤 Responsable: {item.assignee or 'No asignado'}")
                                            cols_info[1].caption(f"📅 Plazo: {item.due_date or 'No indicado'}")
                                            if item.context:
                                                cols_info[2].caption(f"💬 Contexto: {item.context}")
                                            st.divider()
                                else:
                                    st.info("No se detectaron tareas pendientes en el audio.")

                            with tab_map:
                                st.subheader("🧠 Mapa Mental Conceptual")
                                if audio_doc.mind_map and audio_doc.mind_map.mermaid_code:
                                    render_mermaid(audio_doc.mind_map.mermaid_code)
                                    with st.expander("Ver código Mermaid"):
                                        st.code(audio_doc.mind_map.mermaid_code, language="mermaid")
                                else:
                                    st.info("Mapa mental no generado para este archivo.")

                            with tab_trn:
                                st.subheader("🎙️ Transcripción con Diarización")
                                if audio_doc.transcript_segments:
                                    for seg in audio_doc.transcript_segments:
                                        ts = format_ms_to_timestamp(seg.start_ms)
                                        speaker = seg.speaker or "Interlocutor"
                                        st.markdown(f"`[{ts}]` **{speaker}:** {seg.text}")
                                else:
                                    st.info("Transcripción no disponible.")

                            with tab_md:
                                st.subheader("📝 Documento Markdown Exportado")
                                full_md = audio_doc.raw_markdown or ""
                                st.text_area("Markdown", full_md, height=300)
                                st.download_button(
                                    label="📥 Descargar Markdown (.md)",
                                    data=full_md,
                                    file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_resumen.md",
                                    mime="text/markdown"
                                )

                    else:
                        # Pipeline técnico de vídeo/imágenes
                        final_doc = run_documentation_pipeline(tmp_path, context, status_callback=update_status)
                        output_container.markdown(final_doc)
                        st.download_button(
                            label="📥 Descargar Documentación Markdown",
                            data=final_doc,
                            file_name="documentacion_generada.md",
                            mime="text/markdown"
                        )

            except Exception as e:
                st.error(f"Ocurrió un error en el procesamiento: {str(e)}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    elif not uploaded_file:
        output_container.info("👈 Sube una nota de voz (.m4a, .mp3) o vídeo para comenzar.")
