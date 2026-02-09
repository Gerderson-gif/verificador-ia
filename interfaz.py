import streamlit as st
import os
import tempfile
from langchain_core.messages import HumanMessage
# Importamos las funciones necesarias del motor app.py
from app import (
    obtener_ia, 
    transcribir_audio, 
    detectar_imagen_ia, 
    descargar_desde_link, 
    extraer_audio, 
    analizar_frames_video,
    buscar_en_internet
)

# Configuración de página
st.set_page_config(page_title="Detector de Verdad IA", page_icon="🕵️", layout="centered")

# Estilos CSS Profesionales (Diseño Forense)
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; font-weight: bold;}
    .stMetric {background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #d1d3d8;}
    [data-testid="stExpander"] { border: 1px solid #007bff; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🕵️ Centro de Verificación IA")
st.caption("Peritaje Digital: Análisis Forense de Redes Sociales y Verificación en Tiempo Real.")

# --- PESTAÑAS ---
tab_video, tab_imagen, tab_chat = st.tabs(["📹 Analizar Video/Link", "🖼️ Detectar Imagen IA", "💬 Chat Libre"])

# ==========================================
# PESTAÑA 1: VIDEO Y LINKS (FACT-CHECKER)
# ==========================================
with tab_video:
    st.header("📂 Entrada de Evidencia")
    
    fuente = st.radio("Origen del contenido:", ["Pegar Link (TikTok/YT/Reels)", "Subir Archivo Local"], horizontal=True)
    
    # Inicializamos la ruta del video en la sesión para que persista entre clics
    if 'video_path' not in st.session_state:
        st.session_state.video_path = None

    if fuente == "Pegar Link (TikTok/YT/Reels)":
        url = st.text_input("Pega la URL del video aquí:", placeholder="https://www.tiktok.com/...")
        if url:
            if st.button("📥 DESCARGAR CONTENIDO"):
                with st.spinner("📥 Descargando evidencia para análisis forense..."):
                    st.session_state.video_path = descargar_desde_link(url)
                    if st.session_state.video_path and os.path.exists(st.session_state.video_path):
                        st.success(f"✅ Evidencia lista para procesar.")
                    else:
                        st.error("Error en la descarga del enlace.")
    else:
        video_file = st.file_uploader("Sube tu archivo (MP4, MOV, AVI, WEBM)", type=["mp4", "mov", "avi", "webm"])
        if video_file:
            suffix = os.path.splitext(video_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(video_file.read())
                st.session_state.video_path = tmp.name
            st.video(video_file)

    # --- BLOQUE 1: PERITAJE DE VERACIDAD (Audio + OSINT) ---
    if st.session_state.video_path:
        st.divider()
        if st.button("🔍 INICIAR PERITAJE DE VERACIDAD", type="primary"):
            with st.status("🛠️ Procesando evidencia digital...", expanded=True) as status:
                st.write("🎧 Extrayendo y optimizando pista de audio...")
                ruta_audio = extraer_audio(st.session_state.video_path)
                
                st.write("📝 Transcribiendo con Whisper-v3...")
                texto_transcrito = transcribir_audio(ruta_audio)
                
                if "Error" in texto_transcrito:
                    st.error(texto_transcrito)
                    status.update(label="❌ Fallo en procesamiento", state="error")
                else:
                    st.write("🌍 Consultando Google Search (Serper API)...")
                    contexto_web = buscar_en_internet(f"verificar noticia: {texto_transcrito[:150]}")
                    
                    status.update(label="✅ Peritaje de contenido completado", state="complete")

                    with st.expander("📄 Ver Transcripción Extraída"):
                        st.text_area("", texto_transcrito, height=150)

                    st.subheader("📊 Reporte de Veracidad Digital")
                    llm = obtener_ia()
                    if llm:
                        # PROMPT REFORZADO PARA MOSTRAR LINKS
                        prompt_fact_check = f"""
                        Eres un Analista Forense Digital experto. 
                        Tu misión es contrastar esta TRANSCRIPCIÓN con los RESULTADOS DE GOOGLE proporcionados.

                        TRANSCRIPCIÓN: 
                        "{texto_transcrito}"

                        RESULTADOS DE GOOGLE (FUENTES):
                        {contexto_web}

                        Genera un informe técnico con la siguiente estructura:
                        1. 📝 **Resumen Ejecutivo**: Explicación de lo que afirma el video.
                        2. 🔍 **Contraste Forense**: Compara los datos con las fuentes.
                        3. ⚖️ **Veredicto**: [Verdadero], [Falso] o [Engañoso].
                        4. 🔗 **Fuentes de Verificación**: LISTA AQUÍ TODOS LOS LINKS QUE APARECEN EN LOS RESULTADOS DE GOOGLE.
                        """
                        with st.spinner("🧠 Generando reporte detallado..."):
                            res = llm.invoke([HumanMessage(content=prompt_fact_check)])
                            st.markdown(res.content)

        # --- BLOQUE 2: ESCÁNER VISUAL (DEEPFAKE) ---
        st.divider()
        st.subheader("👁️ Análisis Visual de Fotogramas")
        st.info("Nota: Este análisis depende de la disponibilidad de la API de Hugging Face.")
        
        if st.button("🖼️ VERIFICAR FOTOGRAMAS CLAVE"):
            with st.spinner("Analizando frames en busca de rastros de IA..."):
                resultados_visuales = analizar_frames_video(st.session_state.video_path)
                
                if resultados_visuales and "error" not in str(resultados_visuales):
                    total = len(resultados_visuales)
                    ia_frames = sum(1 for r in resultados_visuales if r['etiqueta'] == 'AI')
                    porcentaje = (ia_frames / total) * 100
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Frames", total)
                    c2.metric("Positivos IA", ia_frames)
                    c3.metric("Probabilidad", f"{porcentaje:.1f}%")
                    
                    st.table(resultados_visuales)
                else:
                    st.error("❌ El servicio de análisis visual no está disponible en este momento (Error 410/503).")

# ==========================================
# PESTAÑA 2: IMAGEN ESTÁTICA
# ==========================================
with tab_imagen:
    st.header("🖼️ Detección en Imagen")
    img_file = st.file_uploader("Sube una foto", type=["jpg", "png", "jpeg"])
    if img_file:
        st.image(img_file, width=300)
        if st.button("🔍 Analizar Píxeles"):
            res = detectar_imagen_ia(img_file.read())
            st.write("### Resultado del Motor:")
            st.json(res)

# ==========================================
# PESTAÑA 3: CHAT LIBRE
# ==========================================
with tab_chat:
    st.subheader("💬 Consultoría Técnica")
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input("Haz una consulta sobre ciberseguridad..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        ia = obtener_ia()
        if ia:
            with st.chat_message("assistant"):
                r = ia.invoke(p).content
                st.markdown(r)
                st.session_state.messages.append({"role": "assistant", "content": r})