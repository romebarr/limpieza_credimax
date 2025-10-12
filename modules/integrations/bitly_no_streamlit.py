"""
Módulo de integración con Bitly para acortamiento de enlaces (versión sin streamlit).

Contiene la funcionalidad para acortar enlaces usando la API de Bitly.
"""

import requests

# Configuración Bitly
BITLY_ACCESS_TOKEN = "d9dad23cd1329e489dcbe9c52cd1770e856c50d5"
BITLY_DOMAIN = "mkt-bb.com"
BITLY_API_URL = "https://api-ssl.bitly.com/v4/shorten"


def acortar_enlace_bitly(url_larga):
    """
    Acorta un enlace usando la API de Bitly con dominio personalizado.
    
    Args:
        url_larga: URL original a acortar
        
    Returns:
        str: URL acortada o URL original si falla la API
        
    Note:
        - Usa el token de acceso configurado en BITLY_ACCESS_TOKEN
        - Usa el dominio personalizado mkt-bb.com
        - Timeout de 10 segundos para evitar bloqueos
        - Si falla, retorna el enlace original
    """
    if not url_larga or not url_larga.strip():
        return url_larga
    
    try:
        headers = {
            "Authorization": f"Bearer {BITLY_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "long_url": url_larga.strip(),
            "domain": BITLY_DOMAIN
        }
        
        response = requests.post(BITLY_API_URL, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            return result.get("link", url_larga)
        else:
            # Si falla la API, devolver el enlace original
            print(f"⚠️ No se pudo acortar el enlace: {response.status_code}")
            return url_larga
            
    except Exception as e:
        # Si hay cualquier error, devolver el enlace original
        print(f"⚠️ Error al acortar enlace: {str(e)}")
        return url_larga
