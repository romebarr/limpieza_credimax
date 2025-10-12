"""
Módulo de generación de plantillas SMS para Credimax.

Contiene la funcionalidad para generar plantillas SMS segmentadas por campaña.
"""

import io
import zipfile
import pandas as pd
import numpy as np
from datetime import datetime

from modules.common.formatters import safe_filename
from modules.common.utils import df_to_excel_bytes
from modules.integrations.bitly import acortar_enlace_bitly


def generar_plantilla_sms_credimax_segmentada(df, sms_texto, sms_link, col_campana="Campaña Growth"):
    """
    Genera plantillas SMS segmentadas por campaña para Credimax.
    
    Esta función:
    1. Acorta el enlace usando Bitly
    2. Filtra registros con IND_DESEMBOLSO = "0" y celulares válidos
    3. Agrupa por campaña y genera un archivo Excel por cada campaña
    4. Reemplaza variables en el texto SMS: <#monto#>, <#tasa#>, <#link#>
    5. Exporta archivos sin encabezados para importación directa
    
    Args:
        df: DataFrame con datos de Credimax
        sms_texto: Texto del SMS con variables personalizables
        sms_link: Enlace original a acortar
        col_campana: Nombre de la columna de campaña
        
    Returns:
        tuple: (bytes_zip, lista_archivos_generados) o (None, []) si no hay datos
    """
    if not sms_texto or not sms_link:
        return None, []
    
    # Acortar el enlace usando Bitly
    enlace_acortado = acortar_enlace_bitly(sms_link)
    
    # Usar la misma lógica que preparar_zip_por_campana
    columnas_necesarias = {
        col_campana,
        "IND_DESEMBOLSO",
        "CELULAR",
        "CUPO",  # Columna original del monto
        "Tasa",  # Columna original de la tasa
    }

    df_trabajo = df.copy()
    for col in columnas_necesarias:
        if col not in df_trabajo.columns:
            df_trabajo[col] = np.nan

    # Filtrar registros válidos
    df_exp = df_trabajo[df_trabajo["IND_DESEMBOLSO"] == "0"].copy()
    df_exp[col_campana] = df_exp[col_campana].astype(str).str.strip()
    
    # Filtrar campañas válidas
    mask_no_vacio = (
        df_exp[col_campana].notna()
        & (df_exp[col_campana] != "")
        & (~df_exp[col_campana].str.lower().eq("nan"))
    )
    df_exp = df_exp[mask_no_vacio].copy()
    
    # Filtrar celulares válidos
    df_exp = df_exp[df_exp["CELULAR"].notna() & (df_exp["CELULAR"] != "")].copy()

    if df_exp.empty:
        return None, []

    # Agrupar por campaña
    grupos = df_exp.groupby(col_campana)

    zip_buf = io.BytesIO()
    archivos_generados = []
    fecha_archivo = datetime.now().strftime("%Y%m%d")

    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for nombre_campana, grupo in grupos:
            if grupo.empty:
                continue

            celulares = []
            mensajes = []

            for _, row in grupo.iterrows():
                celular = str(row.get("CELULAR", "")).strip()
                if not celular or celular == "nan":
                    continue

                # Obtener valores originales
                monto = str(row.get("CUPO", "")).strip()
                tasa = str(row.get("Tasa", "")).strip()
                
                # Mantener formato con comas para separadores de miles
                if monto and monto != "nan":
                    monto_limpio = monto  # Mantener el formato original con comas
                else:
                    monto_limpio = "0"
                
                # Limpiar tasa (remover % si existe)
                if tasa and tasa != "nan":
                    tasa_limpia = tasa.replace("%", "").strip()
                else:
                    tasa_limpia = "0"

                # Crear mensaje personalizado
                mensaje = sms_texto
                mensaje = mensaje.replace("<#monto#>", monto_limpio)
                mensaje = mensaje.replace("<#tasa#>", tasa_limpia)
                mensaje = mensaje.replace("<#link#>", enlace_acortado)

                celulares.append(celular)
                mensajes.append(mensaje)

            if not celulares:
                continue

            # Crear DataFrame para esta campaña
            df_campana = pd.DataFrame({
                "celular": celulares,
                "mensaje": mensajes
            })
            
            # Agregar al ZIP (sin encabezados)
            excel_bytes = df_to_excel_bytes(df_campana, sheet_name="sms", header=False)
            nombre_archivo = safe_filename(nombre_campana) or "SIN_CAMPANA"
            nombre_archivo_sms = f"SMS_{nombre_archivo}_{fecha_archivo}.xlsx"
            zf.writestr(nombre_archivo_sms, excel_bytes)
            archivos_generados.append(nombre_archivo_sms)

    if not archivos_generados:
        return None, []

    zip_buf.seek(0)
    return zip_buf.read(), archivos_generados


