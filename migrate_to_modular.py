"""
Script de migración para reemplazar app.py con la versión modularizada.

Este script hace backup del app.py original y lo reemplaza con la versión modularizada.
"""

import shutil
from datetime import datetime
import os

def migrate_to_modular():
    """
    Migra de app.py a la versión modularizada.
    """
    # Crear backup del archivo original
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"app_original_backup_{timestamp}.py"
    
    if os.path.exists("app.py"):
        shutil.copy2("app.py", backup_name)
        print(f"✅ Backup creado: {backup_name}")
    
    # Reemplazar app.py con la versión modularizada
    if os.path.exists("app_modular.py"):
        shutil.copy2("app_modular.py", "app.py")
        print("✅ app.py reemplazado con versión modularizada")
        
        # Limpiar archivo temporal
        os.remove("app_modular.py")
        print("✅ Archivo temporal limpiado")
        
        return True
    else:
        print("❌ No se encontró app_modular.py")
        return False

if __name__ == "__main__":
    print("🔄 Iniciando migración a versión modularizada...")
    success = migrate_to_modular()
    
    if success:
        print("🎉 Migración completada exitosamente!")
        print("📁 El archivo original se guardó como backup")
        print("🚀 Ahora puedes ejecutar: streamlit run app.py")
    else:
        print("❌ La migración falló")
