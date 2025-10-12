"""
Módulo del sistema inteligente de corrección de BINs para Bankard.

Contiene la funcionalidad para detectar, sugerir y corregir BINs automáticamente.
"""

import json
import difflib
import pandas as pd
from pathlib import Path
from datetime import datetime


# BINs permitidos
VALORES_BIN_PERMITIDOS = [
    "Visa Oro",
    "Visa Platinum", 
    "Mastercard Black",
    "Mastercard Clásica",
    "Mastercard Oro",
    "Visa Clásica",
    "Visa Infinite",
    "Visa Signature",
]

# Rutas de archivos
MEMORIA_CORRECCIONES_PATH = Path("memoria_correcciones_bin.json")
MEMORIA_ESTADISTICAS_PATH = Path("memoria_estadisticas_bin.json")


def cargar_memoria_correcciones():
    """
    Carga la memoria de correcciones de BINs desde archivo JSON.
    
    Returns:
        dict: Diccionario con correcciones guardadas
    """
    if MEMORIA_CORRECCIONES_PATH.exists():
        try:
            with open(MEMORIA_CORRECCIONES_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            return {}
    return {}


def cargar_estadisticas_bin():
    """
    Carga las estadísticas de uso de BINs desde archivo JSON.
    
    Returns:
        dict: Diccionario con estadísticas de uso
    """
    if MEMORIA_ESTADISTICAS_PATH.exists():
        try:
            with open(MEMORIA_ESTADISTICAS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            return {}
    return {}


def guardar_memoria_correcciones(memoria):
    """
    Guarda la memoria de correcciones en archivo JSON.
    
    Args:
        memoria: Diccionario con correcciones a guardar
    """
    with open(MEMORIA_CORRECCIONES_PATH, 'w', encoding='utf-8') as f:
        json.dump(memoria, f, ensure_ascii=False, indent=2)


def guardar_estadisticas_bin(estadisticas):
    """
    Guarda las estadísticas de uso en archivo JSON.
    
    Args:
        estadisticas: Diccionario con estadísticas a guardar
    """
    with open(MEMORIA_ESTADISTICAS_PATH, 'w', encoding='utf-8') as f:
        json.dump(estadisticas, f, ensure_ascii=False, indent=2)


def calcular_similitud_bin(bin_original, bin_candidato):
    """
    Calcula la similitud entre dos BINs usando el algoritmo de Levenshtein.
    
    Args:
        bin_original: BIN original problemático
        bin_candidato: BIN candidato para corrección
        
    Returns:
        float: Similitud entre 0 y 1 (1 = idéntico)
    """
    if not bin_original or not bin_candidato:
        return 0.0
    
    # Normalizar textos
    orig = str(bin_original).strip().upper()
    cand = str(bin_candidato).strip().upper()
    
    if orig == cand:
        return 1.0
    
    # Calcular similitud usando SequenceMatcher
    similarity = difflib.SequenceMatcher(None, orig, cand).ratio()
    return similarity


def generar_sugerencias_inteligentes(bin_problema, memoria_correcciones, estadisticas):
    """
    Genera sugerencias inteligentes para un BIN problemático.
    
    Args:
        bin_problema: BIN problemático a corregir
        memoria_correcciones: Diccionario de correcciones previas
        estadisticas: Diccionario de estadísticas de uso
        
    Returns:
        list: Lista de sugerencias ordenadas por similitud
    """
    if not bin_problema:
        return []
    
    sugerencias = []
    bin_problema_norm = str(bin_problema).strip().upper()
    
    # 1. Buscar en memoria de correcciones
    if bin_problema_norm in memoria_correcciones:
        correccion = memoria_correcciones[bin_problema_norm]
        if correccion:
            sugerencias.append((correccion, 1.0, "memoria"))
    
    # 2. Buscar en BINs permitidos por similitud
    for bin_permitido in VALORES_BIN_PERMITIDOS:
        similitud = calcular_similitud_bin(bin_problema, bin_permitido)
        if similitud > 0.3:  # Umbral mínimo de similitud
            sugerencias.append((bin_permitido, similitud, "similitud"))
    
    # 3. Buscar en estadísticas de uso
    if bin_problema_norm in estadisticas:
        uso_data = estadisticas[bin_problema_norm]
        if "correcciones_frecuentes" in uso_data:
            for correccion, frecuencia in uso_data["correcciones_frecuentes"].items():
                if frecuencia > 0:
                    similitud = calcular_similitud_bin(bin_problema, correccion)
                    sugerencias.append((correccion, similitud * 0.8, "frecuencia"))
    
    # Ordenar por similitud descendente
    sugerencias.sort(key=lambda x: x[1], reverse=True)
    
    # Retornar solo los valores únicos
    valores_unicos = []
    valores_vistos = set()
    for valor, similitud, fuente in sugerencias:
        if valor not in valores_vistos:
            valores_unicos.append(valor)
            valores_vistos.add(valor)
    
    return valores_unicos[:5]  # Máximo 5 sugerencias


def actualizar_estadisticas_bin(bin_original, bin_corregido, estadisticas):
    """
    Actualiza las estadísticas de uso de BINs.
    
    Args:
        bin_original: BIN original problemático
        bin_corregido: BIN corregido
        estadisticas: Diccionario de estadísticas
    """
    bin_original_norm = str(bin_original).strip().upper()
    bin_corregido_norm = str(bin_corregido).strip().upper()
    
    if bin_original_norm not in estadisticas:
        estadisticas[bin_original_norm] = {
            "total_usos": 0,
            "correcciones_frecuentes": {},
            "ultima_correccion": None
        }
    
    # Actualizar contadores
    estadisticas[bin_original_norm]["total_usos"] += 1
    estadisticas[bin_original_norm]["ultima_correccion"] = datetime.now().isoformat()
    
    # Actualizar correcciones frecuentes
    if bin_corregido_norm not in estadisticas[bin_original_norm]["correcciones_frecuentes"]:
        estadisticas[bin_original_norm]["correcciones_frecuentes"][bin_corregido_norm] = 0
    estadisticas[bin_original_norm]["correcciones_frecuentes"][bin_corregido_norm] += 1


def detectar_bins_no_permitidos_inteligente(df, memoria_correcciones, estadisticas):
    """
    Detecta BINs no permitidos y genera sugerencias inteligentes.
    
    Args:
        df: DataFrame con datos de Bankard
        memoria_correcciones: Diccionario de correcciones previas
        estadisticas: Diccionario de estadísticas de uso
        
    Returns:
        tuple: (bins_problematicos, sugerencias_automaticas)
    """
    if "BIN" not in df.columns:
        return [], {}
    
    valores_actuales = df["BIN"].dropna().unique()
    bins_problematicos = []
    sugerencias_automaticas = {}
    
    for valor in valores_actuales:
        if valor not in VALORES_BIN_PERMITIDOS and valor not in memoria_correcciones:
            bins_problematicos.append(valor)
            # Generar sugerencias automáticas
            sugerencias = generar_sugerencias_inteligentes(valor, memoria_correcciones, estadisticas)
            if sugerencias:
                sugerencias_automaticas[valor] = sugerencias
    
    return bins_problematicos, sugerencias_automaticas


def aplicar_correcciones_bin(df, memoria_correcciones, estadisticas=None):
    """
    Aplica correcciones de BINs basadas en memoria y estadísticas.
    
    Args:
        df: DataFrame con datos de Bankard
        memoria_correcciones: Diccionario de correcciones previas
        estadisticas: Diccionario de estadísticas de uso (opcional)
        
    Returns:
        DataFrame: DataFrame con BINs corregidos
    """
    if "BIN" not in df.columns:
        return df
    
    def corregir(valor):
        if pd.isna(valor):
            return valor
        val = str(valor).strip()
        
        # Si ya está en memoria de correcciones, usarlo
        if val in memoria_correcciones and memoria_correcciones[val]:
            correccion = memoria_correcciones[val]
            # Actualizar estadísticas si están disponibles
            if estadisticas is not None:
                actualizar_estadisticas_bin(val, correccion, estadisticas)
            return correccion
        
        # Si ya es válido, mantenerlo
        if val in VALORES_BIN_PERMITIDOS:
            return val
        
        # Si no es válido, intentar sugerencias automáticas
        if estadisticas is not None:
            sugerencias = generar_sugerencias_inteligentes(val, memoria_correcciones, estadisticas)
            if sugerencias:
                # Usar la primera sugerencia automáticamente si tiene confianza moderada
                primera_sugerencia = sugerencias[0]
                similitud = calcular_similitud_bin(val, primera_sugerencia)
                # Reducir umbral a 0.6 para ser más permisivo
                if similitud > 0.6:
                    actualizar_estadisticas_bin(val, primera_sugerencia, estadisticas)
                    return primera_sugerencia
        
        # Si no hay sugerencias buenas, intentar normalizar el texto
        val_normalizado = val.title()
        # Verificar si el valor normalizado está en los permitidos
        if val_normalizado in VALORES_BIN_PERMITIDOS:
            return val_normalizado
        
        return val  # Mantener valor original si no se puede corregir
    
    df["BIN"] = df["BIN"].apply(corregir)
    return df