def generar_plantilla_sms_credimax_consolidada(df, sms_texto, sms_link, col_campana="Campaña Growth"):
    """
    Genera UNA SOLA plantilla SMS consolidada para todos los segmentos seleccionados.
    
    Esta función:
    1. Acorta el enlace usando Bitly
    2. Filtra registros con IND_DESEMBOLSO = "0" y celulares válidos
    3. Combina TODOS los registros en un solo archivo
    4. Reemplaza variables en el texto SMS: <#monto#>, <#tasa#>, <#link#>
    5. Exporta un solo archivo sin encabezados
    
    Args:
        df: DataFrame con datos de Credimax (ya filtrado por segmentos seleccionados)
        sms_texto: Texto del SMS con variables personalizables
        sms_link: Enlace original a acortar
        col_campana: Nombre de la columna de campaña
        
    Returns:
        bytes: Archivo Excel con plantilla SMS consolidada o None si no hay datos
    """
    if not sms_texto or not sms_link:
        return None
    
    # Acortar el enlace usando Bitly
    enlace_acortado = acortar_enlace_bitly(sms_link)
    
    # Columnas necesarias
    columnas_necesarias = {
        col_campana,
        "IND_DESEMBOLSO",
        "CELULAR",
        "CUPO",  # Columna original del monto
        "Tasa",  # Columna original de la tasa
    }

    df_trabajo = df.copy()
    for col in columnas_necesarias:
        if col not in df_trabajo.columns:
            df_trabajo[col] = np.nan

    # Filtrar registros válidos
    df_exp = df_trabajo[df_trabajo["IND_DESEMBOLSO"] == "0"].copy()
    df_exp[col_campana] = df_exp[col_campana].astype(str).str.strip()
    
    # Filtrar campañas válidas
    mask_no_vacio = (
        df_exp[col_campana].notna()
        & (df_exp[col_campana] != "")
        & (~df_exp[col_campana].str.lower().eq("nan"))
    )
    df_exp = df_exp[mask_no_vacio].copy()
    
    # Filtrar celulares válidos
    df_exp = df_exp[df_exp["CELULAR"].notna() & (df_exp["CELULAR"] != "")].copy()

    if df_exp.empty:
        return None

    # Generar mensajes para TODOS los registros (sin agrupar por campaña)
    celulares = []
    mensajes = []

    for _, row in df_exp.iterrows():
        celular = str(row.get("CELULAR", "")).strip()
        if not celular or celular == "nan":
            continue

        # Obtener valores originales
        monto = str(row.get("CUPO", "")).strip()
        tasa = str(row.get("Tasa", "")).strip()
        
        # Mantener formato con comas para separadores de miles
        if monto and monto != "nan":
            monto_limpio = monto  # Mantener el formato original con comas
        else:
            monto_limpio = "0"
        
        # Limpiar tasa (remover % si existe)
        if tasa and tasa != "nan":
            tasa_limpia = tasa.replace("%", "").strip()
        else:
            tasa_limpia = "0"

        # Crear mensaje personalizado
        mensaje = sms_texto
        mensaje = mensaje.replace("<#monto#>", monto_limpio)
        mensaje = mensaje.replace("<#tasa#>", tasa_limpia)
        mensaje = mensaje.replace("<#link#>", enlace_acortado)

        celulares.append(celular)
        mensajes.append(mensaje)

    if not celulares:
        return None

    # Crear DataFrame consolidado
    df_consolidado = pd.DataFrame({
        "celular": celulares,
        "mensaje": mensajes
    })
    
    # Generar archivo Excel sin encabezados
    excel_bytes = df_to_excel_bytes(df_consolidado, sheet_name="sms", header=False)
    return excel_bytes
