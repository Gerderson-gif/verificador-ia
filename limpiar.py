import site
import shutil
import os
from pathlib import Path

def limpiar_basura_pip():
    # 1. Obtener la ruta donde se instalan las librerías
    site_packages = site.getsitepackages()[0]
    # A veces en Windows es la segunda ruta (user site)
    if "site-packages" not in site_packages:
        for path in site.getsitepackages():
            if "site-packages" in path:
                site_packages = path
                break
    
    print(f"🧹 Buscando basura en: {site_packages}")
    
    contador = 0
    p = Path(site_packages)
    
    # 2. Buscar carpetas que empiecen con '~'
    for item in p.iterdir():
        if item.is_dir() and item.name.startswith('~'):
            print(f"🗑️ Eliminando carpeta corrupta: {item.name}")
            try:
                shutil.rmtree(item)
                contador += 1
            except Exception as e:
                print(f"❌ No se pudo borrar {item.name}: {e}")
                
    if contador == 0:
        print("✨ Tu entorno de Python está limpio. No se encontró basura.")
    else:
        print(f"✅ Se eliminaron {contador} carpetas corruptas.")

if __name__ == "__main__":
    try:
        limpiar_basura_pip()
    except Exception as e:
        print(f"Error: {e}")
    input("\nPresiona ENTER para salir...")