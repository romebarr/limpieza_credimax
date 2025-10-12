"""
Módulo de UI específico para Bankard.

Contiene componentes de interfaz específicos para el flujo de Bankard.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from modules.ui.common_ui import (
    mostrar_estadisticas_generales, 
    mostrar_preview_datos,
    mostrar_configuracion_sms,
    crear_sidebar_configuracion,
    mostrar_metricas_procesamiento,
    mostrar_errores_archivo
)


def mostrar_sidebar_bankard():
    """
    Muestra la configuración específica de Bankard en la barra lateral.
    
    Returns:
        dict: Configuración seleccionada
    """
    crear_sidebar_configuracion("Configuración Bankard")
    
    # Valores por defecto (se detectan automáticamente en el procesamiento)
    col_tipo = "TIPO "  # Valor por defecto
    col_exclusion = "exclusion"  # Valor por defecto
    
    # Configuración de exportación
    st.sidebar.subheader("1) Exportación")
    exportar_zip = st.sidebar.checkbox(
        "Generar ZIP segmentado", 
        value=True,
        help="Genera archivo ZIP con segmentos por tipo"
    )
    
    # Configuración de SMS
    sms_texto, sms_link = mostrar_configuracion_sms("2) Plantillas SMS")
    
    return {
        "col_tipo": col_tipo,
        "col_exclusion": col_exclusion,
        "exportar_zip": exportar_zip,
        "sms_texto": sms_texto,
        "sms_link": sms_link
    }


def mostrar_exclusiones_bankard(exclusiones_info):
    """
    Muestra información sobre las exclusiones de Bankard.
    
    Args:
        exclusiones_info: Información sobre exclusiones
    """
    st.subheader("🚫 Gestión de Exclusiones")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Cédulas Excluidas", exclusiones_info.get("total_excluidas", 0))
    
    with col2:
        st.metric("Archivos Procesados", exclusiones_info.get("archivos_procesados", 0))
    
    with col3:
        ultima_actualizacion = exclusiones_info.get("ultima_actualizacion", "N/A")
        st.metric("Última Actualización", ultima_actualizacion)
    
    # Mostrar errores si los hay
    if "errores" in exclusiones_info and exclusiones_info["errores"]:
        mostrar_errores_archivo(exclusiones_info["errores"], "Errores en Exclusiones")


# Función desactivada - La corrección de BINs se muestra en la sección de procesamiento
# def mostrar_bins_bankard(bins_info):
#     """
#     Muestra información sobre la corrección de BINs.
#     
#     Args:
#         bins_info: Información sobre BINs
#     """
#     st.subheader("🔧 Corrección de BINs")
#     
#     if "bins_problematicos" in bins_info and bins_info["bins_problematicos"]:
#         st.warning(f"⚠️ Se encontraron {len(bins_info['bins_problematicos'])} BINs problemáticos")
#         
#         # Mostrar BINs problemáticos
#         with st.expander("Ver BINs problemáticos"):
#             for bin_problema in bins_info["bins_problematicos"]:
#                 st.write(f"• {bin_problema}")
#         
#         # Mostrar sugerencias si están disponibles
#         if "sugerencias" in bins_info and bins_info["sugerencias"]:
#             st.info("💡 Sugerencias automáticas disponibles")
#             for bin_problema, sugerencias in bins_info["sugerencias"].items():
#                 with st.expander(f"Sugerencias para: {bin_problema}"):
#                     for sugerencia in sugerencias:
#                         st.write(f"• {sugerencia}")
#     else:
#         st.success("✅ Todos los BINs son válidos")


