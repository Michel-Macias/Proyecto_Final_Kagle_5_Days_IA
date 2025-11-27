# Guía de Uso del Proyecto

Este documento detalla las diferentes formas de interactuar con el sistema **Doc Squad**.

## 🌐 1. Interfaz Web (Recomendado)

La forma más fácil de usar el sistema es a través de la interfaz web moderna construida con Streamlit.

### Pasos:

1. **Iniciar la aplicación**:
   ```bash
   streamlit run app.py
   ```

2. **Abrir en el navegador**:
   La aplicación se abrirá automáticamente en `http://localhost:8501`.

3. **Uso**:
   - Introduce tu **Google API Key** en la barra lateral (si no la tienes en `.env`).
   - Arrastra y suelta tu archivo de video/audio/imagen.
   - (Opcional) Añade contexto extra.
   - Haz clic en **"Generar Documentación"**.
   - Descarga el archivo Markdown resultante.

---

## 📓 2. Jupyter Notebook

Ideal para entender el flujo paso a paso o para entornos como Kaggle y Google Colab.

### Pasos:

1. **Abrir el notebook**:
   ```bash
   jupyter notebook project_notebook.ipynb
   ```

2. **Ejecutar celdas**:
   Sigue las instrucciones dentro del notebook para ejecutar el pipeline celda por celda.

---

## 💻 3. Línea de Comandos (CLI)

Para usuarios avanzados o integración en scripts automatizados.

### Script de Verificación (`verify_pipeline.py`)

Ejecuta el pipeline con un video de prueba predefinido:

```bash
python verify_pipeline.py
```

### Uso Programático

Puedes importar el módulo `src.doc_squad` en tus propios scripts Python:

```python
from src.doc_squad import run_documentation_pipeline
import os

# Asegúrate de tener la API Key configurada
os.environ["GOOGLE_API_KEY"] = "tu_api_key"

# Ejecutar pipeline
documento = run_documentation_pipeline(
    file_path="ruta/a/tu/video.mp4",
    request_context="Tutorial de instalación de servidor web"
)

print(documento)
```

---

## 🔧 Solución de Problemas Comunes

### Error: `ModuleNotFoundError: No module named 'streamlit'`
Instala las dependencias necesarias:
```bash
pip install -r requirements.txt
# O manualmente:
pip install streamlit google-adk google-generativeai python-dotenv
```

### Error: `Google API Key not found`
Asegúrate de tener un archivo `.env` en la raíz del proyecto con el siguiente contenido:
```bash
GOOGLE_API_KEY="tu_api_key_aqui"
```
O introdúcela manualmente en la interfaz web.

### El proceso tarda mucho
El procesamiento de video por parte de Gemini puede tardar unos minutos dependiendo de la duración del video. La interfaz web mostrará indicadores de progreso.
