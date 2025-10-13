"""
Módulo de asignación automática de campañas para Credimax.

Contiene la lógica para asignar automáticamente la columna 'Campaña Growth'
según las reglas de negocio definidas, con sistema de aprendizaje de nuevas
combinaciones.
"""

import pandas as pd
import streamlit as st
import json
import os
from pathlib import Path


# Ruta al archivo de memoria de reglas personalizadas
MEMORIA_REGLAS_CAMPANAS = "memoria_reglas_campanas.json"


def cargar_memoria_reglas():
    """
    Carga la memoria de reglas personalizadas desde el archivo JSON.
    
    Returns:
        dict: Diccionario con reglas personalizadas {combinacion: campana}
    """
    if os.path.exists(MEMORIA_REGLAS_CAMPANAS):
        try:
            with open(MEMORIA_REGLAS_CAMPANAS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"⚠️ Error al cargar memoria de reglas: {e}")
            return {}
    return {}


def guardar_memoria_reglas(memoria):
    """
    Guarda la memoria de reglas personalizadas en el archivo JSON.
    
    Args:
        memoria: Diccionario con reglas personalizadas
    """
    try:
        with open(MEMORIA_REGLAS_CAMPANAS, "w", encoding="utf-8") as f:
            json.dump(memoria, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"❌ Error al guardar memoria de reglas: {e}")


def crear_clave_combinacion(canal, producto, segmento, testeo):
    """
    Crea una clave única para identificar una combinación de atributos.
    
    Args:
        canal: Valor del canal
        producto: Valor del producto
        segmento: Valor del segmento
        testeo: Valor del testeo de cuota
        
    Returns:
        str: Clave única para la combinación
    """
    return f"{canal}|{producto}|{segmento}|{testeo}"


def parsear_clave_combinacion(clave):
    """
    Parsea una clave de combinación en sus componentes.
    
    Args:
        clave: Clave de combinación
        
    Returns:
        tuple: (canal, producto, segmento, testeo)
    """
    partes = clave.split("|")
    if len(partes) == 4:
        return tuple(partes)
    return ("", "", "", "")


def detectar_casos_sin_regla(df):
    """
    Detecta registros que no tienen una regla de asignación definida.
    
    Args:
        df: DataFrame con datos de Credimax
        
    Returns:
        tuple: (DataFrame con casos sin regla, dict con combinaciones únicas)
    """
    # Columnas necesarias
    columnas_requeridas = ["CANAL", "Producto", "SEGMENTO", "TESTEO CUOTA", "Campaña Growth"]
    
    # Verificar que existen las columnas
    for col in columnas_requeridas:
        if col not in df.columns:
            return pd.DataFrame(), {}
    
    # Filtrar casos sin campaña asignada (vacíos)
    casos_sin_regla = df[df["Campaña Growth"] == ""].copy()
    
    if casos_sin_regla.empty:
        return casos_sin_regla, {}
    
    # Identificar combinaciones únicas
    combinaciones = {}
    for _, row in casos_sin_regla.iterrows():
        canal = str(row.get("CANAL", "")).strip().upper()
        producto = str(row.get("Producto", "")).strip().upper()
        segmento = str(row.get("SEGMENTO", "")).strip().upper()
        testeo = str(row.get("TESTEO CUOTA", "")).strip().upper()
        
        clave = crear_clave_combinacion(canal, producto, segmento, testeo)
        
        if clave not in combinaciones:
            combinaciones[clave] = {
                "CANAL": canal,
                "Producto": producto,
                "SEGMENTO": segmento,
                "TESTEO CUOTA": testeo,
                "count": 0
            }
        combinaciones[clave]["count"] += 1
    
    return casos_sin_regla, combinaciones