def mostrar_resultados_bankard(df, config, resultados):
    """
    Muestra los resultados del procesamiento de Bankard.
    
    Args:
        df: DataFrame procesado
        config: Configuración utilizada
        resultados: Resultados del procesamiento
    """
    # Estadísticas generales
    mostrar_estadisticas_generales(df, "📊 Estadísticas de Bankard")
    
    # Información de exclusiones
    if "exclusiones" in resultados:
        mostrar_exclusiones_bankard(resultados["exclusiones"])
    
    # Vista previa de datos
    mostrar_preview_datos(df, "👀 Vista Previa de Datos")
    
    # Métricas de procesamiento
    if "metricas" in resultados:
        mostrar_metricas_procesamiento(resultados["metricas"])
    
    # Resultados de segmentación
    if config["exportar_zip"] and "zip_info" in resultados:
        st.subheader("📁 Archivos ZIP Generados")
        zip_info = resultados["zip_info"]
        st.success(f"✅ Se generaron {len(zip_info['archivos'])} archivos segmentados")
        
        st.write("**Archivos por tipo:**")
        for archivo in zip_info["archivos"]:
            st.caption(f"• {archivo}")
    
    # Resultados de SMS
    if config["sms_texto"] and config["sms_link"] and "sms_info" in resultados:
        st.subheader("📱 Plantillas SMS Generadas")
        sms_info = resultados["sms_info"]
        st.success(f"✅ Se generaron {len(sms_info['archivos'])} plantillas SMS")
        
        st.write("**Plantillas por tipo:**")
        for archivo in sms_info["archivos"]:
            st.caption(f"• {archivo}")
        
        if "enlace_acortado" in sms_info:
            st.caption(f"🔗 **Enlace acortado**: {sms_info['enlace_acortado']}")


def mostrar_downloads_bankard(resultados, config):
    """
    Muestra las opciones de descarga para Bankard.
    
    Args:
        resultados: Resultados del procesamiento
        config: Configuración utilizada
    """
    st.divider()
    st.subheader("⬇️ Descargas Disponibles")
    
    # Descarga de base limpia
    if "base_limpia" in resultados:
        st.download_button(
            "📄 Descargar Base Limpia",
            data=resultados["base_limpia"],
            file_name=f"Bankard_General_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    
    # Descarga de ZIP segmentado
    if config["exportar_zip"] and "zip_bytes" in resultados:
        st.download_button(
            "📦 Descargar ZIP Segmentado",
            data=resultados["zip_bytes"],
            file_name=f"Bankard_Segmentado_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
        )
    
    # Descarga de plantillas SMS
    if config["sms_texto"] and config["sms_link"] and "sms_bytes" in resultados:
        st.download_button(
            "📱 Descargar Plantillas SMS",
            data=resultados["sms_bytes"],
            file_name=f"SMS_Bankard_Segmentado_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
        )


def mostrar_validaciones_bankard(df):
    """
    Muestra validaciones específicas de Bankard.
    
    Args:
        df: DataFrame a validar
    """
    st.subheader("🔍 Validaciones de Bankard")
    
    # Validación de columnas requeridas
    columnas_requeridas = [
        "primer_nombre", "telefono", "cedula", "cupo", "BIN"
    ]
    
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    
    if columnas_faltantes:
        st.warning(f"⚠️ Columnas faltantes: {', '.join(columnas_faltantes)}")
    else:
        st.success("✅ Todas las columnas requeridas están presentes")
    
    # Validación de teléfonos
    if "telefono" in df.columns:
        telefonos_validos = df["telefono"].apply(lambda x: len(str(x).replace("-", "").replace(" ", "")) == 10).sum()
        total_telefonos = len(df)
        st.metric("Teléfonos Válidos", f"{telefonos_validos}/{total_telefonos}")
    
    # Validación de cédulas
    if "cedula" in df.columns:
        cedulas_validas = df["cedula"].apply(lambda x: len(str(x).replace(".", "").replace("-", "")) == 10).sum()
        total_cedulas = len(df)
        st.metric("Cédulas Válidas", f"{cedulas_validas}/{total_cedulas}")
    
    # Validación de BINs
    if "BIN" in df.columns:
        bins_validos = df["BIN"].isin([
            "Visa Oro", "Visa Platinum", "Mastercard Black", "Mastercard Clásica",
            "Mastercard Oro", "Visa Clásica", "Visa Infinite", "Visa Signature"
        ]).sum()
        total_bins = len(df)
        st.metric("BINs Válidos", f"{bins_validos}/{total_bins}")


def mostrar_progreso_bankard(etapa, total=6):
    """
    Muestra el progreso del procesamiento de Bankard.
    
    Args:
        etapa: Etapa actual
        total: Total de etapas
    """
    etapas = [
        "Cargando datos...",
        "Procesando exclusiones...",
        "Corrigiendo BINs...",
        "Aplicando limpiezas...",
        "Generando segmentación...",
        "Creando archivos de salida..."
    ]
    
    if etapa <= len(etapas):
        st.info(f"🔄 {etapas[etapa-1]}")
        st.progress(etapa / total)
