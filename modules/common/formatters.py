"""
Módulo de formateo común para Credimax y Bankard.

Contiene funciones para formatear nombres, números, cupos y otros campos.
"""

import re
import unicodedata
import pandas as pd
import numpy as np


def a_nombre_propio(s):
    """
    Convierte texto a formato de nombres propios (Primera Letra Mayúscula).
    
    Args:
        s: Texto a convertir
        
    Returns:
        str: Texto en formato de nombres propios o valor original si es NaN
    """
    if pd.isna(s):
        return s
    limpio = " ".join(str(s).strip().split())
    return limpio.title()


def cupo_a_texto_miles_coma(valor):
    """
    Convierte un valor numérico a texto con comas como separadores de miles.
    
    Ejemplos:
    - 1000 -> '1,000'
    - '1.000' -> '1,000'
    - 'abc' -> NaN
    
    Args:
        valor: Valor a convertir (puede ser string, int, float)
        
    Returns:
        str: Valor formateado con comas o np.nan si no es válido
    """
    if pd.isna(valor):
        return np.nan
    s = str(valor).strip()
    if s == "":
        return np.nan
    dig = re.sub(r"\D+", "", s)
    if dig == "":
        return np.nan
    num = int(dig)
    return f"{num:,}"


def strip_accents(s: str) -> str:
    """
    Remueve acentos y caracteres especiales de un texto.
    
    Args:
        s: Texto a procesar
        
    Returns:
        str: Texto sin acentos
    """
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(v: str) -> str:
    """
    Normaliza texto para comparaciones: remueve acentos, espacios extra y convierte a mayúsculas.
    
    Args:
        v: Texto a normalizar
        
    Returns:
        str: Texto normalizado en mayúsculas sin acentos
    """
    if pd.isna(v):
        return ""
    s = str(v).strip()
    s = strip_accents(s)
    s = re.sub(r"\s+", " ", s)
    return s.upper()


def formatear_cuota(valor):
    """
    Formatea un valor como cuota con 2 decimales.
    
    Args:
        valor: Valor a formatear
        
    Returns:
        str: Valor formateado con 2 decimales o np.nan si no es válido
    """
    if pd.isna(valor):
        return np.nan
    s = str(valor).strip().replace(",", ".")
    if s == "":
        return np.nan
    try:
        return f"{float(s):.2f}"
    except ValueError:
        return np.nan


def safe_filename(s: str) -> str:
    """
    Convierte un texto en un nombre de archivo seguro removiendo caracteres especiales.
    
    Args:
        s: Texto a convertir
        
    Returns:
        str: Nombre de archivo seguro
    """
    return (
        str(s)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "")
        .replace("*", "")
        .replace("?", "")
        .replace('"', "")
        .replace("<", "")
        .replace(">", "")
        .replace("|", "")
        .strip()
    )
