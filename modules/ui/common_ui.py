"""
Módulo de componentes de UI comunes.

Contiene componentes reutilizables para la interfaz de usuario.
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def mostrar_estadisticas_generales(df, titulo="Estadísticas Generales"):
    """
    Muestra estadísticas generales de un DataFrame.
    
    Args:
        df: DataFrame a analizar
        titulo: Título de la sección
    """
    st.subheader(titulo)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Registros", len(df))
    
    with col2:
        st.metric("Columnas", len(df.columns))
    
    with col3:
        registros_vacios = df.isnull().sum().sum()
        st.metric("Valores Vacíos", registros_vacios)
    
    with col4:
        duplicados = df.duplicated().sum()
        st.metric("Duplicados", duplicados)


def mostrar_preview_datos(df, titulo="Vista Previa de Datos", max_rows=5):
    """
    Muestra una vista previa de los datos.
    
    Args:
        df: DataFrame a mostrar
        titulo: Título de la sección
        max_rows: Número máximo de filas a mostrar
    """
    st.subheader(titulo)
    st.dataframe(df.head(max_rows), use_container_width=True)


def mostrar_errores_archivo(errores, titulo="Errores de Archivo"):
    """
    Muestra errores de procesamiento de archivos.
    
    Args:
        errores: Lista de errores
        titulo: Título de la sección
    """
    if errores:
        st.error(titulo)
        for error in errores:
            st.caption(f"• {error}")


def mostrar_exito_procesamiento(mensaje, archivos_generados=None):
    """
    Muestra mensaje de éxito en el procesamiento.
    
    Args:
        mensaje: Mensaje de éxito
        archivos_generados: Lista de archivos generados (opcional)
    """
    st.success(mensaje)
    
    if archivos_generados:
        st.write("**Archivos generados:**")
        for archivo in archivos_generados:
            st.caption(f"• {archivo}")


def crear_seccion_downloads(titulo="Descargas Disponibles"):
    """
    Crea una sección de descargas con título.
    
    Args:
        titulo: Título de la sección
        
    Returns:
        bool: True si se debe mostrar la sección
    """
    st.divider()
    st.subheader(titulo)
    return True


def mostrar_configuracion_sms(titulo="Configuración SMS"):
    """
    Muestra la configuración de plantillas SMS.
    
    Args:
        titulo: Título de la sección
        
    Returns:
        tuple: (sms_texto, sms_link) o (None, None) si no está habilitado
    """
    st.sidebar.header(titulo)
    
    exportar_sms = st.sidebar.checkbox(
        "Generar plantilla SMS", 
        value=False, 
        help="Genera archivo con plantilla de SMS personalizada"
    )
    
    sms_texto = ""
    sms_link = ""
    
    if exportar_sms:
        st.sidebar.subheader("📱 Configuración SMS")
        sms_texto = st.sidebar.text_area(
            "Texto del SMS",
            help="Usa variables personalizables como <#monto#>, <#tasa#>, <#link#>",
            key=f"sms_texto_{titulo.lower().replace(' ', '_')}"
        )
        sms_link = st.sidebar.text_input(
            "Enlace",
            help="Enlace que reemplazará <#link#> en el SMS",
            key=f"sms_link_{titulo.lower().replace(' ', '_')}"
        )
    
    return sms_texto, sms_link


def mostrar_progreso_procesamiento(etapa, total_etapas=5):
    """
    Muestra una barra de progreso del procesamiento.
    
    Args:
        etapa: Etapa actual (1-indexed)
        total_etapas: Total de etapas
    """
    progreso = etapa / total_etapas
    st.progress(progreso)
    st.caption(f"Procesando... {etapa}/{total_etapas}")


def mostrar_info_archivo(archivo, titulo="Información del Archivo"):
    """
    Muestra información básica de un archivo.
    
    Args:
        archivo: Archivo subido
        titulo: Título de la sección
    """
    st.info(f"{titulo}: {archivo.name} ({archivo.size:,} bytes)")


def crear_sidebar_configuracion(titulo="Configuración"):
    """
    Crea una sección de configuración en la barra lateral.
    
    Args:
        titulo: Título de la sección
    """
    st.sidebar.header(titulo)


def mostrar_metricas_procesamiento(metricas):
    """
    Muestra métricas de procesamiento.
    
    Args:
        metricas: Diccionario con métricas
    """
    if metricas:
        st.subheader("📊 Métricas de Procesamiento")
        
        cols = st.columns(len(metricas))
        for i, (nombre, valor) in enumerate(metricas.items()):
            with cols[i]:
                st.metric(nombre, valor)


def mostrar_warning_configuracion(mensaje):
    """
    Muestra una advertencia de configuración.
    
    Args:
        mensaje: Mensaje de advertencia
    """
    st.warning(f"⚠️ {mensaje}")


def mostrar_info_configuracion(mensaje):
    """
    Muestra información de configuración.
    
    Args:
        mensaje: Mensaje informativo
    """
    st.info(f"ℹ️ {mensaje}")
