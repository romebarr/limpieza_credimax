"""
Aplicación principal modularizada para Limpieza Credimax & Bankard.

Esta versión utiliza todos los módulos creados para una mejor organización y mantenimiento.
"""

# =============================
# IMPORTS PRINCIPALES
# =============================
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Imports de módulos
from modules.ui.main_ui import (
    configurar_pagina, mostrar_header, mostrar_selector_flujo, 
    mostrar_info_flujo, mostrar_uploader_archivo, mostrar_sidebar_info
)
from modules.ui.credimax_ui import (
    mostrar_sidebar_credimax, mostrar_resultados_credimax, 
    mostrar_downloads_credimax, mostrar_validaciones_credimax
)
from modules.ui.bankard_ui import (
    mostrar_sidebar_bankard, mostrar_resultados_bankard,
    mostrar_downloads_bankard, mostrar_validaciones_bankard
)

# Imports de procesamiento
from modules.credimax.processor import preparar_zip_por_campana
from modules.credimax.sms_generator import generar_plantilla_sms_credimax_segmentada
from modules.bankard.processor import preparar_zip_bankard
from modules.bankard.cleaner import (
    limpiar_cupo_bankard, filtrar_vigencia_bankard, 
    limpiar_telefonos_cedulas_bankard, limpiar_nombres_bankard
)
from modules.bankard.exclusions import (
    cargar_cedulas_excluir_uploads, cargar_exclusiones_consolidadas,
    consolidar_exclusiones_desde_directorio, marcar_exclusiones_varios
)
from modules.bankard.bin_corrector import (
    cargar_memoria_correcciones, cargar_estadisticas_bin,
    detectar_bins_no_permitidos_inteligente, aplicar_correcciones_bin
)
from modules.bankard.sms_generator import generar_plantilla_sms_bankard_segmentada
from modules.bankard.column_detector import detectar_columnas_bankard

# Imports comunes
from modules.common.validators import validar_cedula_10, normalizar_celular_ec
from modules.common.formatters import a_nombre_propio, cupo_a_texto_miles_coma
from modules.common.utils import df_to_excel_bytes

# =============================
# CONFIGURACIÓN INICIAL
# =============================
configurar_pagina()
mostrar_header()
mostrar_sidebar_info()

# =============================
# SELECTOR DE FLUJO
# =============================
flujo = mostrar_selector_flujo()
mostrar_info_flujo(flujo)

# =============================
# UPLOADER DE ARCHIVOS
# =============================
archivo = mostrar_uploader_archivo(flujo)

