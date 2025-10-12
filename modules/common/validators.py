"""
Módulo de validaciones comunes para Credimax y Bankard.

Contiene funciones para validar cédulas, celulares y otros campos críticos.
"""

import re
import pandas as pd
import numpy as np


def validar_cedula_10(cedula):
    """
    Valida que una cédula ecuatoriana tenga exactamente 10 dígitos.
    
    Args:
        cedula: Valor a validar (puede ser string, int, float, etc.)
        
    Returns:
        bool: True si la cédula tiene 10 dígitos, False en caso contrario
    """
    if pd.isna(cedula):
        return False
    dig = re.sub(r"\D+", "", str(cedula))
    return len(dig) == 10


def normalizar_celular_ec(valor):
    """
    Normaliza números de celular ecuatorianos a formato estándar de 10 dígitos.
    
    Reglas:
    - Si tiene 10 dígitos: se mantiene
    - Si tiene 9 dígitos y no empieza con '0': se antepone '0'
    - Cualquier otro caso: se retorna NaN
    
    Args:
        valor: Número de celular a normalizar
        
    Returns:
        str: Celular normalizado de 10 dígitos o np.nan si no es válido
    """
    if pd.isna(valor):
        return np.nan
    dig = re.sub(r"\D+", "", str(valor))
    if len(dig) == 10:
        return dig
    if len(dig) == 9 and dig[0] != "0":
        return "0" + dig
    return np.nan


def pad_10_digitos(valor):
    """
    Normaliza un valor a exactamente 10 dígitos, rellenando con ceros a la izquierda.
    
    Args:
        valor: Valor a normalizar (puede ser string, int, float)
        
    Returns:
        str: Valor normalizado a 10 dígitos o cadena vacía si no es válido
    """
    if pd.isna(valor):
        return ""
    s = re.sub(r"\D", "", str(valor))
    if s == "":
        return ""
    if len(s) < 10:
        s = s.zfill(10)
    elif len(s) > 10:
        s = s[:10]
    return s


def extraer_solo_numeros(valor):
    """
    Extrae solo dígitos de un valor y los convierte a entero.
    
    Args:
        valor: Valor a procesar (puede ser string, int, float)
        
    Returns:
        int: Número extraído o 0 si no hay dígitos válidos
    """
    if pd.isna(valor):
        return 0
    dig = re.sub(r"[^0-9]", "", str(valor))
    if dig == "":
        return 0
    return int(dig)
