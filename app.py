import os
import cv2
import requests  # <--- IMPORTANTE: Asegúrate de tener esta librería
from langchain_groq import ChatGroq
from groq import Groq
from pydantic import SecretStr
from dotenv import load_dotenv
import tempfile
import numpy as np

# Cargar variables de entorno (.env)
load_dotenv()

# --- FUNCIÓN 1: OBTENER CEREBRO (CHAT) ---
def obtener_ia():
    clave = os.getenv("GROQ_API_KEY")
    if not clave: return None
    
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=SecretStr(clave)
    )

# --- FUNCIÓN 2 MEJORADA: OÍDO (TRANSCRIBIR VIDEO) ---
def transcribir_video(archivo_video):
    clave = os.getenv("GROQ_API_KEY")
    if not clave: return "Error: Falta la API Key de Groq."
    
    # Configuración del cliente con Timeout extendido
    client = Groq(api_key=clave, timeout=300.0)
    
    try:
        # Intentamos transcribir
        transcription = client.audio.transcriptions.create(
            file=(archivo_video.name, archivo_video.read()),
            model="whisper-large-v3",
            response_format="json", # Pedimos JSON puro
            language="es",          # Forzamos español para mejor precisión
            temperature=0.0         # Temperatura 0 para que no invente palabras
        )
        return transcription.text
    except Exception as e:
        # Capturamos errores específicos
        error_msg = str(e)
        if "413" in error_msg:
            return "Error: El archivo es demasiado grande (Máx 25MB)."
        elif "timeout" in error_msg.lower():
            return "Error: El video tardó demasiado en procesarse. Intenta con uno más corto."
        else:
            return f"Error desconocido en transcripción: {error_msg}"

# --- FUNCIÓN 3 CORREGIDA: DETECTAR IMAGEN IA ---
def detectar_imagen_ia(imagen_bytes):
    hf_token = os.getenv("HUGGINGFACE_API_KEY")
    
    if not hf_token:
        return {"error": "❌ No encontré la HUGGINGFACE_API_KEY en el archivo .env"}

    # URL Nueva (Router)
    API_URL = "https://router.huggingface.co/hf-inference/models/umm-maybe/AI-image-detector"
    
    # --- CAMBIO AQUÍ: AGREGAMOS 'Content-Type' ---
    # Le decimos al servidor: "Te estoy enviando datos binarios, no texto"
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/octet-stream" 
    }
    
    try:
        response = requests.post(API_URL, headers=headers, data=imagen_bytes)
        
        if response.status_code != 200:
            return {"error": f"Error de la API ({response.status_code}): {response.text}"}
            
        return response.json()
        
    except Exception as e:
        return {"error": f"Error crítico: {str(e)}"}
    
    #- FUNCIÓN 4: OJO DE AGUILA (FRAME POR FRAME) ---
def analizar_frames_video(archivo_video):
    # 1. Guardar el video temporalmente para que OpenCV pueda leerlo
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(archivo_video.read())
    video_path = tfile.name
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) # Cuadros por segundo
    if fps == 0: fps = 30 # Valor por defecto si falla
    
    intervalo_segundos = 2 # Analizar 1 frame cada 2 segundos
    frames_a_saltar = int(fps * intervalo_segundos)
    
    count = 0
    resultados = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break # Fin del video
        
        # Solo analizamos si toca el intervalo
        if count % frames_a_saltar == 0:
            # Convertir el frame de OpenCV a bytes (como si fuera un archivo jpg)
            _, buffer = cv2.imencode('.jpg', frame)
            bytes_imagen = buffer.tobytes()
            
            # --- LLAMAMOS A TU OTRA FUNCIÓN DE IMAGEN ---
            analisis = detectar_imagen_ia(bytes_imagen)
            
            # Guardamos resultado simple
            if isinstance(analisis, list):
                 top = max(analisis, key=lambda x: x['score'])
                 resultados.append({
                     "segundo": round(count / fps, 1),
                     "etiqueta": top['label'],
                     "confianza": top['score']
                 })
        
        count += 1
        
    cap.release()
    tfile.close() # Limpieza
    os.remove(video_path) # Borrar archivo temporal
    
    return resultados