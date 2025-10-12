"""
Módulo de generación de plantillas SMS para Bankard.

Contiene la funcionalidad para generar plantillas SMS segmentadas por tipo de tarjeta.
"""

import io
import zipfile
import pandas as pd
import numpy as np
from datetime import datetime

from modules.common.formatters import safe_filename
from modules.common.utils import df_to_excel_bytes
from modules.integrations.bitly import acortar_enlace_bitly


def generar_plantilla_sms_bankard_segmentada(df, sms_texto, sms_link, col_tipo="TIPO ", col_exclusion="exclusion"):
    """
    Genera plantillas SMS segmentadas por tipo para Bankard.
    
    Esta función:
    1. Acorta el enlace usando Bitly
    2. Filtra registros con exclusion = "NO" y teléfonos válidos
    3. Agrupa por tipo de tarjeta y genera un archivo Excel por cada tipo
    4. Reemplaza variables en el texto SMS: <#marca#>, <#cupo#>, <#link#>
    5. Formatea cupos con separadores de miles
    6. Exporta archivos sin encabezados para importación directa
    
    Args:
        df: DataFrame con datos de Bankard
        sms_texto: Texto del SMS con variables personalizables
        sms_link: Enlace original a acortar
        col_tipo: Nombre de la columna de tipo
        col_exclusion: Nombre de la columna de exclusión
        
    Returns:
        tuple: (bytes_zip, lista_archivos_generados) o (None, []) si no hay datos
    """
    if not sms_texto or not sms_link:
        return None, []
    
    # Acortar el enlace usando Bitly
    enlace_acortado = acortar_enlace_bitly(sms_link)
    
    # Asegurar que existen las columnas necesarias
    if col_tipo not in df.columns:
        df[col_tipo] = "SIN_TIPO"
    if col_exclusion not in df.columns:
        df[col_exclusion] = "NO"
    
    # Filtrar registros sin exclusión
    df_filtrado = df[df[col_exclusion] == "NO"].copy()
    
    # Filtrar teléfonos válidos
    df_filtrado = df_filtrado[df_filtrado["telefono"].notna() & (df_filtrado["telefono"] != "")].copy()
    
    if df_filtrado.empty:
        return None, []
    
    # Asegurar que existen las columnas BIN y cupo
    if "BIN" not in df_filtrado.columns:
        df_filtrado["BIN"] = ""
    if "cupo" not in df_filtrado.columns:
        df_filtrado["cupo"] = ""
    
    # Agrupar por tipo
    grupos = df_filtrado.groupby(col_tipo)
    
    zip_buf = io.BytesIO()
    archivos_generados = []
    hoy_str = datetime.now().strftime("%Y%m%d")
    
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for tipo, grupo in grupos:
            if grupo.empty:
                continue
            
            telefonos = []
            mensajes = []
            
            for _, row in grupo.iterrows():
                telefono = str(row.get("telefono", "")).strip()
                if not telefono or telefono == "nan":
                    continue
                
                # Obtener valores originales
                marca = str(row.get("BIN", "")).strip()
                cupo = str(row.get("cupo", "")).strip()
                
                # Formatear cupo con separadores de miles
                if cupo and cupo != "nan":
                    try:
                        cupo_num = int(float(cupo))
                        cupo_limpio = f"{cupo_num:,}"
                    except (ValueError, TypeError):
                        cupo_limpio = "0"
                else:
                    cupo_limpio = "0"
                
                # Crear mensaje personalizado
                mensaje = sms_texto
                mensaje = mensaje.replace("<#marca#>", marca)
                mensaje = mensaje.replace("<#cupo#>", cupo_limpio)
                mensaje = mensaje.replace("<#link#>", enlace_acortado)
                
                telefonos.append(telefono)
                mensajes.append(mensaje)
            
            if not telefonos:
                continue
            
            # Crear DataFrame para este tipo
            df_tipo = pd.DataFrame({
                "telefono": telefonos,
                "mensaje": mensajes
            })
            
            # Agregar al ZIP (sin encabezados)
            excel_bytes = df_to_excel_bytes(df_tipo, sheet_name="sms", header=False)
            nombre_tipo = safe_filename(tipo) or "SIN_TIPO"
            nombre_archivo_sms = f"SMS_Bankard_{nombre_tipo}_{hoy_str}.xlsx"
            zf.writestr(nombre_archivo_sms, excel_bytes)
            archivos_generados.append(nombre_archivo_sms)
    
    if not archivos_generados:
        return None, []
    
    zip_buf.seek(0)
    return zip_buf.read(), archivos_generados
