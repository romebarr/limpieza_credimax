"""
Módulos de la aplicación Limpieza Credimax & Bankard.

Este paquete contiene todos los módulos organizados por funcionalidad:
- common: Funciones comunes de validación y formateo
- integrations: Integraciones externas (Bitly, etc.)
- credimax: Lógica específica de Credimax
- bankard: Lógica específica de Bankard
- ui: Componentes de interfaz de usuario
"""

__version__ = "2.0.0"
__author__ = "SM Growth Lab"
__description__ = "Módulos para limpieza y procesamiento de datos Credimax & Bankard"

# Imports principales para facilitar el uso
from .common.validators import validar_cedula_10, normalizar_celular_ec
from .common.formatters import a_nombre_propio, cupo_a_texto_miles_coma
from .common.utils import df_to_excel_bytes

# Imports de integraciones
from .integrations.bitly import acortar_enlace_bitly

# Imports de Credimax
from .credimax.processor import preparar_zip_por_campana

# Imports de Bankard
from .bankard.processor import preparar_zip_bankard
from .bankard.cleaner import limpiar_cupo_bankard, limpiar_nombres_bankard
from .bankard.exclusions import cargar_exclusiones_consolidadas
from .bankard.bin_corrector import cargar_memoria_correcciones, calcular_similitud_bin

__all__ = [
    # Common
    "validar_cedula_10",
    "normalizar_celular_ec", 
    "a_nombre_propio",
    "cupo_a_texto_miles_coma",
    "df_to_excel_bytes",
    
    # Integrations
    "acortar_enlace_bitly",
    
    # Credimax
    "preparar_zip_por_campana",
    
    # Bankard
    "preparar_zip_bankard",
    "limpiar_cupo_bankard",
    "limpiar_nombres_bankard",
    "cargar_exclusiones_consolidadas",
    "cargar_memoria_correcciones",
    "calcular_similitud_bin",
]
