import os
from langchain_groq import ChatGroq
from groq import Groq
from pydantic import SecretStr
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def obtener_ia():
    # 1. Obtener la clave
    clave = os.getenv("GROQ_API_KEY")
    # 2. Si no hay clave, no devolvemos nada
    if not clave:
        return None
    # 3. Devolver la IA configurada (usando SecretStr para evitar el error de tipo)
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=SecretStr(clave)
    )
# 2. NUEVA FUNCIÓN: Transcribir Video/Audio
def transcribir_video(archivo_video):
    clave = os.getenv("GROQ_API_KEY")
    if not clave: return None
    
    # Cliente directo de Groq para audio
    client = Groq(api_key=clave, timeout=300.0)
    
    try:
        # Usamos el modelo Whisper v3 (¡Es rapidísimo!)
        transcription = client.audio.transcriptions.create(
            file=(archivo_video.name, archivo_video.read()), # Le pasamos el archivo
            model="whisper-large-v3", # Modelo experto en oír
            response_format="json",
            language="es", # Forzamos español (o borra esto para auto-detectar)
            temperature=0.0
        )
        return transcription.text
    except Exception as e:
        return f"Error en la transcripción: {str(e)}"