# 🕵️‍♂️ Verificador de Hechos con IA

Aplicación web construida con Python y Streamlit que verifica noticias en tiempo real utilizando Inteligencia Artificial.

## 🚀 Características
- **Búsqueda en vivo:** Utiliza DuckDuckGo para buscar información reciente (2025-2026).
- **Análisis IA:** Usa el modelo Llama 3 (vía Groq) para analizar la veracidad.
- **RAG Agresivo:** Ignora el conocimiento pre-entrenado para priorizar noticias actuales.
- **Exportación PDF:** Genera reportes descargables con marca de agua.

## 🛠️ Tecnologías
- Python 3.13
- Streamlit (Frontend)
- LangChain (Orquestación)
- Groq Cloud (LLM Llama 3.3)
- DuckDuckGo Search (Búsqueda Web)
- ReportLab (Generación PDF)

## 📦 Instalación
1. Clonar el repositorio.
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
