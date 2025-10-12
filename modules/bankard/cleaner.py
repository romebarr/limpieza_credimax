"""
Módulo de limpieza de datos para Bankard.

Contiene funciones específicas para limpiar y normalizar datos de Bankard.
"""

import pandas as pd
import numpy as np
from datetime import datetime

from modules.common.validators import extraer_solo_numeros, pad_10_digitos
from modules.common.formatters import a_nombre_propio


def limpiar_cupo_bankard(df):
    """
    Limpia la columna 'cupo' en datos de Bankard, extrayendo solo números.
    
    Args:
        df: DataFrame con datos de Bankard
        
    Returns:
        DataFrame: DataFrame con columna 'cupo' limpia
    """
    df = df.copy()
    if "cupo" not in df.columns:
        df["cupo"] = 0
        return df

    df["cupo"] = df["cupo"].apply(extraer_solo_numeros)
    return df


def filtrar_vigencia_bankard(df):
    """
    Filtra registros de Bankard por vigencia, excluyendo los vencidos.
    
    Busca columnas de vigencia con variaciones de nombre y filtra registros
    cuya fecha de vigencia sea mayor o igual a la fecha actual.
    
    Args:
        df: DataFrame con datos de Bankard
        
    Returns:
        tuple: (df_filtrado, cantidad_excluidos)
    """
    df = df.copy()
    col_vigencia = None
    for posible in ["VIGENICA. BASE", "VIGENCIA. BASE", "VIGENCIA BASE"]:
        if posible in df.columns:
            col_vigencia = posible
            break
    if not col_vigencia:
        return df, 0

    fechas = pd.to_datetime(df[col_vigencia], errors="coerce")
    hoy = datetime.now().date()
    mascara = fechas.dt.date >= hoy
    mascara = mascara.fillna(False)
    excluidos = int((~mascara).sum())
    df_filtrado = df[mascara].copy()
    return df_filtrado, excluidos


def limpiar_telefonos_cedulas_bankard(df):
    """
    Normaliza teléfonos y cédulas en datos de Bankard a formato de 10 dígitos.
    
    Args:
        df: DataFrame con datos de Bankard
        
    Returns:
        DataFrame: DataFrame con teléfonos y cédulas normalizados
    """
    df = df.copy()
    if "telefono" not in df.columns:
        df["telefono"] = ""
    if "cedula" not in df.columns:
        df["cedula"] = ""
    df["telefono"] = df["telefono"].apply(pad_10_digitos)
    df["cedula"] = df["cedula"].apply(pad_10_digitos)
    return df


def limpiar_nombres_bankard(df):
    """
    Limpia y normaliza nombres en formato de nombres propios para Bankard.
    
    Maneja diferentes variaciones de columnas de nombres:
    - primer_nombre (archivos de clientes)
    - Nombres (archivos No Clientes)
    - nombre (columna alternativa)
    
    Args:
        df: DataFrame con datos de Bankard
        
    Returns:
        DataFrame: DataFrame con nombres normalizados
    """
    df = df.copy()
    
    # Limpiar primer_nombre si existe (archivos de clientes)
    if "primer_nombre" in df.columns:
        df["primer_nombre"] = df["primer_nombre"].apply(a_nombre_propio)
    
    # Limpiar Nombres si existe (archivos No Clientes)
    if "Nombres" in df.columns:
        df["Nombres"] = df["Nombres"].apply(a_nombre_propio)
    
    # Limpiar nombre si existe (columna alternativa)
    if "nombre" in df.columns:
        df["nombre"] = df["nombre"].apply(a_nombre_propio)
    
    return df
