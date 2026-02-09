import os
import cv2
import requests
import tempfile
import time
import shutil
import numpy as np
from langchain_groq import ChatGroq
from groq import Groq
from pydantic import SecretStr
from dotenv import load_dotenv
import yt_dlp

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip

load_dotenv()

TEMP_FOLDER = os.path.join(tempfile.gettempdir(), "verificador_ia_master")
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# --- IA Y BÚSQUEDA ---
def obtener_ia():
    clave = os.getenv("GROQ_API_KEY")
    if not clave: return None
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=SecretStr(clave))

def buscar_en_internet(consulta):
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key: return "⚠️ Error: Falta SERPER_API_KEY"
    url = "https://google.serper.dev/search"
    payload = {"q": consulta, "gl": "ve", "hl": "es", "num": 4}
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()
        fuentes = data.get('news', []) + data.get('organic', [])
        formato_texto = ""
        for res in fuentes[:4]:
            formato_texto += f"\n- 📰 {res.get('title')}\n  🔗 Link: {res.get('link')}\n"
        return formato_texto if formato_texto else "No se hallaron fuentes oficiales."
    except: return "Error en búsqueda."

# --- PROCESAMIENTO DE VIDEO ---

def descargar_desde_link(url):
    timestamp = int(time.time())
    filename = f"evidencia_{timestamp}.mp4"
    output_path = os.path.normpath(os.path.join(TEMP_FOLDER, filename))
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        return f"Error: {str(e)}"

# --- FUNCIÓN DE DETECCIÓN (URL ACTUALIZADA) ---
def detectar_imagen_ia(imagen_bytes):
    hf_token = os.getenv("HUGGINGFACE_API_KEY")
    
    # NUEVA URL DE LA INFRAESTRUCTURA ROUTER DE HUGGING FACE
    API_URL = "https://router.huggingface.co/hf-inference/models/umm-maybe/AI-image-detector"
    
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/octet-stream" 
    }
    
    try:
        # Aumentamos el timeout porque el router a veces tarda en redirigir
        response = requests.post(API_URL, headers=headers, data=imagen_bytes, timeout=25)
        
        if response.status_code != 200:
            print(f"❌ ERROR API ({response.status_code})")
            return {"error": response.status_code}
            
        return response.json()
    except Exception as e:
        print(f"❌ ERROR CONEXIÓN: {str(e)}")
        return {"error": "timeout"}

# --- PASO 1: FRAMES ---
def analizar_frames_video(video_path):
    print(f"🎬 [PASO 1] Analizando frames: {video_path}")
    video_path = os.path.normpath(video_path)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
        if not cap.isOpened(): return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames_a_saltar = int(fps * 2) 
    count, resultados = 0, []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or len(resultados) >= 6: break
        
        if count % frames_a_saltar == 0:
            print(f"📸 Procesando segundo: {round(count/fps, 1)}")
            success, buffer = cv2.imencode('.jpg', frame)
            if success:
                analisis = detectar_imagen_ia(buffer.tobytes())
                if isinstance(analisis, list) and len(analisis) > 0:
                    top = max(analisis, key=lambda x: x.get('score', 0))
                    resultados.append({
                        "segundo": round(count / fps, 1),
                        "etiqueta": top.get('label', 'unknown'),
                        "confianza": top.get('score', 0)
                    })
        count += 1
    
    cap.release()
    return resultados

# --- PASO 2: AUDIO ---
def extraer_audio(video_path):
    try:
        audio_path = video_path.rsplit('.', 1)[0] + ".mp3"
        video_temp_copy = video_path.replace(".mp4", "_audio_tmp.mp4")
        shutil.copy2(video_path, video_temp_copy)
        
        clip = VideoFileClip(video_temp_copy)
        clip.audio.write_audiofile(audio_path, bitrate="48k", logger=None)
        clip.audio.close()
        clip.close()
        
        if os.path.exists(video_temp_copy):
            os.remove(video_temp_copy)
        return audio_path
    except Exception as e:
        return f"Error audio: {str(e)}"

# --- PASO 3: TRANSCRIPCIÓN ---
def transcribir_audio(ruta_audio):
    clave = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=clave)
    try:
        with open(ruta_audio, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(ruta_audio), file.read()),
                model="whisper-large-v3", language="es"
            )
        return transcription.text
    except Exception as e:
        return f"Error Whisper: {str(e)}"

if __name__ == "__main__":
    print("🚀 Motor - Versión Router ONLINE")