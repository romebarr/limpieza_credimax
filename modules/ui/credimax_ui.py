"""
Módulo de UI específico para Credimax.

Contiene componentes de interfaz específicos para el flujo de Credimax.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from modules.ui.common_ui import (
    mostrar_estadisticas_generales, 
    mostrar_preview_datos,
    mostrar_configuracion_sms,
    crear_sidebar_configuracion,
    mostrar_metricas_procesamiento
)


def mostrar_sidebar_credimax():
    """
    Muestra la configuración específica de Credimax en la barra lateral.
    
    Returns:
        dict: Configuración seleccionada
    """
    crear_sidebar_configuracion("Configuración Credimax")
    
    # Configuración automática de segmentación (sin mostrar en UI)
    col_campana = "Campaña Growth"  # Columna fija
    
    # Configuración de exportación
    st.sidebar.subheader("1) Exportación")
    exportar_zip = st.sidebar.checkbox(
        "Generar ZIP segmentado", 
        value=True,
        help="Genera archivo ZIP con segmentos por campaña"
    )
    
    # Configuración de SMS
    sms_texto, sms_link = mostrar_configuracion_sms("2) Plantillas SMS")
    
    return {
        "col_campana": col_campana,
        "exportar_zip": exportar_zip,
        "sms_texto": sms_texto,
        "sms_link": sms_link
    }


def mostrar_resultados_credimax(df, config, resultados):
    """
    Muestra los resultados del procesamiento de Credimax.
    
    Args:
        df: DataFrame procesado
        config: Configuración utilizada
        resultados: Resultados del procesamiento
    """
    # Estadísticas generales
    mostrar_estadisticas_generales(df, "📊 Estadísticas de Credimax")
    
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
        
        st.write("**Archivos por campaña:**")
        for archivo in zip_info["archivos"]:
            st.caption(f"• {archivo}")
    
    # Resultados de SMS
    if config["sms_texto"] and config["sms_link"] and "sms_info" in resultados:
        st.subheader("📱 Plantillas SMS Generadas")
        sms_info = resultados["sms_info"]
        st.success(f"✅ Se generaron {len(sms_info['archivos'])} plantillas SMS")
        
        st.write("**Plantillas por campaña:**")
        for archivo in sms_info["archivos"]:
            st.caption(f"• {archivo}")
        
        if "enlace_acortado" in sms_info:
            st.caption(f"🔗 **Enlace acortado**: {sms_info['enlace_acortado']}")


def mostrar_downloads_credimax(resultados, config):
    """
    Muestra las opciones de descarga para Credimax.
    
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
            file_name=f"Base_Credimax_LIMPIA_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    
    # Descarga de comparativo
    if "comparativo" in resultados:
        st.download_button(
            "📊 Descargar Comparativo de Campañas",
            data=resultados["comparativo"],
            file_name=f"Base_Credimax_COMPARACION_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    
    # Descarga de ZIP segmentado
    if config["exportar_zip"] and "zip_bytes" in resultados:
        st.download_button(
            "📦 Descargar ZIP Segmentado",
            data=resultados["zip_bytes"],
            file_name=f"Credimax_Segmentado_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
        )
    
    # Descarga de plantillas SMS
    if config["sms_texto"] and config["sms_link"] and "sms_bytes" in resultados:
        st.download_button(
            "📱 Descargar Plantillas SMS",
            data=resultados["sms_bytes"],
            file_name=f"SMS_Credimax_Segmentado_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
        )


def mostrar_validaciones_credimax(df):
    """
    Muestra validaciones específicas de Credimax.
    
    Args:
        df: DataFrame a validar
    """
    st.subheader("🔍 Validaciones de Credimax")
    
    # Validación de columnas requeridas
    columnas_requeridas = [
        "MIS", "CEDULA", "FECHA NACIMIENTO", "primer_nombre", 
        "CELULAR", "CORREO CLIENTE", "CUPO", "Tasa"
    ]
    
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    
    if columnas_faltantes:
        st.warning(f"⚠️ Columnas faltantes: {', '.join(columnas_faltantes)}")
    else:
        st.success("✅ Todas las columnas requeridas están presentes")
    
    # Validación de cédulas
    if "CEDULA" in df.columns:
        cedulas_validas = df["CEDULA"].apply(lambda x: len(str(x).replace(".", "").replace("-", "")) == 10).sum()
        total_cedulas = len(df)
        st.metric("Cédulas Válidas", f"{cedulas_validas}/{total_cedulas}")
    
    # Validación de celulares
    if "CELULAR" in df.columns:
        celulares_validos = df["CELULAR"].apply(lambda x: len(str(x).replace("-", "").replace(" ", "")) == 10).sum()
        total_celulares = len(df)
        st.metric("Celulares Válidos", f"{celulares_validos}/{total_celulares}")


def mostrar_progreso_credimax(etapa, total=5):
    """
    Muestra el progreso del procesamiento de Credimax.
    
    Args:
        etapa: Etapa actual
        total: Total de etapas
    """
    etapas = [
        "Cargando datos...",
        "Validando columnas...",
        "Aplicando limpiezas...",
        "Generando segmentación...",
        "Creando archivos de salida..."
    ]
    
    if etapa <= len(etapas):
        st.info(f"🔄 {etapas[etapa-1]}")
        st.progress(etapa / total)
