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
