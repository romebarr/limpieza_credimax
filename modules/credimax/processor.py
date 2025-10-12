"""
Módulo de procesamiento de datos para Credimax.

Contiene la lógica principal de procesamiento y segmentación de datos Credimax.
"""

import io
import zipfile
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

from modules.common.formatters import formatear_cuota, safe_filename
from modules.common.utils import df_to_excel_bytes


def preparar_zip_por_campana(df: pd.DataFrame, col_campana: str = "Campaña Growth"):
    """
    Genera un archivo ZIP con archivos Excel segmentados por campaña para Credimax.
    
    Esta función:
    1. Filtra registros con IND_DESEMBOLSO = "0" (sin desembolso)
    2. Agrupa por campaña y genera un archivo Excel por cada campaña
    3. Aplica mapeo de columnas para estandarizar nombres
    4. Formatea valores (cupos con comas, cuotas con decimales)
    
    Args:
        df: DataFrame con los datos de Credimax
        col_campana: Nombre de la columna que contiene las campañas
        
    Returns:
        tuple: (bytes_zip, columnas_exportadas) o (None, []) si no hay datos
    """
    columnas_necesarias = {
        col_campana,
        "IND_DESEMBOLSO",
        "CELULAR",
        "primer_nombre",
        "CORREO CLIENTE",
        "CUPO",
        "CUOTA",
        "Tasa",
        "CUPO_TARJETA_BK",
        "MARCA_TARJETA_BK",
    }

    df_trabajo = df.copy()
    for col in columnas_necesarias:
        if col not in df_trabajo.columns:
            df_trabajo[col] = np.nan

    df_exp = df_trabajo[df_trabajo["IND_DESEMBOLSO"] == "0"].copy()
    df_exp[col_campana] = df_exp[col_campana].astype(str).str.strip()
    mask_no_vacio = (
        df_exp[col_campana].notna()
        & (df_exp[col_campana] != "")
        & (~df_exp[col_campana].str.lower().eq("nan"))
    )
    df_exp = df_exp[mask_no_vacio].copy()

    if df_exp.empty:
        return None, []

    # Mapeo columnas de salida (primer_nombre => nombre)
    mapeo_columnas = {
        "primer_nombre": "nombre",             # <- solicitado
        "CORREO CLIENTE": "correo",
        "CUPO": "monto_credito_aprob",
        "CUOTA": "cuota_credimax",
        "Tasa": "Tasa_Credito_Aprob",
        "CUPO_TARJETA_BK": "Cupo_Aprobado_OB_BK",
        "MARCA_TARJETA_BK": "Marca_BK_OB",
    }

    df_exp["CUOTA"] = df_exp["CUOTA"].apply(formatear_cuota)

    columnas_originales = list(mapeo_columnas.keys()) + [col_campana, "CELULAR"]
    df_exp = df_exp[columnas_originales].copy()

    # Renombrar columnas
    df_exp = df_exp.rename(columns=mapeo_columnas)

    # Agrupar por campaña
    grupos = df_exp.groupby(col_campana)

    zip_buf = io.BytesIO()
    archivos_generados = []
    hoy_str = datetime.now().strftime("%Y%m%d")

    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for nombre_campana, grupo in grupos:
            if grupo.empty:
                continue

            # Limpiar nombre de archivo
            nombre_archivo = safe_filename(nombre_campana) or "SIN_CAMPANA"
            nombre_archivo_excel = f"Credimax_{nombre_archivo}_{hoy_str}.xlsx"

            # Convertir a bytes
            excel_bytes = df_to_excel_bytes(grupo, sheet_name="base")
            zf.writestr(nombre_archivo_excel, excel_bytes)
            archivos_generados.append(nombre_archivo_excel)

    if not archivos_generados:
        return None, []

    zip_buf.seek(0)
    return zip_buf.read(), archivos_generados
