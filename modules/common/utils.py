"""
Módulo de utilidades comunes para Credimax y Bankard.

Contiene funciones de utilidad general como conversión de DataFrames y manipulación de archivos.
"""

import io
import pandas as pd


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "base", header: bool = True) -> bytes:
    """
    Convierte un DataFrame de pandas a bytes de archivo Excel.
    
    Args:
        df: DataFrame a convertir
        sheet_name: Nombre de la hoja en el Excel
        header: Si incluir encabezados de columnas (True) o no (False)
        
    Returns:
        bytes: Contenido del archivo Excel en bytes
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name, header=header)
    buf.seek(0)
    return buf.read()


def ensure_column_from(df, target, sources=(), fill_value=""):
    """
    Asegura que existe una columna objetivo, creándola desde fuentes o con valor por defecto.
    
    Args:
        df: DataFrame a procesar
        target: Nombre de la columna objetivo
        sources: Lista de columnas fuente para buscar valores
        fill_value: Valor por defecto si no se encuentra en fuentes
        
    Returns:
        str: Nombre de la columna objetivo
    """
    if target in df.columns:
        return target
    
    for source in sources:
        if source in df.columns:
            df[target] = df[source]
            return target
    
    df[target] = fill_value
    return target


def procesar_archivo_excel_exclusiones(archivo_path, nombre_archivo):
    """
    Procesa un archivo Excel de exclusiones y extrae las cédulas.
    
    Args:
        archivo_path: Ruta al archivo Excel
        nombre_archivo: Nombre del archivo para mensajes de error
        
    Returns:
        tuple: (cedulas_set, error_message) o (None, error_message) si falla
    """
    from modules.common.validators import pad_10_digitos
    
    try:
        df_exc = pd.read_excel(archivo_path, dtype=str)
    except Exception as exc:
        return None, f"{nombre_archivo}: {exc}"
    
    if "IDENTIFICACION" not in df_exc.columns:
        return None, f"{nombre_archivo}: no contiene columna 'IDENTIFICACION'"
    
    cedulas = set(df_exc["IDENTIFICACION"].astype(str).apply(pad_10_digitos))
    return cedulas, None
