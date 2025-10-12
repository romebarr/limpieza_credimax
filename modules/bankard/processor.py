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

    # Mapeo de columnas para Bankard (incluye variantes para No Clientes)
    mapeo_columnas_bankard = {
        "primer_nombre": "primer_nombre_bankard",
        "Nombres": "primer_nombre_bankard",  # Para archivos No Clientes
        "cupo": "Cupo_Aprobado_OB_BK", 
        "BIN": "Marca_BK_OB",
        "correo": "correo",
        "CORREO BANCO ": "correo",  # Para archivos No Clientes
        "telefono": "telefono"
    }

    # Aplicar mapeo de columnas
    for col_original, col_nueva in mapeo_columnas_bankard.items():
        if col_original in df_filtrado.columns:
            df_filtrado[col_nueva] = df_filtrado[col_original]

    # Columnas finales que se exportarán (incluyendo la columna de tipo para agrupación)
    columnas_finales = [
        "primer_nombre_bankard",
        "Cupo_Aprobado_OB_BK",
        "Marca_BK_OB", 
        "correo",
        "telefono",
        col_tipo  # Incluir la columna de tipo para poder agrupar
    ]
    
    # Asegurar que todas las columnas existen
    for col in columnas_finales:
        if col not in df_filtrado.columns:
            df_filtrado[col] = ""

    df_final = df_filtrado[columnas_finales].copy()
    
    # Formatear cupos con separadores de miles
    if "Cupo_Aprobado_OB_BK" in df_final.columns:
        def formatear_cupo(valor):
            if pd.isna(valor) or valor == "" or valor == "nan":
                return "0"
            try:
                # Convertir a número y formatear con comas
                cupo_num = int(float(str(valor)))
                return f"{cupo_num:,}"
            except (ValueError, TypeError):
                return "0"
        
        df_final["Cupo_Aprobado_OB_BK"] = df_final["Cupo_Aprobado_OB_BK"].apply(formatear_cupo)

    # Agrupar por tipo de tarjeta (usar la columna original)
    grupos = df_final.groupby(col_tipo)

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

            # Excluir la columna de tipo del archivo Excel final
            columnas_exportar = [col for col in grupo.columns if col != col_tipo]
            grupo_exportar = grupo[columnas_exportar].copy()

            # Convertir a bytes
            excel_bytes = df_to_excel_bytes(grupo_exportar, sheet_name="base")
            zf.writestr(nombre_archivo_excel, excel_bytes)
            archivos_generados.append(nombre_archivo_excel)

    if not archivos_generados:
        return None, []

    zip_buf.seek(0)
    return zip_buf.read(), archivos_generados