def mostrar_interfaz_reglas_interactiva(combinaciones_sin_regla, memoria_reglas):
    """
    Muestra una interfaz interactiva para que el usuario asigne campañas a
    combinaciones que no tienen regla definida.
    
    Args:
        combinaciones_sin_regla: Dict con combinaciones sin regla
        memoria_reglas: Dict con reglas personalizadas existentes
        
    Returns:
        dict: Nuevas reglas asignadas por el usuario
    """
    if not combinaciones_sin_regla:
        return {}
    
    st.warning(f"⚠️ Se encontraron {len(combinaciones_sin_regla)} combinaciones sin regla de asignación")
    st.info("👇 Por favor, asigna la campaña correspondiente a cada combinación. Estas reglas se guardarán para futuras ejecuciones.")
    
    nuevas_reglas = {}
    
    # Campañas disponibles (opciones para el usuario)
    campanas_disponibles = [
        "",  # Opción vacía por defecto
        "Credimax Online No Clientes Afluente",
        "Credimax Online No Clientes Masivo",
        "Credimax Online Elite",
        "Credimax Online Premium",
        "Credimax Online Masivo Cuotas",
        "Credimax Online Masivo",
        "Otra (especificar)"
    ]
    
    for idx, (clave, info) in enumerate(combinaciones_sin_regla.items()):
        st.divider()
        
        # Mostrar información de la combinación
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Combinación {idx + 1}** ({info['count']} registros)")
            st.markdown(f"""
            - **Canal**: `{info['CANAL']}`
            - **Producto**: `{info['Producto']}`
            - **Segmento**: `{info['SEGMENTO']}`
            - **Testeo Cuota**: `{info['TESTEO CUOTA']}`
            """)
        
        with col2:
            st.metric("Registros", info['count'])
        
        # Selector de campaña
        campana_seleccionada = st.selectbox(
            "Selecciona la campaña para esta combinación:",
            options=campanas_disponibles,
            key=f"campana_{clave}",
            help="Esta regla se guardará para futuras ejecuciones"
        )
        
        # Si selecciona "Otra", mostrar input de texto
        if campana_seleccionada == "Otra (especificar)":
            campana_personalizada = st.text_input(
                "Especifica el nombre de la campaña:",
                key=f"campana_custom_{clave}",
                placeholder="Ej: Credimax Online Nueva Campaña"
            )
            if campana_personalizada.strip():
                nuevas_reglas[clave] = campana_personalizada.strip()
        elif campana_seleccionada:
            nuevas_reglas[clave] = campana_seleccionada
    
    # Botón para guardar reglas
    if nuevas_reglas:
        st.divider()
        if st.button("💾 Guardar Reglas en Memoria", type="primary"):
            # Actualizar memoria
            memoria_reglas.update(nuevas_reglas)
            guardar_memoria_reglas(memoria_reglas)
            st.success(f"✅ Se guardaron {len(nuevas_reglas)} nuevas reglas en la memoria")
            st.rerun()
    
    return nuevas_reglas


def aplicar_reglas_personalizadas(df, memoria_reglas):
    """
    Aplica reglas personalizadas almacenadas en la memoria.
    
    Args:
        df: DataFrame con datos de Credimax
        memoria_reglas: Dict con reglas personalizadas
        
    Returns:
        DataFrame: DataFrame con reglas personalizadas aplicadas
    """
    if not memoria_reglas:
        return df
    
    # Preparar columnas
    canal_n = df["CANAL"].fillna("").astype(str).str.strip().str.upper()
    prod_n = df["Producto"].fillna("").astype(str).str.strip().str.upper()
    seg_n = df["SEGMENTO"].fillna("").astype(str).str.strip().str.upper()
    test_n = df["TESTEO CUOTA"].fillna("").astype(str).str.strip().str.upper()
    
    # Aplicar cada regla personalizada
    registros_aplicados = 0
    for clave, campana in memoria_reglas.items():
        canal, producto, segmento, testeo = parsear_clave_combinacion(clave)
        
        # Crear máscara para esta combinación
        mask = (
            (canal_n == canal) &
            (prod_n == producto) &
            (seg_n == segmento) &
            (test_n == testeo)
        )
        
        # Aplicar solo a registros que aún no tienen campaña asignada
        mask_sin_campana = (df["Campaña Growth"] == "")
        mask_final = mask & mask_sin_campana
        
        if mask_final.any():
            df.loc[mask_final, "Campaña Growth"] = campana
            registros_aplicados += mask_final.sum()
    
    if registros_aplicados > 0:
        st.info(f"ℹ️ Se aplicaron {registros_aplicados} reglas personalizadas desde la memoria")
    
    return df


def mostrar_estado_memoria_reglas(memoria_reglas):
    """
    Muestra el estado actual de la memoria de reglas personalizadas.
    
    Args:
        memoria_reglas: Dict con reglas personalizadas
    """
    if memoria_reglas:
        with st.expander(f"📋 Memoria de Reglas Personalizadas ({len(memoria_reglas)} reglas guardadas)"):
            for clave, campana in memoria_reglas.items():
                canal, producto, segmento, testeo = parsear_clave_combinacion(clave)
                st.markdown(f"""
                **{campana}**
                - Canal: `{canal}` | Producto: `{producto}` | Segmento: `{segmento}` | Testeo: `{testeo}`
                """)


