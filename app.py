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
from modules.credimax.sms_generator import generar_plantilla_sms_credimax_segmentada, generar_plantilla_sms_credimax_consolidada
from modules.credimax.campaign_assigner import asignar_campanas_automaticamente, mostrar_estadisticas_campanas
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
    detectar_bins_no_permitidos_inteligente, aplicar_correcciones_bin,
    mostrar_sugerencias_interactivas_bin, mostrar_estado_memoria_bin, VALORES_BIN_PERMITIDOS
)
from modules.bankard.sms_generator import generar_plantilla_sms_bankard_segmentada, generar_plantilla_sms_bankard_consolidada
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
            
            # 2. Asignar campañas automáticamente
            df, estadisticas_campanas = asignar_campanas_automaticamente(df)
            mostrar_estadisticas_campanas(estadisticas_campanas)
            
            # 3. Generar base limpia
            resultados["base_limpia"] = df_to_excel_bytes(df, "base_limpia")
            
            # 4. Generar comparativo de campañas
            if "Campaña Growth Original" in df.columns:
                df_comp = df[["CEDULA", "Campaña Growth Original", "Campaña Growth"]].copy()
                df_comp["Cambio Aplicado"] = df_comp["Campaña Growth Original"] != df_comp["Campaña Growth"]
                resultados["comparativo"] = df_to_excel_bytes(df_comp, "comparacion")
            
            # 5. Generar ZIP segmentado
            segmentos_disponibles = []
            if config["exportar_zip"]:
                zip_bytes, archivos = preparar_zip_por_campana(df, config["col_campana"])
                if zip_bytes:
                    resultados["zip_bytes"] = zip_bytes
                    resultados["zip_info"] = {"archivos": archivos}
                    # Extraer nombres de segmentos de los archivos
                    segmentos_disponibles = [
                        archivo.replace("Credimax_", "").replace(f"_{datetime.now().strftime('%Y%m%d')}.xlsx", "")
                        for archivo in archivos
                    ]
            
            # Mostrar resultados y descargas primero
            mostrar_resultados_credimax(df, config, resultados)
            mostrar_downloads_credimax(resultados, config)
            
            # 6. Selector de segmentos para plantillas SMS
            if config["sms_texto"] and config["sms_link"] and segmentos_disponibles:
                st.divider()
                st.subheader("📱 Generación de Plantillas SMS")
                st.info("Selecciona los segmentos que deseas incluir en las plantillas SMS")
                
                # Multiselect para elegir segmentos
                segmentos_seleccionados = st.multiselect(
                    "Segmentos para SMS:",
                    options=segmentos_disponibles,
                    default=segmentos_disponibles,  # Por defecto todos seleccionados
                    help="Selecciona uno o más segmentos para generar plantillas SMS"
                )
                
                # Botón para generar SMS
                if segmentos_seleccionados and st.button("🚀 Generar Plantilla SMS", type="primary"):
                    with st.spinner("Generando plantilla SMS consolidada..."):
                        # Filtrar DataFrame por segmentos seleccionados
                        df_filtrado = df[df[config["col_campana"]].isin(segmentos_seleccionados)].copy()
                        
                        # Generar UN SOLO archivo SMS consolidado
                        sms_bytes = generar_plantilla_sms_credimax_consolidada(
                            df_filtrado, config["sms_texto"], config["sms_link"], config["col_campana"]
                        )
                        
                        if sms_bytes:
                            # Contar registros
                            num_registros = len(df_filtrado[df_filtrado["IND_DESEMBOLSO"] == "0"])
                            st.success(f"✅ Se generó plantilla SMS con {num_registros} registros")
                            
                            # Mostrar segmentos incluidos
                            with st.expander("📋 Segmentos incluidos en la plantilla"):
                                for segmento in segmentos_seleccionados:
                                    count = len(df_filtrado[df_filtrado[config["col_campana"]] == segmento])
                                    st.write(f"• {segmento}: {count} registros")
                            
                            # Botón de descarga
                            st.download_button(
                                "⬇️ Descargar Plantilla SMS",
                                data=sms_bytes,
                                file_name=f"Plantilla_SMS_Credimax_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.warning("⚠️ No se pudo generar la plantilla SMS para los segmentos seleccionados")
            
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
            
            # 4. Detectar y corregir BINs interactivamente
            bins_problematicos, sugerencias = detectar_bins_no_permitidos_inteligente(
                df, memoria_correcciones, estadisticas_bin
            )
            
            # Mostrar estado de memoria de correcciones
            mostrar_estado_memoria_bin(memoria_correcciones)
            
            # Mostrar interfaz interactiva para corrección de BINs
            correcciones_confirmadas = {}
            if bins_problematicos:
                st.warning(f"⚠️ Se encontraron {len(bins_problematicos)} BINs no permitidos")
                correcciones_confirmadas = mostrar_sugerencias_interactivas_bin(
                    bins_problematicos, sugerencias, memoria_correcciones
                )
                
                # Recargar memoria después de posibles correcciones
                if correcciones_confirmadas:
                    memoria_correcciones = cargar_memoria_correcciones()
            else:
                st.success("✅ No se encontraron BINs problemáticos")
            
            # Aplicar correcciones confirmadas
            df_antes = df.copy()
            df = aplicar_correcciones_bin(
                df, memoria_correcciones, estadisticas_bin, correcciones_confirmadas
            )
            
            # Contar correcciones aplicadas
            cambios_bin = 0
            if "BIN" in df.columns and "BIN" in df_antes.columns:
                cambios_bin = (df["BIN"] != df_antes["BIN"]).sum()
                if cambios_bin > 0:
                    st.success(f"✅ Se aplicaron {cambios_bin} correcciones de BINs confirmadas")
                else:
                    st.info("ℹ️ No se realizaron cambios en los BINs")
            
            # 5. Generar base limpia
            resultados["base_limpia"] = df_to_excel_bytes(df, "base_limpia")
            
            # 6. Generar ZIP segmentado
            segmentos_disponibles_bk = []
            if config["exportar_zip"]:
                zip_bytes, archivos = preparar_zip_bankard(
                    df, config["col_tipo"], config["col_exclusion"]
                )
                if zip_bytes:
                    resultados["zip_bytes"] = zip_bytes
                    resultados["zip_info"] = {"archivos": archivos}
                    # Extraer nombres de segmentos de los archivos
                    segmentos_disponibles_bk = [
                        archivo.replace("Bankard_", "").replace(f"_{datetime.now().strftime('%Y%m%d')}.xlsx", "")
                        for archivo in archivos
                    ]
            
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
            
            # Mostrar estadísticas de BINs
            if "BIN" in df.columns:
                # Filtrar valores nulos o vacíos
                df_bins = df[df["BIN"].notna() & (df["BIN"] != "") & (df["BIN"] != "nan")].copy()
                
                if not df_bins.empty:
                    bins_unicos = df_bins["BIN"].value_counts()
                    st.subheader("📊 Estadísticas de BINs")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de BINs únicos", len(bins_unicos))
                    with col2:
                        bins_validos = sum(1 for bin_val in bins_unicos.index if bin_val in VALORES_BIN_PERMITIDOS)
                        st.metric("BINs válidos", f"{bins_validos}/{len(bins_unicos)}")
                    with col3:
                        total_registros = len(df_bins)
                        st.metric("Total registros", total_registros)
                    
                    # Mostrar distribución de BINs
                    with st.expander("Ver distribución de BINs"):
                        # Crear DataFrame con información detallada
                        df_distribucion = bins_unicos.reset_index()
                        df_distribucion.columns = ["BIN", "Cantidad"]
                        df_distribucion["Porcentaje"] = (df_distribucion["Cantidad"] / total_registros * 100).round(2)
                        df_distribucion["Es Válido"] = df_distribucion["BIN"].apply(
                            lambda x: "✅" if x in VALORES_BIN_PERMITIDOS else "❌"
                        )
                        
                        st.dataframe(df_distribucion, use_container_width=True)
                        
                        # Mostrar resumen de BINs problemáticos
                        bins_problematicos_actuales = [bin_val for bin_val in bins_unicos.index 
                                                     if bin_val not in VALORES_BIN_PERMITIDOS and bin_val != "BIN NO VÁLIDO"]
                        bins_no_validos = [bin_val for bin_val in bins_unicos.index if bin_val == "BIN NO VÁLIDO"]
                        
                        if bins_no_validos:
                            st.error(f"❌ Hay {len(bins_no_validos)} registros con BINs que no se pudieron corregir automáticamente")
                        elif bins_problematicos_actuales:
                            st.warning(f"⚠️ Aún hay {len(bins_problematicos_actuales)} BINs problemáticos sin corregir")
                        else:
                            st.success("✅ Todos los BINs son válidos")
                else:
                    st.warning("⚠️ No se encontraron BINs válidos en el DataFrame")
            
            # Mostrar resultados
            mostrar_resultados_bankard(df, config, resultados)
            mostrar_downloads_bankard(resultados, config)
            
            # 7. Selector de segmentos para plantillas SMS
            if config["sms_texto"] and config["sms_link"] and segmentos_disponibles_bk:
                st.divider()
                st.subheader("📱 Generación de Plantillas SMS")
                st.info("Selecciona los segmentos que deseas incluir en las plantillas SMS")
                
                # Multiselect para elegir segmentos
                segmentos_seleccionados_bk = st.multiselect(
                    "Segmentos para SMS:",
                    options=segmentos_disponibles_bk,
                    default=segmentos_disponibles_bk,  # Por defecto todos seleccionados
                    help="Selecciona uno o más segmentos para generar plantillas SMS",
                    key="bankard_sms_selector"
                )
                
                # Botón para generar SMS
                if segmentos_seleccionados_bk and st.button("🚀 Generar Plantilla SMS", type="primary", key="bankard_sms_btn"):
                    with st.spinner("Generando plantilla SMS consolidada..."):
                        # Filtrar DataFrame por segmentos seleccionados
                        df_filtrado = df[df[config["col_tipo"]].isin(segmentos_seleccionados_bk)].copy()
                        
                        # Generar UN SOLO archivo SMS consolidado
                        sms_bytes = generar_plantilla_sms_bankard_consolidada(
                            df_filtrado, config["sms_texto"], config["sms_link"], 
                            config["col_tipo"], config["col_exclusion"]
                        )
                        
                        if sms_bytes:
                            # Contar registros
                            num_registros = len(df_filtrado[df_filtrado[config["col_exclusion"]] == "NO"])
                            st.success(f"✅ Se generó plantilla SMS con {num_registros} registros")
                            
                            # Mostrar segmentos incluidos
                            with st.expander("📋 Segmentos incluidos en la plantilla"):
                                for segmento in segmentos_seleccionados_bk:
                                    count = len(df_filtrado[df_filtrado[config["col_tipo"]] == segmento])
                                    st.write(f"• {segmento}: {count} registros")
                            
                            # Botón de descarga
                            st.download_button(
                                "⬇️ Descargar Plantilla SMS",
                                data=sms_bytes,
                                file_name=f"Plantilla_SMS_Bankard_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="bankard_sms_download"
                            )
                        else:
                            st.warning("⚠️ No se pudo generar la plantilla SMS para los segmentos seleccionados")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        st.exception(e)
else:
    st.info("👆 Por favor, sube un archivo para comenzar el procesamiento")
