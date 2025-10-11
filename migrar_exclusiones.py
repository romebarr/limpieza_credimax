#!/usr/bin/env python3
"""
Script de migración para consolidar archivos de exclusiones Excel
en el nuevo sistema JSON consolidado.

Uso:
    python migrar_exclusiones.py

Este script:
1. Lee todos los archivos Excel de data/exclusiones_bankard/
2. Extrae las cédulas de la columna IDENTIFICACION
3. Consolida todo en exclusiones_consolidadas.json
4. Muestra estadísticas del proceso
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Configuración
EXCLUSIONES_BANKARD_DIR = Path("data/exclusiones_bankard")
EXCLUSIONES_CONSOLIDADAS_PATH = Path("exclusiones_consolidadas.json")

def pad_10_digitos(valor):
    """Normaliza cédulas a 10 dígitos"""
    if pd.isna(valor):
        return ""
    import re
    s = re.sub(r"\D", "", str(valor))
    if s == "":
        return ""
    if len(s) < 10:
        s = s.zfill(10)
    elif len(s) > 10:
        s = s[:10]
    return s

def cargar_exclusiones_consolidadas():
    """Carga el archivo JSON consolidado existente"""
    if EXCLUSIONES_CONSOLIDADAS_PATH.exists():
        try:
            with open(EXCLUSIONES_CONSOLIDADAS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("cedulas_excluidas", {}), data.get("estadisticas", {})
        except (json.JSONDecodeError, KeyError):
            return {}, {}
    return {}, {}

def guardar_exclusiones_consolidadas(cedulas_data, estadisticas):
    """Guarda las exclusiones consolidadas en JSON"""
    data = {
        "cedulas_excluidas": cedulas_data,
        "estadisticas": estadisticas
    }
    with open(EXCLUSIONES_CONSOLIDADAS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def procesar_archivo_exclusiones(archivo_path, cedulas_consolidadas, estadisticas):
    """Procesa un archivo de exclusiones"""
    try:
        df_exc = pd.read_excel(archivo_path, dtype=str)
    except Exception as exc:
        return False, f"Error leyendo archivo: {exc}"
    
    if "IDENTIFICACION" not in df_exc.columns:
        return False, "No contiene columna 'IDENTIFICACION'"
    
    cedulas_nuevas = 0
    cedulas_actualizadas = 0
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    
    for cedula_raw in df_exc["IDENTIFICACION"].dropna():
        cedula = pad_10_digitos(cedula_raw)
        if not cedula:
            continue
            
        if cedula not in cedulas_consolidadas:
            cedulas_consolidadas[cedula] = {
                "fecha_agregada": fecha_actual,
                "fuente": archivo_path.name,
                "activa": True
            }
            cedulas_nuevas += 1
        else:
            # Actualizar fecha si ya existe
            cedulas_consolidadas[cedula]["fecha_agregada"] = fecha_actual
            cedulas_consolidadas[cedula]["fuente"] = archivo_path.name
            cedulas_actualizadas += 1
    
    return True, f"Procesado: {cedulas_nuevas} nuevas, {cedulas_actualizadas} actualizadas"

def main():
    print("🔄 Iniciando migración de exclusiones...")
    print(f"📁 Directorio fuente: {EXCLUSIONES_BANKARD_DIR}")
    print(f"💾 Archivo destino: {EXCLUSIONES_CONSOLIDADAS_PATH}")
    print("-" * 50)
    
    # Verificar directorio
    if not EXCLUSIONES_BANKARD_DIR.exists():
        print(f"❌ Error: El directorio {EXCLUSIONES_BANKARD_DIR} no existe")
        print("   Crea el directorio y coloca tus archivos Excel ahí")
        return False
    
    # Cargar datos existentes
    cedulas_consolidadas, estadisticas = cargar_exclusiones_consolidadas()
    print(f"📊 Cédulas existentes en sistema: {len(cedulas_consolidadas)}")
    
    # Procesar archivos
    archivos_procesados = 0
    errores = []
    archivos_excel = list(EXCLUSIONES_BANKARD_DIR.glob("*.xlsx"))
    
    if not archivos_excel:
        print("⚠️  No se encontraron archivos Excel en el directorio")
        return False
    
    print(f"📋 Encontrados {len(archivos_excel)} archivos Excel")
    print("-" * 50)
    
    for i, archivo in enumerate(archivos_excel, 1):
        if archivo.name.startswith("~$"):
            continue
            
        print(f"[{i:3d}/{len(archivos_excel)}] Procesando: {archivo.name}")
        
        success, message = procesar_archivo_exclusiones(archivo, cedulas_consolidadas, estadisticas)
        if success:
            archivos_procesados += 1
            print(f"    ✅ {message}")
        else:
            errores.append(f"{archivo.name}: {message}")
            print(f"    ❌ {message}")
    
    # Actualizar estadísticas
    estadisticas["total_cedulas"] = len(cedulas_consolidadas)
    estadisticas["ultima_actualizacion"] = datetime.now().isoformat()
    estadisticas["archivos_procesados"] = estadisticas.get("archivos_procesados", 0) + archivos_procesados
    
    # Guardar resultados
    guardar_exclusiones_consolidadas(cedulas_consolidadas, estadisticas)
    
    # Mostrar resumen
    print("-" * 50)
    print("📊 RESUMEN DE MIGRACIÓN")
    print("-" * 50)
    print(f"✅ Archivos procesados: {archivos_procesados}")
    print(f"❌ Errores: {len(errores)}")
    print(f"📋 Total cédulas consolidadas: {len(cedulas_consolidadas)}")
    print(f"💾 Archivo guardado: {EXCLUSIONES_CONSOLIDADAS_PATH}")
    
    if errores:
        print("\n⚠️  ERRORES ENCONTRADOS:")
        for error in errores:
            print(f"   • {error}")
    
    print("\n🎉 ¡Migración completada!")
    print("💡 Ahora puedes usar el sistema consolidado en la aplicación Streamlit")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Migración cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