def asignar_campanas_automaticamente(df):
    """
    Asigna automáticamente la columna 'Campaña Growth' según reglas de negocio.
    
    Reglas:
    - Canal: ONLINE
    - Producto: No Clientes vs Clientes
    - Segmento: Afluente (ELITE/PREMIUM) vs Masivo (SILVER/PRESTIGE)
    - Testeo de Cuotas: SI/NO
    
    Args:
        df: DataFrame con datos de Credimax
        
    Returns:
        DataFrame: DataFrame con columna 'Campaña Growth' asignada
    """
    # Guardar valor original si existe
    if "Campaña Growth" in df.columns:
        df["Campaña Growth Original"] = df["Campaña Growth"]
    else:
        df["Campaña Growth Original"] = ""
    
    # Verificar que existen las columnas necesarias
    columnas_requeridas = ["CANAL", "Producto", "SEGMENTO", "TESTEO CUOTA"]
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    
    if columnas_faltantes:
        st.warning(f"⚠️ Columnas faltantes para asignación automática: {', '.join(columnas_faltantes)}")
        st.info("ℹ️ Se mantendrán los valores existentes de 'Campaña Growth' o se asignará valor vacío")
        
        # Si no hay columna Campaña Growth, crear una vacía
        if "Campaña Growth" not in df.columns:
            df["Campaña Growth"] = ""
        
        # Retornar estadísticas vacías
        estadisticas = {
            "No Clientes Afluente": 0,
            "No Clientes Masivo": 0,
            "Elite": 0,
            "Premium": 0,
            "Masivo Cuotas": 0,
            "Masivo Sin Cuotas": 0,
        }
        return df, estadisticas
    
    # Preparar columnas necesarias
    canal_n = df["CANAL"].fillna("").astype(str).str.strip().str.upper()
    prod_n = df["Producto"].fillna("").astype(str).str.strip().str.upper()
    seg_n = df["SEGMENTO"].fillna("").astype(str).str.strip().str.upper()
    test_n = df["TESTEO CUOTA"].fillna("").astype(str).str.strip().str.upper()
    
    # Definir máscaras básicas
    is_online = canal_n == "ONLINE"
    is_no_cli = prod_n.str.contains("NO CLIENTES", na=False, case=False)
    is_afluente = seg_n.isin({"ELITE", "PREMIUM"})
    is_masivo = seg_n.isin({"SILVER", "PRESTIGE"})
    test_es_si = test_n.isin({"SI", "1", "TRUE", "X"})
    
    # Crear columna de campaña
    camp_final = pd.Series("", index=df.index, dtype="object")
    
    # Aplicar reglas de segmentación
    mask_no_cli_afl = is_online & is_no_cli & is_afluente
    mask_no_cli_mas = is_online & is_no_cli & is_masivo
    mask_online_otros = is_online & (~is_no_cli)
    mask_elite = mask_online_otros & (seg_n == "ELITE")
    mask_premium = mask_online_otros & (seg_n == "PREMIUM")
    mask_masivo_base = mask_online_otros & is_masivo
    mask_masivo_cuotas = mask_masivo_base & test_es_si
    mask_masivo_sin_cuotas = mask_masivo_base & (~test_es_si)
    
    # Asignar campañas
    camp_final.loc[mask_no_cli_afl] = "Credimax Online No Clientes Afluente"
    camp_final.loc[mask_no_cli_mas] = "Credimax Online No Clientes Masivo"
    camp_final.loc[mask_elite] = "Credimax Online Elite"
    camp_final.loc[mask_premium] = "Credimax Online Premium"
    camp_final.loc[mask_masivo_cuotas] = "Credimax Online Masivo Cuotas"
    camp_final.loc[mask_masivo_sin_cuotas] = "Credimax Online Masivo"
    
    # Asignar al DataFrame
    df["Campaña Growth"] = camp_final
    
    # Estadísticas de asignación
    estadisticas = {
        "No Clientes Afluente": int(mask_no_cli_afl.sum()),
        "No Clientes Masivo": int(mask_no_cli_mas.sum()),
        "Elite": int(mask_elite.sum()),
        "Premium": int(mask_premium.sum()),
        "Masivo Cuotas": int(mask_masivo_cuotas.sum()),
        "Masivo Sin Cuotas": int(mask_masivo_sin_cuotas.sum()),
    }
    
    return df, estadisticas


def mostrar_estadisticas_campanas(estadisticas):
    """
    Muestra las estadísticas de asignación de campañas.
    
    Args:
        estadisticas: Diccionario con estadísticas de asignación
    """
    st.subheader("🧠 Asignación Automática de Campañas")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("No Clientes Afluente", estadisticas.get("No Clientes Afluente", 0))
        st.metric("Masivo Sin Cuotas", estadisticas.get("Masivo Sin Cuotas", 0))
    with col2:
        st.metric("No Clientes Masivo", estadisticas.get("No Clientes Masivo", 0))
        st.metric("Elite", estadisticas.get("Elite", 0))
    with col3:
        st.metric("Masivo Cuotas", estadisticas.get("Masivo Cuotas", 0))
        st.metric("Premium", estadisticas.get("Premium", 0))

