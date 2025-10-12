"""
Módulo de gestión de exclusiones para Bankard.

Contiene la funcionalidad para cargar, procesar y gestionar exclusiones de cédulas.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime


def cargar_cedulas_excluir_uploads(files):
    """
    Carga cédulas de exclusión desde archivos subidos por el usuario.
    
    Args:
        files: Lista de archivos subidos (Streamlit file uploader)
        
    Returns:
        tuple: (set_cedulas, lista_errores)
    """
    from modules.common.validators import pad_10_digitos
    from modules.common.utils import procesar_archivo_excel_exclusiones
    
    cedulas = set()
    errores = []
    for upload in files or []:
        try:
            upload.seek(0)
        except Exception:
            pass
        
        cedulas_archivo, error = procesar_archivo_excel_exclusiones(upload, upload.name)
        if error:
            errores.append(error)
        else:
            cedulas.update(cedulas_archivo)
    
    return cedulas, errores


def cargar_exclusiones_consolidadas():
    """
    Carga el archivo JSON consolidado de exclusiones.
    
    Returns:
        tuple: (cedulas_excluidas, estadisticas)
    """
    EXCLUSIONES_CONSOLIDADAS_PATH = Path("exclusiones_consolidadas.json")
    
    if EXCLUSIONES_CONSOLIDADAS_PATH.exists():
        try:
            with open(EXCLUSIONES_CONSOLIDADAS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("cedulas_excluidas", {}), data.get("estadisticas", {})
        except (json.JSONDecodeError, KeyError):
            return {}, {}
    return {}, {}


def guardar_exclusiones_consolidadas(cedulas_data, estadisticas):
    """
    Guarda exclusiones consolidadas en archivo JSON.
    
    Args:
        cedulas_data: Diccionario con datos de cédulas
        estadisticas: Diccionario con estadísticas
    """
    EXCLUSIONES_CONSOLIDADAS_PATH = Path("exclusiones_consolidadas.json")
    
    data = {
        "cedulas_excluidas": cedulas_data,
        "estadisticas": estadisticas,
        "ultima_actualizacion": datetime.now().isoformat()
    }
    
    with open(EXCLUSIONES_CONSOLIDADAS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def procesar_archivo_exclusiones(archivo_path, cedulas_consolidadas, estadisticas):
    """
    Procesa un archivo de exclusiones y actualiza la base consolidada.
    
    Args:
        archivo_path: Ruta al archivo a procesar
        cedulas_consolidadas: Diccionario de cédulas consolidadas
        estadisticas: Diccionario de estadísticas
        
    Returns:
        tuple: (success, message)
    """
    from modules.common.validators import pad_10_digitos
    
    try:
        df = pd.read_excel(archivo_path, dtype=str)
    except Exception as e:
        return False, f"Error al leer archivo: {e}"
    
    if "IDENTIFICACION" not in df.columns:
        return False, "Archivo no contiene columna 'IDENTIFICACION'"
    
    cedulas_nuevas = 0
    cedulas_actualizadas = 0
    
    for cedula in df["IDENTIFICACION"]:
        cedula_limpia = pad_10_digitos(cedula)
        if cedula_limpia and cedula_limpia not in cedulas_consolidadas:
            cedulas_consolidadas[cedula_limpia] = {
                "fecha_agregada": datetime.now().isoformat(),
                "archivo_origen": str(archivo_path)
            }
            cedulas_nuevas += 1
        elif cedula_limpia in cedulas_consolidadas:
            cedulas_actualizadas += 1
    
    # Actualizar estadísticas
    estadisticas["total_cedulas"] = len(cedulas_consolidadas)
    estadisticas["ultima_actualizacion"] = datetime.now().isoformat()
    estadisticas["archivos_procesados"] = estadisticas.get("archivos_procesados", 0) + 1
    
    return True, f"Procesado: {cedulas_nuevas} nuevas, {cedulas_actualizadas} actualizadas"


def cargar_cedulas_excluir_directorio(path: Path):
    """
    Carga exclusiones desde archivos Excel en un directorio (método legacy).
    
    Args:
        path: Ruta al directorio con archivos Excel
        
    Returns:
        tuple: (set_cedulas, lista_errores, lista_archivos_procesados)
    """
    from modules.common.utils import procesar_archivo_excel_exclusiones
    
    cedulas = set()
    errores = []
    archivos = []
    if not path.exists():
        return cedulas, errores, archivos

    for archivo in path.glob("*.xlsx"):
        if archivo.name.startswith("~$"):
            continue
        
        cedulas_archivo, error = procesar_archivo_excel_exclusiones(archivo, archivo.name)
        if error:
            errores.append(error)
        else:
            cedulas.update(cedulas_archivo)
            archivos.append(archivo.name)

    return cedulas, errores, archivos


def consolidar_exclusiones_desde_directorio():
    """
    Consolida todos los archivos Excel en el JSON consolidado.
    
    Returns:
        tuple: (success, message)
    """
    EXCLUSIONES_BANKARD_DIR = Path("data/exclusiones_bankard")
    
    cedulas_consolidadas, estadisticas = cargar_exclusiones_consolidadas()
    
    cedulas_directorio, errores, archivos = cargar_cedulas_excluir_directorio(EXCLUSIONES_BANKARD_DIR)
    
    cedulas_nuevas = 0
    for cedula in cedulas_directorio:
        if cedula not in cedulas_consolidadas:
            cedulas_consolidadas[cedula] = {
                "fecha_agregada": datetime.now().isoformat(),
                "archivo_origen": "directorio_consolidado"
            }
            cedulas_nuevas += 1
    
    # Actualizar estadísticas
    estadisticas["total_cedulas"] = len(cedulas_consolidadas)
    estadisticas["ultima_actualizacion"] = datetime.now().isoformat()
    estadisticas["archivos_procesados"] = estadisticas.get("archivos_procesados", 0) + 1
    
    # Guardar consolidado
    guardar_exclusiones_consolidadas(cedulas_consolidadas, estadisticas)
    
    return True, f"Procesado: {cedulas_nuevas} nuevas, {cedulas_actualizadas} actualizadas"


def marcar_exclusiones_varios(df, cedulas_excluir):
    """
    Marca registros como excluidos basado en lista de cédulas.
    
    Args:
        df: DataFrame a procesar
        cedulas_excluir: Set de cédulas a excluir
        
    Returns:
        DataFrame: DataFrame con columna de exclusión marcada
    """
    from modules.common.validators import pad_10_digitos
    
    df = df.copy()
    
    # Asegurar que existe la columna de exclusión
    if "exclusion" not in df.columns:
        df["exclusion"] = "NO"
    
    # Marcar exclusiones
    if "cedula" in df.columns:
        df["exclusion"] = df["cedula"].apply(
            lambda x: "SI" if pad_10_digitos(x) in cedulas_excluir else "NO"
        )
    
    return df
