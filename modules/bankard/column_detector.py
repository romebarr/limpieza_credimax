"""
Módulo para detectar columnas automáticamente en datos de Bankard.

Contiene funciones para detectar automáticamente las columnas de tipo y exclusión.
"""

import pandas as pd


def detectar_columna_tipo(df):
    """
    Detecta automáticamente la columna de tipo de tarjeta.
    
    Args:
        df: DataFrame con datos de Bankard
        
    Returns:
        str: Nombre de la columna de tipo detectada
    """
    posibles_tipo = ["TIPO ", "TIPO", "Tipo", "TARJETA", "Tipo_Tarjeta", "TIPO_TARJETA"]
    
    for col in posibles_tipo:
        if col in df.columns:
            return col
    
    # Si no se encuentra ninguna, usar la primera que contenga "tipo" (case insensitive)
    for col in df.columns:
        if "tipo" in col.lower():
            return col
    
    # Si no se encuentra ninguna, usar "TIPO " por defecto
    return "TIPO "


def detectar_columna_exclusion(df):
    """
    Detecta automáticamente la columna de exclusión.
    
    Args:
        df: DataFrame con datos de Bankard
        
    Returns:
        str: Nombre de la columna de exclusión detectada
    """
    posibles_exclusion = ["exclusion", "EXCLUSION", "Exclusion", "EXCLUIDO", "Excluido", "EXCLUIR"]
    
    for col in posibles_exclusion:
        if col in df.columns:
            return col
    
    # Si no se encuentra ninguna, usar la primera que contenga "exclu" (case insensitive)
    for col in df.columns:
        if "exclu" in col.lower():
            return col
    
    # Si no se encuentra ninguna, usar "exclusion" por defecto
    return "exclusion"


def detectar_columnas_bankard(df):
    """
    Detecta automáticamente todas las columnas necesarias para Bankard.
    
    Args:
        df: DataFrame con datos de Bankard
        
    Returns:
        dict: Diccionario con las columnas detectadas
    """
    return {
        "col_tipo": detectar_columna_tipo(df),
        "col_exclusion": detectar_columna_exclusion(df)
    }
