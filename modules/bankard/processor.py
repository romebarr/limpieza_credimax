"""
Módulo de procesamiento de datos para Bankard.

Contiene la lógica principal de procesamiento y segmentación de datos Bankard.
"""

import io
import zipfile
import pandas as pd
import numpy as np
from datetime import datetime

from modules.common.formatters import safe_filename
from modules.common.utils import df_to_excel_bytes


def preparar_zip_bankard(df, col_tipo="TIPO ", col_exclusion="exclusion"):
    """
    Genera un archivo ZIP con archivos Excel segmentados por tipo y exclusión para Bankard.
    
    Esta función:
    1. Filtra registros con exclusion = "NO" (sin exclusión)
    2. Agrupa por tipo de tarjeta y genera un archivo Excel por cada tipo
    3. Aplica mapeo de columnas para estandarizar nombres
    4. Formatea valores (cupos con comas)
    
    Args:
        df: DataFrame con los datos de Bankard
        col_tipo: Nombre de la columna que contiene los tipos
        col_exclusion: Nombre de la columna de exclusión
        
    Returns:
        tuple: (bytes_zip, columnas_exportadas) o (None, []) si no hay datos
    """
    # Asegurar que existen las columnas necesarias
    if col_tipo not in df.columns:
        df[col_tipo] = "SIN_TIPO"
    if col_exclusion not in df.columns:
        df[col_exclusion] = "NO"

    # Filtrar solo registros sin exclusión
    df_filtrado = df[df[col_exclusion] == "NO"].copy()
    
    if df_filtrado.empty:
        return None, []

    # Mapeo de columnas para estandarizar nombres
    mapeo_columnas = {
        "primer_nombre": "nombre",
        "Nombres": "nombre", 
        "telefono": "telefono",
        "cedula": "cedula",
        "cupo": "cupo_aprobado",
        "BIN": "marca_tarjeta",
        col_tipo: "tipo_tarjeta"
    }

    # Aplicar mapeo de columnas
    for col_original, col_nueva in mapeo_columnas.items():
        if col_original in df_filtrado.columns:
            df_filtrado[col_nueva] = df_filtrado[col_original]

    # Seleccionar columnas finales
    columnas_finales = [
        "nombre", "telefono", "cedula", "cupo_aprobado", 
        "marca_tarjeta", "tipo_tarjeta"
    ]
    
    # Asegurar que todas las columnas existen
    for col in columnas_finales:
        if col not in df_filtrado.columns:
            df_filtrado[col] = ""

    df_final = df_filtrado[columnas_finales].copy()

    # Agrupar por tipo de tarjeta
    grupos = df_final.groupby("tipo_tarjeta")

    zip_buf = io.BytesIO()
    archivos_generados = []
    hoy_str = datetime.now().strftime("%Y%m%d")

    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for tipo, grupo in grupos:
            if grupo.empty:
                continue

            # Limpiar nombre de archivo
            nombre_tipo = safe_filename(tipo) or "SIN_TIPO"
            nombre_archivo_excel = f"Bankard_{nombre_tipo}_{hoy_str}.xlsx"

            # Convertir a bytes
            excel_bytes = df_to_excel_bytes(grupo, sheet_name="base")
            zf.writestr(nombre_archivo_excel, excel_bytes)
            archivos_generados.append(nombre_archivo_excel)

    if not archivos_generados:
        return None, []

    zip_buf.seek(0)
    return zip_buf.read(), archivos_generados
