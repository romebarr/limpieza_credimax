"""
Módulo de UI principal para la aplicación.

Contiene la configuración principal y navegación de la interfaz.
"""

import streamlit as st
from modules.ui.common_ui import mostrar_info_configuracion


def configurar_pagina():
    """
    Configura la página principal de Streamlit.
    """
    st.set_page_config(
        page_title="Limpieza Credimax – SM Growth Lab", 
        layout="wide",
        initial_sidebar_state="expanded"
    )


def mostrar_header():
    """
    Muestra el encabezado principal de la aplicación.
    """
    st.title("🧹 Limpieza y Exportación – Credimax & Bankard")
    st.caption(
        "Sube la base correspondiente, aplicamos validaciones/normalizaciones y preparamos las "
        "descargas segmentadas según las reglas de cada flujo."
    )


def mostrar_selector_flujo():
    """
    Muestra el selector de flujo en la barra lateral.
    
    Returns:
        str: Flujo seleccionado ('credimax' o 'bankard')
    """
    st.sidebar.header("🚀 Seleccionar Flujo")
    
    flujo = st.sidebar.radio(
        "¿Qué base quieres procesar?",
        ["Credimax", "Bankard"],
        help="Selecciona el tipo de base de datos a procesar"
    )
    
    return flujo.lower()


def mostrar_info_flujo(flujo):
    """
    Muestra información específica del flujo seleccionado.
    
    Args:
        flujo: Flujo seleccionado ('credimax' o 'bankard')
    """
    if flujo == "credimax":
        st.info("""
        **🏦 Flujo Credimax:**
        - Validación de cédulas, celulares y nombres
        - Segmentación automática por campaña
        - Generación de plantillas SMS personalizables
        - Exportación segmentada por campaña
        """)
    elif flujo == "bankard":
        st.info("""
        **🏛️ Flujo Bankard:**
        - Sistema inteligente de corrección de BINs
        - Gestión consolidada de exclusiones
        - Filtrado por vigencia
        - Generación de plantillas SMS por tipo de tarjeta
        """)


def mostrar_uploader_archivo(flujo):
    """
    Muestra el uploader de archivos específico para cada flujo.
    
    Args:
        flujo: Flujo seleccionado ('credimax' o 'bankard')
        
    Returns:
        UploadedFile: Archivo subido o None
    """
    if flujo == "credimax":
        archivo = st.file_uploader(
            "📁 Subir base de Credimax",
            type=["xlsx", "xls"],
            help="Sube un archivo Excel con la base de Credimax"
        )
    elif flujo == "bankard":
        archivo = st.file_uploader(
            "📁 Subir base de Bankard",
            type=["xlsx", "xls"],
            help="Sube un archivo Excel con la base de Bankard"
        )
    else:
        archivo = None
    
    return archivo


def mostrar_uploader_exclusiones():
    """
    Muestra el uploader de archivos de exclusiones (solo para Bankard).
    
    Returns:
        list: Lista de archivos de exclusiones subidos
    """
    st.sidebar.subheader("📋 Archivos de Exclusión")
    
    exclusion_files = st.sidebar.file_uploader(
        "Subir archivos de exclusión",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        help="Sube archivos Excel con cédulas a excluir (columna IDENTIFICACION)"
    )
    
    return exclusion_files


def mostrar_estado_procesamiento(estado, mensaje=""):
    """
    Muestra el estado actual del procesamiento.
    
    Args:
        estado: Estado del procesamiento ('cargando', 'procesando', 'completado', 'error')
        mensaje: Mensaje adicional a mostrar
    """
    if estado == "cargando":
        st.info("📥 Cargando archivo...")
    elif estado == "procesando":
        st.info(f"🔄 Procesando datos... {mensaje}")
    elif estado == "completado":
        st.success(f"✅ Procesamiento completado! {mensaje}")
    elif estado == "error":
        st.error(f"❌ Error en el procesamiento: {mensaje}")


def mostrar_sidebar_info():
    """
    Muestra información adicional en la barra lateral.
    """
    st.sidebar.divider()
    st.sidebar.markdown("### ℹ️ Información")
    st.sidebar.markdown("""
    **Versión:** 2.0.0  
    **Equipo:** SM Growth Lab  
    **Última actualización:** 2024
    """)
    
    # Enlaces removidos de la interfaz - solo en documentación


def limpiar_cache():
    """
    Limpia el cache de Streamlit si es necesario.
    """
    if st.button("🧹 Limpiar Cache", help="Limpia el cache de la aplicación"):
        st.cache_data.clear()
        st.rerun()


def mostrar_footer():
    """
    Muestra el pie de página de la aplicación.
    """
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        <p>Desarrollado por <strong>SM Growth Lab</strong></p>
    </div>
    """, unsafe_allow_html=True)
