import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from app import obtener_ia, transcribir_video # <--- IMPORTAMOS LA NUEVA FUNCIÓN

st.set_page_config(page_title="SIMAMUL", page_icon="🕵️", layout="centered")

# Estilos CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("🕵️ SIMAMUL: Análisis de Video")
st.caption("Sube un video para detectar falacias, mentiras o resumir contenido.")

# --- BARRA LATERAL PARA SUBIR VIDEO ---
with st.sidebar:
    st.header("📂 Cargar Video")
    video_file = st.file_uploader("Sube tu MP4 (Máx 25MB)", type=["mp4", "mov", "avi"])
    
    if video_file:
        st.video(video_file) # Previsualizar video
        boton_analizar = st.button("🔍 Transcribir y Analizar", type="primary")

# --- LÓGICA DE ANÁLISIS DE VIDEO ---
if video_file and "boton_analizar" in locals() and boton_analizar:
    with st.spinner("🎧 Escuchando el video (Transcribiendo)..."):
        texto_transcrito = transcribir_video(video_file)
    
    if "Error" in texto_transcrito:
        st.error(texto_transcrito)
    else:
        st.success("✅ Video transcrito exitosamente")
        
        # Mostrar la transcripción en un desplegable
        with st.expander("Ver Transcripción Completa"):
            st.write(texto_transcrito)
        
        # PROMPT DE VERIFICACIÓN
        # Aquí es donde ocurre la magia: Le decimos a la IA qué hacer con el texto
        prompt_analisis = f"""
        Actúa como un experto verificador de hechos (Fact-Checker) y analista de discurso.
        Analiza la siguiente transcripción de un video:
        
        '''{texto_transcrito}'''
        
        Tu tarea es:
        1. Resumir brevemente de qué trata.
        2. Extraer las afirmaciones principales.
        3. Evaluar la veracidad de esas afirmaciones basándote en tu conocimiento (lógica, ciencia, historia).
        4. Detectar si hay tono manipulador, falacias lógicas o intentos de estafa.
        5. Dar un veredicto final: ¿Es confiable esta información?
        """
        
        # Enviamos a la IA
        llm = obtener_ia()
        with st.spinner("🧠 Analizando la verdad..."):
            respuesta = llm.invoke([HumanMessage(content=prompt_analisis)])
            st.write(respuesta.content)
            
            # Guardamos en el historial por si quieres hacerle preguntas sobre el video
            if "mensajes" not in st.session_state: st.session_state.mensajes = []
            st.session_state.mensajes.append(HumanMessage(content=f"He subido un video. Transcripción: {texto_transcrito}"))
            st.session_state.mensajes.append(respuesta)

# --- CHAT NORMAL (Debajo del análisis) ---
st.divider()
st.subheader("💬 Chat sobre el video")

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

for mensaje in st.session_state.mensajes:
    if isinstance(mensaje, HumanMessage):
        with st.chat_message("user"): st.write(mensaje.content)
    elif isinstance(mensaje, AIMessage):
        with st.chat_message("assistant"): st.write(mensaje.content)

prompt = st.chat_input("Pregunta algo sobre el video o cualquier otro tema...")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.mensajes.append(HumanMessage(content=prompt))
    
    llm = obtener_ia()
    if llm:
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                respuesta = llm.invoke(st.session_state.mensajes)
                st.write(respuesta.content)
                st.session_state.mensajes.append(respuesta)