import streamlit as st
import os
import re
import io
import datetime # IMPORTANTE: Para saber la fecha de hoy
from dotenv import load_dotenv

# 1. Configuración de la Página
st.set_page_config(page_title="Verificador IA (En Vivo)", page_icon="📡")

# 2. Cargar Claves
load_dotenv()

# --- FUNCIONES LÓGICAS ---

@st.cache_resource
def obtener_ia():
    from langchain_groq import ChatGroq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("❌ Falta la GROQ_API_KEY en el archivo .env")
        return None
    # Usamos Llama 3.3 Versatile
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0, groq_api_key=api_key)

def buscar_en_duckduckgo_directo(consulta):
    try:
        from duckduckgo_search import DDGS
        # Buscamos noticias (region='wt-wt' es mundial, timelimit='d' es último día, 'm' mes)
        # Quitamos timelimit para que busque en general pero priorice relevancia
        with DDGS() as ddgs:
            return list(ddgs.text(keywords=consulta, max_results=6))
    except ImportError:
        return "Error: Librería duckduckgo-search no instalada."
    except Exception as e:
        return f"Error en búsqueda: {e}"

def limpiar_texto_para_pdf(texto):
    if not texto: return ""
    texto = texto.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    texto = texto.replace('"', '&quot;').replace("'", '&apos;')
    texto = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)
    return texto

def generar_pdf_en_memoria(texto_resultado):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfgen import canvas

    def on_page_watermark(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 60)
        canvas.setStrokeColorRGB(0.9, 0.9, 0.9)
        canvas.setFillColorRGB(0.9, 0.9, 0.9)
        canvas.translate(letter[0]/2, letter[1]/2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "VERIFICADO POR IA")
        canvas.restoreState()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    estilos = getSampleStyleSheet()
    estilo_cuerpo = ParagraphStyle('Cuerpo', parent=estilos['Normal'], spaceAfter=12, leading=15)
    
    contenido = []
    contenido.append(Paragraph("<b>Reporte de Verificación</b>", estilos['Title']))
    contenido.append(Spacer(1, 12))
    
    for linea in texto_resultado.split('\n'):
        linea = linea.strip()
        if linea:
            linea_segura = limpiar_texto_para_pdf(linea)
            try:
                p = Paragraph(linea_segura, estilo_cuerpo)
                contenido.append(p)
            except:
                p = Paragraph(linea.replace('<',''), estilo_cuerpo)
                contenido.append(p)

    doc.build(contenido, onFirstPage=on_page_watermark, onLaterPages=on_page_watermark)
    buffer.seek(0)
    return buffer

def ejecutar_verificacion(pregunta):
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    llm = obtener_ia()
    if not llm: return None, None
    
    # 1. Búsqueda
    raw_results = buscar_en_duckduckgo_directo(pregunta)
    
    # 2. Construir contexto visible
    contexto = ""
    if isinstance(raw_results, list):
        for res in raw_results:
            titulo = res.get('title', 'Sin título')
            link = res.get('href', 'Sin link')
            cuerpo = res.get('body', 'Sin info')
            contexto += f"NOTICIA: {titulo}\nCONTENIDO: {cuerpo}\nENLACE: {link}\n---\n"
    else:
        contexto = str(raw_results)
    
    # 3. Fecha Actual
    fecha_hoy = datetime.datetime.now().strftime("%d de %B de %Y")
    
    # 4. Prompt Agresivo (Instruye ignorar conocimiento interno)
    SYSTEM_PROMPT = f"""
    FECHA ACTUAL: {fecha_hoy}
    
    Eres un Analista de Inteligencia. Tu trabajo NO es usar tu memoria. Tu trabajo es LEER el 'CONTEXTO WEB' y responder basándote SOLO en eso.
    
    REGLA DE ORO: Si tu memoria interna dice que algo pasó en 2023, pero el CONTEXTO WEB dice que cambió en 2025 o 2026, CREÉLE AL CONTEXTO WEB.
    
    INSTRUCCIONES:
    1. Lee las noticias proporcionadas abajo.
    2. Si las noticias confirman el hecho, di VERDADERO.
    3. Si las noticias lo niegan, di FALSO.
    4. Si no hay noticias relacionadas en el contexto, di "NO HAY INFORMACIÓN RECIENTE DISPONIBLE" (No uses tu memoria).
    5. CITA LAS FUENTES CON SUS LINKS.
    
    CONTEXTO WEB (Información en tiempo real):
    {contexto}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "Afirmación a investigar: {question}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    respuesta_ia = chain.invoke({"question": pregunta})
    
    return respuesta_ia, contexto # Devolvemos también el contexto para mostrarlo

# --- INTERFAZ GRÁFICA ---

st.title("📡 Verificador En Tiempo Real")
st.markdown(f"**Fecha del sistema:** {datetime.datetime.now().strftime('%Y-%m-%d')}")

pregunta_usuario = st.text_area("Escribe el dato a verificar:", placeholder="Ej: ¿Quién ganó las elecciones de X país en 2025?")

if st.button("🔍 Investigar Ahora", type="primary"):
    if not pregunta_usuario:
        st.warning("Escribe algo primero.")
    else:
        with st.spinner('Rastreando información en la web...'):
            try:
                # Obtenemos respuesta IA + Evidencia cruda
                resultado_texto, evidencia_cruda = ejecutar_verificacion(pregunta_usuario)
                
                if resultado_texto:
                    st.session_state['resultado'] = resultado_texto
                    st.session_state['evidencia'] = evidencia_cruda
                    st.success("Análisis finalizado.")
            except Exception as e:
                st.error(f"Error: {e}")

# Verificamos que existan AMBAS cosas antes de intentar mostrarlas
if 'resultado' in st.session_state and 'evidencia' in st.session_state:
    st.divider()
    
    # SECCIÓN DE DEBUG (Evidencia Cruda)
    with st.expander("👁️ Ver lo que la IA encontró en Internet (Evidencia Cruda)"):
        st.text(st.session_state['evidencia'])
    
    st.subheader("Resultados del Análisis")
    st.write(st.session_state['resultado'])
    
    st.divider()
    
    # Generar el PDF
    if st.download_button(
        label="📄 Generar PDF",
        data=generar_pdf_en_memoria(st.session_state['resultado']),
        file_name="reporte_live.pdf",
        mime="application/pdf"
    ):
        st.toast("PDF Generado")