if archivo is not None:
    try:
        # Cargar datos
        df = pd.read_excel(archivo, dtype=str)
        
        if flujo == "credimax":
            # =============================
            # FLUJO CREDIMAX
            # =============================
            config = mostrar_sidebar_credimax()
            
            # Validaciones
            mostrar_validaciones_credimax(df)
            
            # Procesamiento
            resultados = {}
            
            # 1. Limpieza básica
            df["CEDULA"] = df["CEDULA"].apply(lambda x: x if validar_cedula_10(x) else np.nan)
            df["CELULAR"] = df["CELULAR"].apply(normalizar_celular_ec)
            df["primer_nombre"] = df["primer_nombre"].apply(a_nombre_propio)
            df["CUPO"] = df["CUPO"].apply(cupo_a_texto_miles_coma)
            
            # 2. Generar base limpia
            resultados["base_limpia"] = df_to_excel_bytes(df, "base_limpia")
            
            # 3. Generar comparativo de campañas
            if "Campaña Growth" in df.columns:
                df_comp = df[["CEDULA", "Campaña Growth"]].copy()
                resultados["comparativo"] = df_to_excel_bytes(df_comp, "comparacion")
            
            # 4. Generar ZIP segmentado
            if config["exportar_zip"]:
                zip_bytes, archivos = preparar_zip_por_campana(df, config["col_campana"])
                if zip_bytes:
                    resultados["zip_bytes"] = zip_bytes
                    resultados["zip_info"] = {"archivos": archivos}
            
            # 5. Generar plantillas SMS
            if config["sms_texto"] and config["sms_link"]:
                sms_bytes, archivos_sms = generar_plantilla_sms_credimax_segmentada(
                    df, config["sms_texto"], config["sms_link"], config["col_campana"]
                )
                if sms_bytes:
                    resultados["sms_bytes"] = sms_bytes
                    resultados["sms_info"] = {"archivos": archivos_sms}
            
            # Mostrar resultados
            mostrar_resultados_credimax(df, config, resultados)
            mostrar_downloads_credimax(resultados, config)
            
        elif flujo == "bankard":
            # =============================
            # FLUJO BANKARD
            # =============================
            config = mostrar_sidebar_bankard()
            
            # Detectar columnas automáticamente
            columnas_detectadas = detectar_columnas_bankard(df)
            config.update(columnas_detectadas)
            
            # Cargar exclusiones
            exclusion_files = st.sidebar.file_uploader(
                "Subir archivos de exclusión",
                type=["xlsx", "xls"],
                accept_multiple_files=True,
                help="Sube archivos Excel con cédulas a excluir"
            )
            
            # Procesar exclusiones
            exclusiones_info = {}
            cedulas_excluir = set()
            
            if exclusion_files:
                cedulas_upload, errores = cargar_cedulas_excluir_uploads(exclusion_files)
                cedulas_excluir.update(cedulas_upload)
                exclusiones_info["errores"] = errores
            
            # Cargar exclusiones consolidadas
            cedulas_consolidadas, estadisticas = cargar_exclusiones_consolidadas()
            cedulas_excluir.update(cedulas_consolidadas.keys())
            exclusiones_info.update(estadisticas)
            
            # Cargar memoria de correcciones
            memoria_correcciones = cargar_memoria_correcciones()
            estadisticas_bin = cargar_estadisticas_bin()
            
            # Procesamiento
            resultados = {}
            
            # 1. Limpieza básica
            df = limpiar_cupo_bankard(df)
            df = limpiar_telefonos_cedulas_bankard(df)
            df = limpiar_nombres_bankard(df)
            
            # 2. Filtrar por vigencia
            df, excluidos_vigencia = filtrar_vigencia_bankard(df)
            
            # 3. Marcar exclusiones
            df = marcar_exclusiones_varios(df, cedulas_excluir)
            
            # 4. Corregir BINs
            bins_problematicos, sugerencias = detectar_bins_no_permitidos_inteligente(
                df, memoria_correcciones, estadisticas_bin
            )
            df = aplicar_correcciones_bin(df, memoria_correcciones, estadisticas_bin)
            
            # 5. Generar base limpia
            resultados["base_limpia"] = df_to_excel_bytes(df, "base_limpia")
            
            # 6. Generar ZIP segmentado
            if config["exportar_zip"]:
                zip_bytes, archivos = preparar_zip_bankard(
                    df, config["col_tipo"], config["col_exclusion"]
                )
                if zip_bytes:
                    resultados["zip_bytes"] = zip_bytes
                    resultados["zip_info"] = {"archivos": archivos}
            
            # 7. Generar plantillas SMS
            if config["sms_texto"] and config["sms_link"]:
                sms_bytes, archivos_sms = generar_plantilla_sms_bankard_segmentada(
                    df, config["sms_texto"], config["sms_link"], 
                    config["col_tipo"], config["col_exclusion"]
                )
                if sms_bytes:
                    resultados["sms_bytes"] = sms_bytes
                    resultados["sms_info"] = {"archivos": archivos_sms}
            
            # Agregar información adicional
            resultados["exclusiones"] = exclusiones_info
            resultados["bins"] = {
                "bins_problematicos": bins_problematicos,
                "sugerencias": sugerencias
            }
            resultados["metricas"] = {
                "Excluidos por vigencia": excluidos_vigencia,
                "Total exclusiones": len(cedulas_excluir)
            }
            
            # Mostrar resultados
            mostrar_resultados_bankard(df, config, resultados)
            mostrar_downloads_bankard(resultados, config)
            
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        st.exception(e)
else:
    st.info("👆 Por favor, sube un archivo para comenzar el procesamiento")
