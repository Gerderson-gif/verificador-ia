import site
import shutil
import os
import sys
from pathlib import Path

def limpiar_basura_pip():
    # 1. Identificar si estamos en un entorno virtual o en el sistema global
    if hasattr(sys, 'real_prefix') or (sys.base_prefix != sys.prefix):
        # Estamos en un VENV
        site_packages_list = [p for p in sys.path if "site-packages" in p and "venv" in p.lower()]
    else:
        # Estamos en el Python global
        site_packages_list = site.getsitepackages()

    if not site_packages_list:
        print("❌ No se pudo localizar la carpeta site-packages.")
        return

    # Usamos la primera coincidencia válida
    site_packages = site_packages_list[0]
    print(f"🔍 Escaneando dependencias en: {site_packages}")
    
    contador = 0
    p = Path(site_packages)
    
    # 2. Buscar carpetas que empiecen con '~' (Basura de instalaciones fallidas)
    # También buscamos carpetas '.tmp' que a veces deja pip
    try:
        for item in p.iterdir():
            if item.is_dir() and (item.name.startswith('~') or item.name.endswith('.tmp')):
                print(f"🗑️ Eliminando rastro corrupto: {item.name}")
                try:
                    shutil.rmtree(item)
                    contador += 1
                except PermissionError:
                    print(f"⚠️ Permiso denegado para {item.name}. Asegúrate de que no haya un programa usando la librería.")
                except Exception as e:
                    print(f"❌ Error inesperado en {item.name}: {e}")
                    
        if contador == 0:
            print("✨ ¡Perfecto! Tu entorno de Python está libre de carpetas huérfanas.")
        else:
            print(f"✅ Limpieza completada. Se eliminaron {contador} elementos.")
            
    except FileNotFoundError:
        print(f"❌ La ruta no existe: {site_packages}")

if __name__ == "__main__":
    print("--- UTILIDAD DE MANTENIMIENTO PIP ---")
    try:
        limpiar_basura_pip()
    except Exception as e:
        print(f"🔴 Error crítico: {e}")
    
    print("\n" + "="*30)
    input("Presiona ENTER para finalizar...")