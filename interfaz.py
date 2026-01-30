import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from app import obtener_ia, transcribir_video, detectar_imagen_ia # <--- Importamos la nueva función

st.set_page_config(page_title="Detector de Verdad IA", page_icon="🕵️", layout="centered")

# Estilos CSS (Modo oscuro y limpio)
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("🕵️ Centro de Verificación IA")
st.caption("Analiza videos e imágenes para descubrir la verdad.")

# --- CREAMOS LAS PESTAÑAS ---
tab_video, tab_imagen, tab_chat = st.tabs(["📹 Analizar Video", "🖼️ Detectar Imagen IA", "💬 Chat Libre"])

# ==========================================
# PESTAÑA 1: VIDEO (VERSIÓN PRO)
# ==========================================
with tab_video:
    st.header("📂 Análisis de Video Inteligente")
    st.info("ℹ️ Nota: Por limitaciones de la API, el video debe pesar menos de 25MB.")
    
    # Subida de archivo
    video_file = st.file_uploader("Sube tu MP4", type=["mp4", "mov", "avi"], key="video_uploader")
    
    if video_file:
        # 1. VALIDACIÓN DE PESO (Preventiva)
        # Convertimos bytes a Megabytes
        file_size_mb = video_file.size / (1024 * 1024)
        
        if file_size_mb > 25:
            st.error(f"🚨 El archivo es demasiado pesado ({file_size_mb:.2f} MB). El límite es 25 MB.")
            st.warning("💡 Consejo: Usa una herramienta online para comprimir el video antes de subirlo.")
        else:
            # Si el peso es correcto, mostramos el video y el botón
            st.video(video_file)
            st.caption(f"Peso del archivo: {file_size_mb:.2f} MB")
            
            if st.button("🔍 Analizar Video", type="primary"):
                # A. TRANSCRIPCIÓN
                with st.spinner("🎧 Escuchando cada palabra del video..."):
                    # Reiniciamos el puntero del archivo al principio por si acaso
                    video_file.seek(0)
                    texto_transcrito = transcribir_video(video_file)
                
                # B. VERIFICACIÓN DE ERRORES
                if "Error:" in texto_transcrito:
                    st.error(texto_transcrito)
                else:
                    st.success("✅ Transcripción completada exitosamente")
                    
                    with st.expander("📄 Leer texto completo extraído"):
                        st.text_area("", texto_transcrito, height=200)
                    
                    # C. ANÁLISIS CON LLAMA 3 (PROMPT INGENIERIL)
                    prompt_analisis = f"""
                    Eres un Analista de Inteligencia y Verificador de Datos (Fact-Checker).
                    Tu misión es analizar la siguiente transcripción de un video y generar un reporte estructurado.
                    
                    TRANSCRIPCIÓN DEL VIDEO:
                    '''{texto_transcrito}'''
                    
                    Instrucciones de salida (Usa Markdown):
                    1. 📝 **Resumen Ejecutivo**: De qué trata el video en 2 líneas.
                    2. 🔍 **Afirmaciones Clave**: Lista las 3-5 afirmaciones más importantes que hace el hablante.
                    3. ⚖️ **Veredicto de Veracidad**:
                       - Para cada afirmación, indica si parece: [Creíble], [Dudoso] o [Falso/Engañoso].
                       - Justifica tu respuesta usando lógica y conocimiento general.
                    4. 🚩 **Análisis de Sentimiento y Manipulación**: ¿El hablante usa lenguaje emocional, miedo o urgencia para manipular?
                    5. 💡 **Conclusión Final**: ¿Recomendarías confiar en este video?
                    """
                    
                    llm = obtener_ia()
                    if llm:
                        with st.spinner("🧠 Analizando patrones de engaño y lógica..."):
                            res = llm.invoke([HumanMessage(content=prompt_analisis)])
                            st.markdown("### 📊 Reporte de Análisis")
                            st.markdown(res.content)
                    else:
                        st.error("Error al conectar con el cerebro (Llama 3). Revisa tu API Key.")
                        
                        # ... (Código anterior de transcripción) ...

            # --- NUEVO BLOQUE: ANÁLISIS VISUAL DE FRAMES ---
            st.divider()
            st.subheader("👁️ Escáner Visual (Detección de Deepfake)")
            st.info("Este módulo analiza fotogramas clave del video buscando rastros de generación por IA.")
            
            if st.button("📸 Escanear Frames del Video", type="secondary"):
                # Importamos la nueva función aquí para usarla
                from app import analizar_frames_video
                
                # Rebobinamos el video otra vez
                video_file.seek(0)
                
                with st.spinner("Cortando frames y analizando píxeles... (Esto puede tardar un poco)"):
                    resultados_visuales = analizar_frames_video(video_file)
                
                # --- MOSTRAR RESULTADOS ---
                if not resultados_visuales:
                    st.error("No se pudieron extraer frames.")
                else:
                    # Contadores
                    total_frames = len(resultados_visuales)
                    ia_frames = sum(1 for r in resultados_visuales if r['etiqueta'] in ['artificial', 'AI'])
                    porcentaje_fake = (ia_frames / total_frames) * 100
                    
                    # Veredicto Visual
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Frames Analizados", total_frames)
                    col2.metric("Frames Sospechosos", ia_frames)
                    col3.metric("Probabilidad de Deepfake", f"{porcentaje_fake:.1f}%")
                    
                    if porcentaje_fake > 50:
                        st.error("🚨 ALERTA: La mayoría de los frames parecen generados por IA.")
                    elif porcentaje_fake > 20:
                        st.warning("⚠️ PRECAUCIÓN: Algunos frames tienen anomalías.")
                    else:
                        st.success("✅ El video parece visualmente auténtico.")
                    
                    # Detalles desplegables
                    with st.expander("Ver detalles por segundo"):
                        st.table(resultados_visuales)

# ==========================================
# PESTAÑA 3: CHAT GENERAL
# ==========================================
with tab_chat:
    st.subheader("💬 Chat con Llama 3")
    # (Aquí podrías poner tu lógica de chat simple si quieres)
    st.write("Usa este espacio para preguntas generales.")