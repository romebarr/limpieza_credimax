"""
Módulo de asignación automática de campañas para Credimax.

Contiene la lógica para asignar automáticamente la columna 'Campaña Growth'
según las reglas de negocio definidas.
"""

import pandas as pd
import streamlit as st


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
    
    # Preparar columnas necesarias
    canal_n = df["CANAL"].fillna("").astype(str).str.strip().str.upper()
    prod_n = df["PRODUCTO"].fillna("").astype(str).str.strip().str.upper()
    seg_n = df["SEGMENTO"].fillna("").astype(str).str.strip().str.upper()
    test_n = df["TESTEO_CUOTAS"].fillna("").astype(str).str.strip().str.upper()
    
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

