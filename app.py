import io
import json
import re
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st

# =============================
# Config básica
# =============================
st.set_page_config(page_title="Limpieza Credimax – SM Growth Lab", layout="wide")
st.title("🧹 Limpieza y Exportación – Credimax & Bankard")
st.caption(
    "Sube la base correspondiente, aplicamos validaciones/normalizaciones y preparamos las "
    "descargas segmentadas según las reglas de cada flujo."
)

# =============================
# Helpers – Credimax
# =============================
COLUMNAS_ESPERADAS = [
    "MIS",
    "CEDULA",
    "FECHA NACIMIENTO",
    "primer_nombre",
    "primer_apellido",
    "CELULAR",
    "CORREO CLIENTE",
    "SEGMENTO",
    "CUPO",
    "Plazo",
    "Tasa",
    "Ind_Tasa_Exclusiva",
    "Vigencia",
    "Ind_Campaña_Vigente",
    "Producto",
    "Ind_Perfil_Campaña",
    "CANAL",
    "IND_DESEMBOLSO",
    "Campaña Growth",
    "CUPO_TARJETA_BK",
    "MARCA_TARJETA_BK",
    "BASE MARIO",
    "CUOTA",
    "TESTEO CUOTA",
]

SEG_AFL = {"ELITE", "PREMIUM"}  # Afluente
SEG_MAS = {"SILVER", "PRESTIGE"}  # Masivo

MARCAS_VALIDAS_DEFAULT = [
    "Visa Clásica",
    "Visa Oro",
    "Visa Infinite",
    "Visa Platinum",
    "Visa Signature",
]

# =============================
# Helpers – Bankard
# =============================
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

MEMORIA_CORRECCIONES_PATH = Path("memoria_correcciones_bin.json")
MEMORIA_ESTADISTICAS_PATH = Path("memoria_estadisticas_bin.json")
EXCLUSIONES_BANKARD_DIR = Path("data/exclusiones_bankard")
EXCLUSIONES_CONSOLIDADAS_PATH = Path("exclusiones_consolidadas.json")
EXCLUSIONES_BANKARD_DIR.mkdir(parents=True, exist_ok=True)

# =============================
# Configuración Bitly
# =============================
BITLY_ACCESS_TOKEN = "d9dad23cd1329e489dcbe9c52cd1770e856c50d5"
BITLY_DOMAIN = "mkt-bb.com"
BITLY_API_URL = "https://api-ssl.bitly.com/v4/shorten"

# =============================
# Funciones comunes
# =============================
def validar_cedula_10(cedula):
    if pd.isna(cedula):
        return False
    dig = re.sub(r"\D+", "", str(cedula))
    return len(dig) == 10


def normalizar_celular_ec(valor):
    """Extrae dígitos; si 10 -> ok; si 9 y primero != '0' -> anteponer '0'; caso contrario -> NaN."""
    if pd.isna(valor):
        return np.nan
    dig = re.sub(r"\D+", "", str(valor))
    if len(dig) == 10:
        return dig
    if len(dig) == 9 and dig[0] != "0":
        return "0" + dig
    return np.nan


def a_nombre_propio(s):
    if pd.isna(s):
        return s
    limpio = " ".join(str(s).strip().split())
    return limpio.title()


def cupo_a_texto_miles_coma(valor):
    """Convierte a texto con coma como separador de miles. 1000 -> '1,000'; '1.000' -> '1,000'."""
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
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(v: str) -> str:
    if pd.isna(v):
        return ""
    s = str(v).strip()
    s = strip_accents(s)
    s = re.sub(r"\s+", " ", s)
    return s.upper()


def formatear_cuota(valor):
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


def acortar_enlace_bitly(url_larga):
    """Acorta un enlace usando Bitly API"""
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
            st.warning(f"⚠️ No se pudo acortar el enlace: {response.status_code}")
            return url_larga
            
    except Exception as e:
        # Si hay cualquier error, devolver el enlace original
        st.warning(f"⚠️ Error al acortar enlace: {str(e)}")
        return url_larga


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "base", header: bool = True) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name, header=header)
    buf.seek(0)
    return buf.read()


def pad_10_digitos(valor):
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

# =============================
# Funciones específicas Credimax
# =============================
def preparar_zip_por_campana(df: pd.DataFrame, col_campana: str = "Campaña Growth"):
    """Genera el ZIP segmentado por campaña y devuelve (bytes_zip, columnas_exportadas)."""
    columnas_necesarias = {
        col_campana,
        "IND_DESEMBOLSO",
        "CELULAR",
        "primer_nombre",
        "CORREO CLIENTE",
        "CUPO",
        "CUOTA",
        "Tasa",
        "CUPO_TARJETA_BK",
        "MARCA_TARJETA_BK",
    }

    df_trabajo = df.copy()
    for col in columnas_necesarias:
        if col not in df_trabajo.columns:
            df_trabajo[col] = np.nan

    df_exp = df_trabajo[df_trabajo["IND_DESEMBOLSO"] == "0"].copy()
    df_exp[col_campana] = df_exp[col_campana].astype(str).str.strip()
    mask_no_vacio = (
        df_exp[col_campana].notna()
        & (df_exp[col_campana] != "")
        & (~df_exp[col_campana].str.lower().eq("nan"))
    )
    df_exp = df_exp[mask_no_vacio].copy()

    if df_exp.empty:
        return None, []

    # Mapeo columnas de salida (primer_nombre => nombre)
    mapeo_columnas = {
        "primer_nombre": "nombre",             # <- solicitado
        "CORREO CLIENTE": "correo",
        "CUPO": "monto_credito_aprob",
        "CUOTA": "cuota_credimax",
        "Tasa": "Tasa_Credito_Aprob",
        "CUPO_TARJETA_BK": "Cupo_Aprobado_OB_BK",
        "MARCA_TARJETA_BK": "Marca_BK_OB",
    }

    df_exp["CUOTA"] = df_exp["CUOTA"].apply(formatear_cuota)

    columnas_originales = list(mapeo_columnas.keys()) + [col_campana, "CELULAR"]
    df_exp = df_exp[columnas_originales].copy()
    df_exp = df_exp.rename(columns=mapeo_columnas)

    def cel_10(s):
        if pd.isna(s):
            return np.nan
        dig = re.sub(r"\D+", "", str(s))
        return dig if len(dig) == 10 else s

    df_exp["CELULAR"] = df_exp["CELULAR"].apply(cel_10)

    columnas_exportadas = [
        "CELULAR",
        "nombre",
        "correo",
        "monto_credito_aprob",
        "cuota_credimax",
        "Tasa_Credito_Aprob",
        "Cupo_Aprobado_OB_BK",
        "Marca_BK_OB",
    ]

    for col in columnas_exportadas:
        if col not in df_exp.columns:
            df_exp[col] = np.nan

    fecha_archivo = datetime.now().strftime("%d-%m")
    zip_buf = io.BytesIO()

    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for nombre, grupo in df_exp.groupby(col_campana, dropna=False):
            if pd.isna(nombre):
                continue
            nombre_archivo = safe_filename(nombre)
            if not nombre_archivo or nombre_archivo.lower() == "nan":
                continue

            grupo_salida = grupo.drop(columns=[col_campana]).copy()
            grupo_salida = grupo_salida.reindex(columns=columnas_exportadas)
            excel_bytes = df_to_excel_bytes(grupo_salida, sheet_name="base")
            zf.writestr(f"{nombre_archivo}_{fecha_archivo}.xlsx", excel_bytes)

    zip_buf.seek(0)
    return zip_buf.read(), columnas_exportadas

# =============================
# Funciones específicas Bankard
# =============================
def cargar_memoria_correcciones():
    """Carga las correcciones manuales de BINs"""
    if MEMORIA_CORRECCIONES_PATH.exists():
        try:
            return json.loads(MEMORIA_CORRECCIONES_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def cargar_estadisticas_bin():
    """Carga estadísticas de uso y patrones de BINs"""
    if MEMORIA_ESTADISTICAS_PATH.exists():
        try:
            return json.loads(MEMORIA_ESTADISTICAS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "frecuencias": {},
                "sugerencias": {},
                "patrones": {},
                "ultima_actualizacion": None
            }
    return {
        "frecuencias": {},
        "sugerencias": {},
        "patrones": {},
        "ultima_actualizacion": None
    }


def guardar_memoria_correcciones(memoria):
    """Guarda las correcciones manuales de BINs"""
    MEMORIA_CORRECCIONES_PATH.write_text(
        json.dumps(memoria, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def guardar_estadisticas_bin(estadisticas):
    """Guarda las estadísticas de uso de BINs"""
    estadisticas["ultima_actualizacion"] = datetime.now().isoformat()
    MEMORIA_ESTADISTICAS_PATH.write_text(
        json.dumps(estadisticas, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def calcular_similitud_bin(bin_original, bin_candidato):
    """Calcula similitud entre dos BINs usando distancia de Levenshtein normalizada"""
    if not bin_original or not bin_candidato:
        return 0.0
    
    s1, s2 = str(bin_original).lower().strip(), str(bin_candidato).lower().strip()
    if s1 == s2:
        return 1.0
    
    # Distancia de Levenshtein simple
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1.0 - (distance / max_len) if max_len > 0 else 0.0


def generar_sugerencias_inteligentes(bin_problema, memoria_correcciones, estadisticas):
    """Genera sugerencias inteligentes para un BIN problemático"""
    sugerencias = []
    
    # 1. Buscar en correcciones manuales existentes
    if bin_problema in memoria_correcciones:
        return [memoria_correcciones[bin_problema]]
    
    # 2. Buscar por similitud en BINs válidos
    similitudes = []
    for bin_valido in VALORES_BIN_PERMITIDOS:
        similitud = calcular_similitud_bin(bin_problema, bin_valido)
        if similitud > 0.3:  # Umbral mínimo de similitud
            similitudes.append((bin_valido, similitud))
    
    # Ordenar por similitud descendente
    similitudes.sort(key=lambda x: x[1], reverse=True)
    sugerencias.extend([bin_valido for bin_valido, _ in similitudes[:3]])
    
    # 3. Buscar en patrones históricos
    if bin_problema in estadisticas.get("patrones", {}):
        patrones = estadisticas["patrones"][bin_problema]
        # Ordenar por frecuencia de uso
        patrones_ordenados = sorted(patrones.items(), key=lambda x: x[1], reverse=True)
        sugerencias.extend([patron for patron, _ in patrones_ordenados[:2]])
    
    # 4. Buscar sugerencias previamente generadas
    if bin_problema in estadisticas.get("sugerencias", {}):
        sugerencias_previas = estadisticas["sugerencias"][bin_problema]
        sugerencias.extend(sugerencias_previas[:2])
    
    # Eliminar duplicados manteniendo orden
    sugerencias_unicas = []
    for sug in sugerencias:
        if sug not in sugerencias_unicas:
            sugerencias_unicas.append(sug)
    
    return sugerencias_unicas[:5]  # Máximo 5 sugerencias


def actualizar_estadisticas_bin(bin_original, bin_corregido, estadisticas):
    """Actualiza las estadísticas cuando se usa una corrección"""
    if not bin_original or not bin_corregido:
        return
    
    bin_orig = str(bin_original).strip()
    bin_corr = str(bin_corregido).strip()
    
    # Actualizar frecuencias
    if "frecuencias" not in estadisticas:
        estadisticas["frecuencias"] = {}
    
    if bin_orig not in estadisticas["frecuencias"]:
        estadisticas["frecuencias"][bin_orig] = {}
    
    if bin_corr not in estadisticas["frecuencias"][bin_orig]:
        estadisticas["frecuencias"][bin_orig][bin_corr] = 0
    
    estadisticas["frecuencias"][bin_orig][bin_corr] += 1
    
    # Actualizar patrones (más generales)
    if "patrones" not in estadisticas:
        estadisticas["patrones"] = {}
    
    if bin_orig not in estadisticas["patrones"]:
        estadisticas["patrones"][bin_orig] = {}
    
    if bin_corr not in estadisticas["patrones"][bin_orig]:
        estadisticas["patrones"][bin_orig][bin_corr] = 0
    
    estadisticas["patrones"][bin_orig][bin_corr] += 1


def detectar_bins_no_permitidos_inteligente(df, memoria_correcciones, estadisticas):
    """Detecta BINs no permitidos y genera sugerencias automáticas"""
    if "BIN" not in df.columns:
        return [], {}
    
    valores_actuales = {
        str(x).strip() for x in df["BIN"].dropna().unique().tolist()
    }
    permitidos = set(VALORES_BIN_PERMITIDOS)
    memorizados = set(memoria_correcciones.keys())
    
    bins_problematicos = []
    sugerencias_automaticas = {}
    
    for valor in valores_actuales:
        if valor not in permitidos and valor not in memorizados:
            bins_problematicos.append(valor)
            # Generar sugerencias automáticas
            sugerencias = generar_sugerencias_inteligentes(valor, memoria_correcciones, estadisticas)
            if sugerencias:
                sugerencias_automaticas[valor] = sugerencias
    
    return bins_problematicos, sugerencias_automaticas


def limpiar_cupo_bankard(df):
    df = df.copy()
    if "cupo" not in df.columns:
        df["cupo"] = 0
        return df

    def solo_numero(val):
        if pd.isna(val):
            return 0
        dig = re.sub(r"[^0-9]", "", str(val))
        if dig == "":
            return 0
        return int(dig)

    df["cupo"] = df["cupo"].apply(solo_numero)
    return df




def aplicar_correcciones_bin(df, memoria_correcciones, estadisticas=None):
    """Aplica correcciones de BIN con actualización de estadísticas"""
    df = df.copy()
    if "BIN" not in df.columns:
        df["BIN"] = np.nan
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
                # Usar la primera sugerencia automáticamente si tiene alta confianza
                primera_sugerencia = sugerencias[0]
                # Solo auto-aplicar si la similitud es muy alta (>0.8)
                similitud = calcular_similitud_bin(val, primera_sugerencia)
                if similitud > 0.8:
                    actualizar_estadisticas_bin(val, primera_sugerencia, estadisticas)
                    return primera_sugerencia
        
        return val.title()

    df["BIN"] = df["BIN"].apply(corregir)
    return df


def filtrar_vigencia_bankard(df):
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
    df = df.copy()
    if "telefono" not in df.columns:
        df["telefono"] = ""
    if "cedula" not in df.columns:
        df["cedula"] = ""
    df["telefono"] = df["telefono"].apply(pad_10_digitos)
    df["cedula"] = df["cedula"].apply(pad_10_digitos)
    return df


def limpiar_nombres_bankard(df):
    """Limpia y normaliza nombres en formato de nombres propios para Bankard"""
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


def cargar_cedulas_excluir_uploads(files):
    cedulas = set()
    errores = []
    for upload in files or []:
        try:
            upload.seek(0)
        except Exception:
            pass
        try:
            df_exc = pd.read_excel(upload, dtype=str)
        except Exception as exc:
            errores.append(f"{upload.name}: {exc}")
            continue
        if "IDENTIFICACION" not in df_exc.columns:
            errores.append(f"{upload.name}: no contiene columna 'IDENTIFICACION'")
            continue
        cedulas.update(df_exc["IDENTIFICACION"].astype(str).apply(pad_10_digitos))
    return cedulas, errores


def cargar_exclusiones_consolidadas():
    """Carga el archivo JSON consolidado de exclusiones"""
    if EXCLUSIONES_CONSOLIDADAS_PATH.exists():
        try:
            with open(EXCLUSIONES_CONSOLIDADAS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("cedulas_excluidas", {}), data.get("estadisticas", {})
        except (json.JSONDecodeError, KeyError):
            return {}, {}
    return {}, {}


def guardar_exclusiones_consolidadas(cedulas_data, estadisticas):
    """Guarda las exclusiones consolidadas en JSON"""
    data = {
        "cedulas_excluidas": cedulas_data,
        "estadisticas": estadisticas
    }
    with open(EXCLUSIONES_CONSOLIDADAS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def procesar_archivo_exclusiones(archivo_path, cedulas_consolidadas, estadisticas):
    """Procesa un archivo de exclusiones y actualiza la base consolidada"""
    try:
        df_exc = pd.read_excel(archivo_path, dtype=str)
    except Exception as exc:
        return False, f"Error leyendo archivo: {exc}"
    
    if "IDENTIFICACION" not in df_exc.columns:
        return False, "No contiene columna 'IDENTIFICACION'"
    
    cedulas_nuevas = 0
    cedulas_actualizadas = 0
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    
    for cedula_raw in df_exc["IDENTIFICACION"].dropna():
        cedula = pad_10_digitos(cedula_raw)
        if not cedula:
            continue
            
        if cedula not in cedulas_consolidadas:
            cedulas_consolidadas[cedula] = {
                "fecha_agregada": fecha_actual,
                "fuente": archivo_path.name,
                "activa": True
            }
            cedulas_nuevas += 1
        else:
            # Actualizar fecha si ya existe
            cedulas_consolidadas[cedula]["fecha_agregada"] = fecha_actual
            cedulas_consolidadas[cedula]["fuente"] = archivo_path.name
            cedulas_actualizadas += 1
    
    # Actualizar estadísticas
    estadisticas["total_cedulas"] = len(cedulas_consolidadas)
    estadisticas["ultima_actualizacion"] = datetime.now().isoformat()
    estadisticas["archivos_procesados"] = estadisticas.get("archivos_procesados", 0) + 1
    
    return True, f"Procesado: {cedulas_nuevas} nuevas, {cedulas_actualizadas} actualizadas"


def cargar_cedulas_excluir_directorio(path: Path):
    """Carga exclusiones desde archivos Excel (método legacy)"""
    cedulas = set()
    errores = []
    archivos = []
    if not path.exists():
        return cedulas, errores, archivos

    for archivo in path.glob("*.xlsx"):
        if archivo.name.startswith("~$"):
            continue
        try:
            df_exc = pd.read_excel(archivo, dtype=str)
        except Exception as exc:
            errores.append(f"{archivo.name}: {exc}")
            continue
        if "IDENTIFICACION" not in df_exc.columns:
            errores.append(
                f"{archivo.name}: no contiene columna 'IDENTIFICACION'"
            )
            continue
        cedulas.update(
            df_exc["IDENTIFICACION"].astype(str).apply(pad_10_digitos)
        )
        archivos.append(archivo.name)

    return cedulas, errores, archivos


def consolidar_exclusiones_desde_directorio():
    """Consolida todos los archivos Excel en el JSON consolidado"""
    cedulas_consolidadas, estadisticas = cargar_exclusiones_consolidadas()
    archivos_procesados = 0
    errores = []
    
    if not EXCLUSIONES_BANKARD_DIR.exists():
        return False, "Directorio de exclusiones no existe"
    
    for archivo in EXCLUSIONES_BANKARD_DIR.glob("*.xlsx"):
        if archivo.name.startswith("~$"):
            continue
            
        success, message = procesar_archivo_exclusiones(archivo, cedulas_consolidadas, estadisticas)
        if success:
            archivos_procesados += 1
        else:
            errores.append(f"{archivo.name}: {message}")
    
    if archivos_procesados > 0:
        guardar_exclusiones_consolidadas(cedulas_consolidadas, estadisticas)
        return True, f"Consolidados {archivos_procesados} archivos. {len(errores)} errores."
    
    return False, f"No se procesaron archivos. {len(errores)} errores."


def marcar_exclusiones_varios(df, cedulas_excluir):
    df = df.copy()
    if "exclusion" in df.columns:
        base = df["exclusion"].astype(str)
    elif "Excluir" in df.columns:
        base = df["Excluir"].astype(str)
    else:
        base = pd.Series("NO", index=df.index)

    def normalizar(valor):
        return "SI" if str(valor).strip().upper() == "SI" else "NO"

    df["exclusion"] = base.apply(normalizar)

    if cedulas_excluir:
        df["cedula"] = df["cedula"].astype(str)
        mask = df["cedula"].isin(cedulas_excluir)
        df.loc[mask, "exclusion"] = "SI"

    return df


def ensure_column_from(df, target, sources=(), fill_value=""):
    if target in df.columns:
        return target
    for src in sources:
        if src in df.columns:
            df[target] = df[src]
            return target
    df[target] = fill_value
    return target


def generar_plantilla_sms_credimax_segmentada(df, sms_texto, sms_link, col_campana="Campaña Growth"):
    """Genera plantillas SMS segmentadas por campaña para Credimax"""
    if not sms_texto or not sms_link:
        return None, []
    
    # Acortar el enlace usando Bitly
    enlace_acortado = acortar_enlace_bitly(sms_link)
    
    # Usar la misma lógica que preparar_zip_por_campana
    columnas_necesarias = {
        col_campana,
        "IND_DESEMBOLSO",
        "CELULAR",
        "CUPO",  # Columna original del monto
        "Tasa",  # Columna original de la tasa
    }

    df_trabajo = df.copy()
    for col in columnas_necesarias:
        if col not in df_trabajo.columns:
            df_trabajo[col] = np.nan

    df_exp = df_trabajo[df_trabajo["IND_DESEMBOLSO"] == "0"].copy()
    df_exp[col_campana] = df_exp[col_campana].astype(str).str.strip()
    mask_no_vacio = (
        df_exp[col_campana].notna()
        & (df_exp[col_campana] != "")
        & (~df_exp[col_campana].str.lower().eq("nan"))
    )
    df_exp = df_exp[mask_no_vacio].copy()

    if df_exp.empty:
        return None, []

    # Filtrar solo registros con celular válido
    df_exp = df_exp[df_exp["CELULAR"].notna() & (df_exp["CELULAR"] != "")]

    if df_exp.empty:
        return None, []

    fecha_archivo = datetime.now().strftime("%d-%m")
    zip_buf = io.BytesIO()
    archivos_generados = []

    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for nombre, grupo in df_exp.groupby(col_campana, dropna=False):
            if pd.isna(nombre):
                continue
            nombre_archivo = safe_filename(nombre)
            if not nombre_archivo or nombre_archivo.lower() == "nan":
                continue

            # Generar mensajes personalizados para este grupo
            mensajes = []
            celulares = []
            
            for _, row in grupo.iterrows():
                mensaje = sms_texto
                
                # Reemplazar variables
                monto = str(row.get("CUPO", "")).strip()
                tasa = str(row.get("Tasa", "")).strip()
                
                # Mantener formato con comas para separadores de miles
                if monto and monto != "nan":
                    monto_limpio = monto  # Mantener el formato original con comas
                else:
                    monto_limpio = "0"
                
                # Limpiar tasa (quitar % si existe)
                if tasa and tasa != "nan":
                    tasa_limpia = tasa.replace("%", "").strip()
                else:
                    tasa_limpia = "0"
                
                mensaje = mensaje.replace("<#monto#>", monto_limpio)
                mensaje = mensaje.replace("<#tasa#>", tasa_limpia)
                mensaje = mensaje.replace("<#link#>", enlace_acortado)
                
                mensajes.append(mensaje)
                celulares.append(row["CELULAR"])
            
            # Crear DataFrame para esta campaña
            df_campana = pd.DataFrame({
                "celular": celulares,
                "mensaje": mensajes
            })
            
            # Agregar al ZIP (sin encabezados)
            excel_bytes = df_to_excel_bytes(df_campana, sheet_name="sms", header=False)
            nombre_archivo_sms = f"SMS_{nombre_archivo}_{fecha_archivo}.xlsx"
            zf.writestr(nombre_archivo_sms, excel_bytes)
            archivos_generados.append(nombre_archivo_sms)

    if not archivos_generados:
        return None, []

    zip_buf.seek(0)
    return zip_buf.read(), archivos_generados


def generar_plantilla_sms_bankard_segmentada(df, sms_texto, sms_link, col_tipo="TIPO ", col_exclusion="exclusion"):
    """Genera plantillas SMS segmentadas por tipo y exclusión para Bankard"""
    if not sms_texto or not sms_link:
        return None, []
    
    # Acortar el enlace usando Bitly
    enlace_acortado = acortar_enlace_bitly(sms_link)
    
    if col_tipo not in df.columns or col_exclusion not in df.columns:
        return None, []

    # Asegurar que las columnas necesarias existan
    if "telefono" not in df.columns:
        df["telefono"] = ""
    if "BIN" not in df.columns:
        df["BIN"] = ""
    if "cupo" not in df.columns:
        df["cupo"] = ""

    hoy_str = datetime.now().strftime("%d%m")
    zip_buf = io.BytesIO()
    archivos_generados = []

    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for tipo in sorted(df[col_tipo].dropna().astype(str).unique()):
            # Solo procesar registros SIN exclusión (exclusion = "NO")
            subset = df[
                (df[col_tipo].astype(str) == tipo)
                & (df[col_exclusion].astype(str).str.upper() == "NO")
            ].copy()
            
            if subset.empty:
                continue
            
            # Filtrar solo registros con teléfono válido
            subset = subset[subset["telefono"].notna() & (subset["telefono"] != "")]
            
            if subset.empty:
                continue
            
            # Generar mensajes personalizados para este grupo
            mensajes = []
            telefonos = []
            
            for _, row in subset.iterrows():
                mensaje = sms_texto
                
                # Reemplazar variables
                marca = str(row.get("BIN", "")).strip()
                cupo = str(row.get("cupo", "")).strip()
                
                # Formatear cupo con separadores de miles
                if cupo and cupo != "nan":
                    try:
                        # Convertir a entero y luego formatear con comas
                        cupo_num = int(float(cupo))
                        cupo_limpio = f"{cupo_num:,}"
                    except (ValueError, TypeError):
                        cupo_limpio = "0"
                else:
                    cupo_limpio = "0"
                
                mensaje = mensaje.replace("<#marca#>", marca)
                mensaje = mensaje.replace("<#cupo#>", cupo_limpio)
                mensaje = mensaje.replace("<#link#>", enlace_acortado)
                
                mensajes.append(mensaje)
                telefonos.append(row["telefono"])
            
            # Crear DataFrame para este tipo
            df_tipo = pd.DataFrame({
                "telefono": telefonos,
                "mensaje": mensajes
            })
            
            # Agregar al ZIP (sin encabezados)
            excel_bytes = df_to_excel_bytes(df_tipo, sheet_name="sms", header=False)
            nombre_tipo = safe_filename(tipo) or "SIN_TIPO"
            nombre_archivo_sms = f"SMS_Bankard_{nombre_tipo}_{hoy_str}.xlsx"
            zf.writestr(nombre_archivo_sms, excel_bytes)
            archivos_generados.append(nombre_archivo_sms)

    if not archivos_generados:
        return None, []

    zip_buf.seek(0)
    return zip_buf.read(), archivos_generados


def preparar_zip_bankard(df, col_tipo="TIPO ", col_exclusion="exclusion"):
    if col_tipo not in df.columns or col_exclusion not in df.columns:
        return None, []

    # Mapeo de columnas para Bankard (incluye variantes para No Clientes)
    mapeo_columnas_bankard = {
        "primer_nombre": "primer_nombre_bankard",
        "Nombres": "primer_nombre_bankard",  # Para archivos No Clientes
        "cupo": "Cupo_Aprobado_OB_BK", 
        "BIN": "Marca_BK_OB",
        "correo": "correo",
        "CORREO BANCO ": "correo",  # Para archivos No Clientes
        "telefono": "telefono"
    }

    # Columnas finales que se exportarán
    columnas_exportadas = [
        "primer_nombre_bankard",
        "Cupo_Aprobado_OB_BK",
        "Marca_BK_OB", 
        "correo",
        "telefono"
    ]

    hoy_str = datetime.now().strftime("%d%m")
    zip_buf = io.BytesIO()
    archivos = 0

    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for tipo in sorted(df[col_tipo].dropna().astype(str).unique()):
            for excl in ["SI", "NO"]:
                subset = df[
                    (df[col_tipo].astype(str) == tipo)
                    & (df[col_exclusion].astype(str).str.upper() == excl)
                ].copy()
                if subset.empty:
                    continue
                
                # Aplicar mapeo de columnas
                subset_mapeado = subset.copy()
                for col_original, col_nueva in mapeo_columnas_bankard.items():
                    if col_original in subset_mapeado.columns:
                        subset_mapeado[col_nueva] = subset_mapeado[col_original]
                
                # Formatear cupo con comas
                if "Cupo_Aprobado_OB_BK" in subset_mapeado.columns:
                    subset_mapeado["Cupo_Aprobado_OB_BK"] = subset_mapeado["Cupo_Aprobado_OB_BK"].apply(
                        lambda x: f"{int(x):,}" if str(x).strip() != "" and str(x).strip() != "nan" else ""
                    )
                
                # Seleccionar solo las columnas que se van a exportar
                subset_final = subset_mapeado.reindex(columns=columnas_exportadas)
                
                # Asegurar que todas las columnas existan
                for col in columnas_exportadas:
                    if col not in subset_final.columns:
                        subset_final[col] = ""
                
                nombre_tipo = safe_filename(tipo) or "SIN_TIPO"
                
                # Formato de nombre según exclusión
                if excl == "SI":
                    nombre_archivo = f"Bankard_{nombre_tipo}_Excluir_{hoy_str}.xlsx"
                else:  # NO
                    nombre_archivo = f"Bankard_{nombre_tipo}_{hoy_str}.xlsx"
                zf.writestr(nombre_archivo, df_to_excel_bytes(subset_final, sheet_name="base"))
                archivos += 1

    if archivos == 0:
        return None, []

    zip_buf.seek(0)
    return zip_buf.read(), columnas_exportadas

# =============================
# Flujos de ejecución
# =============================
def run_credimax():
    st.sidebar.header("1) Sube la base Credimax")
    base_file = st.sidebar.file_uploader(
        "Base Credimax (.xlsx)", type=["xlsx"], key="base_credimax"
    )

    st.sidebar.header("2) Exportación por campaña")
    export_por_campana = st.sidebar.checkbox(
        "Generar ZIP por 'Campaña Growth'", value=True, key="zip_credimax"
    )
    
    st.sidebar.header("3) Plantillas SMS")
    exportar_sms = st.sidebar.checkbox(
        "Generar plantilla SMS", 
        value=False, 
        key="exportar_sms_credimax",
        help="Genera archivo con plantilla de SMS personalizada"
    )
    
    # Campos para plantilla SMS
    sms_texto = ""
    sms_link = ""
    if exportar_sms:
        st.sidebar.subheader("📱 Configuración SMS")
        sms_texto = st.sidebar.text_area(
            "Texto del SMS",
            value="En Banco Bolivariano, tienes un prestamo aprobado de $<#monto#> con una tasa del <#tasa#>% por tiempo limitado. Solicitalo aqui ahora: <#link#>",
            help="Usa <#monto#> para monto, <#tasa#> para tasa, <#link#> para enlace",
            key="sms_texto_credimax"
        )
        sms_link = st.sidebar.text_input(
            "Enlace",
            value="https://ejemplo.com/credimax",
            help="Enlace que reemplazará <#link#> en el SMS",
            key="sms_link_credimax"
        )

    if not base_file:
        st.info("👆 Sube la base para continuar.")
        return

    try:
        df = pd.read_excel(base_file, dtype=str)
    except Exception as e:
        st.error(f"No se pudo leer el Excel: {e}")
        return

    for col in COLUMNAS_ESPERADAS:
        if col not in df.columns:
            df[col] = np.nan

    df["CEDULA_VALIDO"] = df["CEDULA"].apply(validar_cedula_10)
    df["CELULAR"] = df["CELULAR"].apply(normalizar_celular_ec)
    df["CELULAR_VALIDO"] = df["CELULAR"].notna() & (df["CELULAR"].str.len() == 10)

    df["primer_nombre"] = df["primer_nombre"].apply(a_nombre_propio)
    df["primer_apellido"] = df["primer_apellido"].apply(a_nombre_propio)

    df["CUPO"] = df["CUPO"].apply(cupo_a_texto_miles_coma)
    df["CUPO_TARJETA_BK"] = df["CUPO_TARJETA_BK"].apply(cupo_a_texto_miles_coma)

    # MARCA_TARJETA_BK: forzar a NaN cuando no esté en lista válida (comparación normalizada)
    valid_norms = {norm(x) for x in MARCAS_VALIDAS_DEFAULT}
    marca_norm = df["MARCA_TARJETA_BK"].apply(lambda x: norm(x) if pd.notna(x) else x)
    mask_invalid_marcas = df["MARCA_TARJETA_BK"].notna() & (~marca_norm.isin(valid_norms))
    invalid_ejemplos = (
        df.loc[mask_invalid_marcas, "MARCA_TARJETA_BK"].dropna().astype(str).str.strip().value_counts().head(10)
    )
    if mask_invalid_marcas.any():
        df.loc[mask_invalid_marcas, "MARCA_TARJETA_BK"] = np.nan
        st.warning(
            f"Se detectaron **{int(mask_invalid_marcas.sum())}** marcas de tarjeta no válidas. "
            "Fueron limpiadas a vacío (NaN). Revisa las tarjetas en el origen."
        )
        if len(invalid_ejemplos):
            st.caption("Ejemplos más frecuentes no válidos:")
            st.write(invalid_ejemplos)

    # Reglas determinísticas Campaña Growth
    for col in ["Campaña Growth", "CANAL", "Producto", "SEGMENTO", "TESTEO CUOTA"]:
        if col not in df.columns:
            df[col] = np.nan

    canal_n = df["CANAL"].apply(norm)
    prod_n = df["Producto"].apply(norm)
    seg_n = df["SEGMENTO"].apply(norm)
    test_n = df["TESTEO CUOTA"].apply(norm)

    is_online = canal_n == "ONLINE"
    is_no_cli = prod_n.isin({
        "CREDIMAX ONLINE NO CLIENTES",
        "CREDIMAX ONLINE NO CLIENTE",
        "CREDIMAX ONLINE NOCLIENTES",
    })
    is_afluente = seg_n.isin(SEG_AFL)
    is_masivo = seg_n.isin(SEG_MAS)
    test_es_si = test_n.isin({"SI", "1", "TRUE", "X"})

    df["Campaña Growth Original"] = df["Campaña Growth"]
    camp_final = df["Campaña Growth"].astype("object").copy()

    mask_no_cli_afl = is_online & is_no_cli & is_afluente
    mask_no_cli_mas = is_online & is_no_cli & is_masivo
    mask_online_otros = is_online & (~is_no_cli)
    mask_elite = mask_online_otros & (seg_n == "ELITE")
    mask_premium = mask_online_otros & (seg_n == "PREMIUM")
    mask_masivo_base = mask_online_otros & is_masivo
    mask_masivo_cuotas = mask_masivo_base & test_es_si
    mask_masivo_sin_cuotas = mask_masivo_base & (~test_es_si)

    camp_final.loc[mask_no_cli_afl] = "Credimax Online No Clientes Afluente"
    camp_final.loc[mask_no_cli_mas] = "Credimax Online No Clientes Masivo"
    camp_final.loc[mask_elite] = "Credimax Online Elite"
    camp_final.loc[mask_premium] = "Credimax Online Premium"
    camp_final.loc[mask_masivo_cuotas] = "Credimax Online Masivo Cuotas"
    camp_final.loc[mask_masivo_sin_cuotas] = "Credimax Online Masivo"

    df["Campaña Growth"] = camp_final

    df_cmp = df.copy()
    df_cmp["Coincide (Original vs Reglas)"] = (
        df_cmp["Campaña Growth Original"].fillna("").str.strip()
        == df_cmp["Campaña Growth"].fillna("").str.strip()
    )
    df_cmp["Cambio Aplicado (Original -> Final)"] = ~df_cmp["Coincide (Original vs Reglas)"]

    st.subheader("🧠 Reescritura de 'Campaña Growth' (reglas)")

    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.metric("No Clientes Afluente", int(mask_no_cli_afl.sum()))
        st.metric("Masivo (sin cuotas)", int(mask_masivo_sin_cuotas.sum()))
    with col_r2:
        st.metric("No Clientes Masivo", int(mask_no_cli_mas.sum()))
        st.metric("Elite", int(mask_elite.sum()))
    with col_r3:
        st.metric("Masivo (cuotas)", int(mask_masivo_cuotas.sum()))
        st.metric("Premium", int(mask_premium.sum()))

    st.divider()
    st.subheader("📦 Descargas")

    # ✅ Archivo principal con el nombre solicitado
    st.download_button(
        "⬇️ Base Credimax LIMPIA FINAL CON SEGMENTO.xlsx",
        data=df_to_excel_bytes(df, sheet_name="base"),
        file_name="Base Credimax LIMPIA FINAL CON SEGMENTO.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    cmp_cols = [
        "SEGMENTO",
        "Producto",
        "Ind_Perfil_Campaña",
        "CANAL",
        "TESTEO CUOTA",
        "Campaña Growth Original",
        "Campaña Growth",
        "Coincide (Original vs Reglas)",
        "Cambio Aplicado (Original -> Final)",
    ]

    st.download_button(
        "⬇️ Base Credimax COMPARACION CAMPANA GROWTH.xlsx",
        data=df_to_excel_bytes(df_cmp[cmp_cols], sheet_name="comparacion"),
        file_name="Base Credimax COMPARACION CAMPANA GROWTH.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    if export_por_campana:
        zip_bytes, columnas_segmentadas = preparar_zip_por_campana(df)

        if zip_bytes:
            st.download_button(
                "⬇️ Descargar ZIP por campaña",
                data=zip_bytes,
                file_name=f"Campanas_segmentadas_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip",
            )
            st.caption(
                "Columnas en cada archivo segmentado: "
                + ", ".join(columnas_segmentadas)
            )
        else:
            st.info(
                "No hay registros con IND_DESEMBOLSO = '0' y campaña válida para generar el ZIP."
            )

    # Generar plantilla SMS si está habilitada
    if exportar_sms and sms_texto and sms_link:
        # Acortar enlace para mostrar en la interfaz
        enlace_acortado = acortar_enlace_bitly(sms_link)
        
        zip_sms_bytes, archivos_sms = generar_plantilla_sms_credimax_segmentada(df, sms_texto, sms_link)
        if zip_sms_bytes and archivos_sms:
            st.divider()
            st.subheader("📱 Plantillas SMS Segmentadas")
            
            # Mostrar estadísticas de archivos generados
            st.write(f"**Se generaron {len(archivos_sms)} plantillas SMS segmentadas por campaña:**")
            for archivo in archivos_sms:
                st.caption(f"• {archivo}")
            
            # Botón de descarga
            fecha_sms = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                "⬇️ Descargar ZIP Plantillas SMS",
                data=zip_sms_bytes,
                file_name=f"SMS_Credimax_Segmentado_{fecha_sms}.zip",
                mime="application/zip",
            )
            st.caption("📱 **Plantillas SMS segmentadas por campaña** (solo registros sin desembolso)")
            st.caption(f"🔗 **Enlace acortado**: {enlace_acortado}")
        else:
            st.warning("No se pudo generar las plantillas SMS. Verifica que haya registros con IND_DESEMBOLSO = '0', campañas válidas y celulares válidos.")

    st.success("✅ Limpieza Credimax completada. Descarga tus archivos.")


def run_bankard():
    st.sidebar.header("1) Sube la base Bankard")
    base_file = st.sidebar.file_uploader(
        "Base Bankard (.xlsx)", type=["xlsx"], key="base_bankard"
    )

    st.sidebar.header("2) Sistema de Exclusiones")
    
    # Cargar exclusiones consolidadas
    cedulas_consolidadas, estadisticas_exclusiones = cargar_exclusiones_consolidadas()
    
    st.sidebar.header("3) Plantillas SMS")
    exportar_sms = st.sidebar.checkbox(
        "Generar plantilla SMS", 
        value=False, 
        key="exportar_sms_bankard",
        help="Genera archivo con plantilla de SMS personalizada"
    )
    
    # Campos para plantilla SMS
    sms_texto = ""
    sms_link = ""
    if exportar_sms:
        st.sidebar.subheader("📱 Configuración SMS")
        sms_texto = st.sidebar.text_area(
            "Texto del SMS",
            value="Felicidades! Tu Bankard <#marca#> ha sido aprobada con un cupo de $<#cupo#>. Obtenla en minutos aqui: <#link#>",
            help="Usa <#marca#> para marca, <#cupo#> para cupo, <#link#> para enlace",
            key="sms_texto_bankard"
        )
        sms_link = st.sidebar.text_input(
            "Enlace",
            value="https://ejemplo.com/bankard",
            help="Enlace que reemplazará <#link#> en el SMS",
            key="sms_link_bankard"
        )
    
    # Mostrar estadísticas del sistema consolidado
    if estadisticas_exclusiones:
        st.sidebar.success(f"📊 **Sistema Consolidado Activo**")
        st.sidebar.metric("Cédulas en exclusión", estadisticas_exclusiones.get("total_cedulas", 0))
        st.sidebar.caption(f"Última actualización: {estadisticas_exclusiones.get('ultima_actualizacion', 'N/A')[:10]}")
        st.sidebar.caption(f"Archivos procesados: {estadisticas_exclusiones.get('archivos_procesados', 0)}")
    else:
        st.sidebar.info("📊 **Sistema Consolidado Vacío**")
        st.sidebar.caption("Usa las opciones abajo para cargar exclusiones")
    
    # Opciones de carga de exclusiones
    st.sidebar.subheader("🔄 Opciones de Carga")
    
    # Opción 1: Consolidar desde carpeta
    if st.sidebar.button("📁 Consolidar desde carpeta", help="Procesa todos los Excel de data/exclusiones_bankard/"):
        with st.spinner("Consolidando archivos Excel..."):
            success, message = consolidar_exclusiones_desde_directorio()
            if success:
                st.sidebar.success(message)
                st.rerun()
            else:
                st.sidebar.error(message)
    
    # Opción 2: Cargar archivos individuales
    exclusion_files = st.sidebar.file_uploader(
        "📤 Subir archivos de exclusión (.xlsx)",
        type=["xlsx"],
        accept_multiple_files=True,
        key="exclusiones_bankard",
        help="Se procesarán y agregarán al sistema consolidado"
    )
    
    # Procesar archivos subidos
    if exclusion_files:
        with st.spinner("Procesando archivos subidos..."):
            archivos_procesados = 0
            for uploaded_file in exclusion_files:
                # Crear archivo temporal
                temp_path = EXCLUSIONES_BANKARD_DIR / uploaded_file.name
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Procesar archivo
                success, message = procesar_archivo_exclusiones(temp_path, cedulas_consolidadas, estadisticas_exclusiones)
                if success:
                    archivos_procesados += 1
                    # Guardar cambios
                    guardar_exclusiones_consolidadas(cedulas_consolidadas, estadisticas_exclusiones)
                else:
                    st.sidebar.warning(f"Error en {uploaded_file.name}: {message}")
                
                # Limpiar archivo temporal
                temp_path.unlink()
            
            if archivos_procesados > 0:
                st.sidebar.success(f"✅ Procesados {archivos_procesados} archivos")
                st.rerun()
    
    # Opción 3: Método legacy (para compatibilidad)
    st.sidebar.caption("---")
    st.sidebar.caption("**Método Legacy (solo lectura):**")
    (
        cedulas_persistentes,
        errores_persistentes,
        archivos_persistentes,
    ) = cargar_cedulas_excluir_directorio(EXCLUSIONES_BANKARD_DIR)
    
    if archivos_persistentes:
        st.sidebar.caption(f"Archivos Excel detectados: {len(archivos_persistentes)}")
        st.sidebar.caption("💡 Usa 'Consolidar desde carpeta' para procesarlos")

    if not base_file:
        st.info("👆 Sube la base para continuar.")
        return

    try:
        df = pd.read_excel(base_file, dtype=str)
    except Exception as e:
        st.error(f"No se pudo leer el Excel: {e}")
        return

    df = limpiar_cupo_bankard(df)
    memoria_correcciones = cargar_memoria_correcciones()
    estadisticas = cargar_estadisticas_bin()
    
    # Detectar BINs problemáticos con sugerencias automáticas
    pendientes, sugerencias_auto = detectar_bins_no_permitidos_inteligente(df, memoria_correcciones, estadisticas)

    if pendientes:
        st.warning(
            f"Se encontraron **{len(pendientes)}** valores en 'BIN' fuera de la lista permitida."
        )
        st.caption(
            "Opciones permitidas: " + ", ".join(VALORES_BIN_PERMITIDOS)
        )
        
        # Mostrar estadísticas de uso si están disponibles
        if estadisticas.get("ultima_actualizacion"):
            st.caption(f"💡 Sistema de aprendizaje activo (última actualización: {estadisticas['ultima_actualizacion'][:10]})")
        
        correcciones_inputs = {}
        with st.form("correcciones_bin"):
            st.write("Indica cómo reemplazar cada BIN detectado (dejar vacío para ignorar).")
            
            for valor in pendientes:
                # Mostrar sugerencias automáticas si están disponibles
                sugerencias = sugerencias_auto.get(valor, [])
                if sugerencias:
                    st.write(f"**'{valor}'** - Sugerencias automáticas:")
                    for i, sug in enumerate(sugerencias[:3], 1):
                        st.caption(f"  {i}. {sug}")
                
                # Input con valor por defecto de la primera sugerencia
                valor_default = sugerencias[0] if sugerencias else memoria_correcciones.get(valor, "")
                correcciones_inputs[valor] = st.text_input(
                    f"Nuevo valor para '{valor}'",
                    value=valor_default,
                    key=f"bin_corr_{valor}",
                    help=f"Sugerencias: {', '.join(sugerencias[:3])}" if sugerencias else None
                )
            
            submitted = st.form_submit_button("Guardar correcciones")
        
        if submitted:
            actualizaciones = {}
            for origen, nuevo in correcciones_inputs.items():
                if nuevo.strip():
                    actualizaciones[origen] = nuevo.strip()
                    # Actualizar estadísticas inmediatamente
                    actualizar_estadisticas_bin(origen, nuevo.strip(), estadisticas)
            
            if actualizaciones:
                memoria_correcciones.update(actualizaciones)
                guardar_memoria_correcciones(memoria_correcciones)
                guardar_estadisticas_bin(estadisticas)
                st.success("Correcciones guardadas y estadísticas actualizadas. Se aplicarán inmediatamente.")
            else:
                st.info("No se ingresaron correcciones nuevas.")
            
            # Recargar datos actualizados
            memoria_correcciones = cargar_memoria_correcciones()
            estadisticas = cargar_estadisticas_bin()

    # Aplicar correcciones con el sistema inteligente
    df = aplicar_correcciones_bin(df, memoria_correcciones, estadisticas)
    df, excluidos_vigencia = filtrar_vigencia_bankard(df)
    df = limpiar_telefonos_cedulas_bankard(df)
    df = limpiar_nombres_bankard(df)

    # Usar el sistema consolidado como principal
    cedulas_excluir = set(cedulas_consolidadas.keys())
    
    # Agregar exclusiones de uploads (método legacy para compatibilidad)
    if exclusion_files:
        cedulas_upload, errores_exclusiones = cargar_cedulas_excluir_uploads(exclusion_files)
        cedulas_excluir.update(cedulas_upload)
        if errores_exclusiones:
            for msg in errores_exclusiones:
                st.warning(f"Exclusión omitida: {msg}")
    
    # Agregar exclusiones persistentes (método legacy)
    if cedulas_persistentes:
        cedulas_excluir.update(cedulas_persistentes)
    
    total_exclusiones = len(cedulas_excluir)
    if total_exclusiones:
        st.caption(
            f"Se aplicaron **{total_exclusiones}** cédulas de exclusión "
            f"({len(cedulas_consolidadas)} del sistema consolidado + {total_exclusiones - len(cedulas_consolidadas)} adicionales)."
        )

    df = marcar_exclusiones_varios(df, cedulas_excluir)
    
    # Verificar si existe columna TIPO antes de crearla
    tiene_tipo = "TIPO " in df.columns or "TIPO" in df.columns
    ensure_column_from(df, "TIPO ", sources=["TIPO"], fill_value="No Clientes")
    
    # Mostrar información si se creó la columna TIPO
    if not tiene_tipo:
        st.info("ℹ️ **Columna TIPO no encontrada** - Se asignó automáticamente 'No Clientes' a todos los registros")

    total_registros = len(df)
    excl_si = int((df["exclusion"].astype(str).str.upper() == "SI").sum())
    excl_no = int((df["exclusion"].astype(str).str.upper() == "NO").sum())

    st.subheader("📋 Resultados Bankard")
    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.metric("Registros totales", total_registros)
    col_b2.metric("Exclusión = SI", excl_si)
    col_b3.metric("Exclusión = NO", excl_no)
    
    # Mostrar información de limpieza aplicada
    st.caption("🧹 **Limpieza aplicada:** Nombres en formato propio, cupos con comas, teléfonos/cédulas normalizados, BINs corregidos")
    
    # Mostrar estadísticas del sistema de aprendizaje
    if estadisticas.get("frecuencias") or estadisticas.get("patrones"):
        st.divider()
        st.subheader("🧠 Estadísticas del Sistema de Aprendizaje")
        
        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            if estadisticas.get("frecuencias"):
                st.write("**Correcciones más frecuentes:**")
                frecuencias_totales = {}
                for bin_orig, correcciones in estadisticas["frecuencias"].items():
                    for bin_corr, count in correcciones.items():
                        key = f"{bin_orig} → {bin_corr}"
                        frecuencias_totales[key] = count
                
                if frecuencias_totales:
                    top_correcciones = sorted(frecuencias_totales.items(), key=lambda x: x[1], reverse=True)[:5]
                    for correccion, count in top_correcciones:
                        st.caption(f"• {correccion}: {count} veces")
        
        with col_stats2:
            if estadisticas.get("patrones"):
                st.write("**Patrones detectados:**")
                total_patrones = sum(len(patrones) for patrones in estadisticas["patrones"].values())
                st.metric("BINs con patrones", total_patrones)
                
                if estadisticas.get("ultima_actualizacion"):
                    fecha_ultima = estadisticas["ultima_actualizacion"][:10]
                    st.caption(f"Última actualización: {fecha_ultima}")
        
        # Botón para limpiar estadísticas (opcional)
        if st.button("🗑️ Limpiar estadísticas", help="Elimina todas las estadísticas de aprendizaje"):
            estadisticas = {
                "frecuencias": {},
                "sugerencias": {},
                "patrones": {},
                "ultima_actualizacion": None
            }
            guardar_estadisticas_bin(estadisticas)
            st.success("Estadísticas limpiadas")
            st.rerun()

    if excluidos_vigencia:
        st.info(
            f"Se excluyeron {excluidos_vigencia} registros por vigencia vencida o inválida."
        )

    st.divider()
    st.subheader("📦 Descargas")

    # Aplicar mapeo de columnas para el archivo principal (incluye variantes para No Clientes)
    mapeo_columnas_bankard = {
        "primer_nombre": "primer_nombre_bankard",
        "Nombres": "primer_nombre_bankard",  # Para archivos No Clientes
        "cupo": "Cupo_Aprobado_OB_BK", 
        "BIN": "Marca_BK_OB",
        "correo": "correo",
        "CORREO BANCO ": "correo",  # Para archivos No Clientes
        "telefono": "telefono"
    }
    
    columnas_exportadas_principal = [
        "primer_nombre_bankard",
        "Cupo_Aprobado_OB_BK",
        "Marca_BK_OB", 
        "correo",
        "telefono"
    ]
    
    # Crear DataFrame mapeado para el archivo principal
    df_mapeado = df.copy()
    for col_original, col_nueva in mapeo_columnas_bankard.items():
        if col_original in df_mapeado.columns:
            df_mapeado[col_nueva] = df_mapeado[col_original]
    
    # Formatear cupo con comas
    if "Cupo_Aprobado_OB_BK" in df_mapeado.columns:
        df_mapeado["Cupo_Aprobado_OB_BK"] = df_mapeado["Cupo_Aprobado_OB_BK"].apply(
            lambda x: f"{int(x):,}" if str(x).strip() != "" and str(x).strip() != "nan" else ""
        )
    
    # Seleccionar solo las columnas mapeadas
    df_final = df_mapeado.reindex(columns=columnas_exportadas_principal)
    
    # Asegurar que todas las columnas existan
    for col in columnas_exportadas_principal:
        if col not in df_final.columns:
            df_final[col] = ""

    # Generar nombre del archivo principal con fecha
    fecha_archivo = datetime.now().strftime("%d%m")
    nombre_archivo_principal = f"Bankard_General_{fecha_archivo}.xlsx"
    
    st.download_button(
        "⬇️ Base Bankard LIMPIA.xlsx",
        data=df_to_excel_bytes(df_final, sheet_name="base"),
        file_name=nombre_archivo_principal,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    zip_bytes, columnas_zip = preparar_zip_bankard(df)
    if zip_bytes:
        fecha_zip = datetime.now().strftime("%d%m")
        st.download_button(
            "⬇️ Descargar ZIP por tipo y exclusión",
            data=zip_bytes,
            file_name=f"Bankard_Segmentado_{fecha_zip}.zip",
            mime="application/zip",
        )
        st.caption("Columnas en cada archivo segmentado: " + ", ".join(columnas_zip))
        st.caption("📋 **Mapeo de columnas:** primer_nombre → primer_nombre_bankard, cupo → Cupo_Aprobado_OB_BK, BIN → Marca_BK_OB")
    else:
        st.info("No hay registros para exportar por tipo y exclusión.")

    # Generar plantilla SMS si está habilitada
    if exportar_sms and sms_texto and sms_link:
        # Acortar enlace para mostrar en la interfaz
        enlace_acortado = acortar_enlace_bitly(sms_link)
        
        zip_sms_bytes, archivos_sms = generar_plantilla_sms_bankard_segmentada(df, sms_texto, sms_link)
        if zip_sms_bytes and archivos_sms:
            st.divider()
            st.subheader("📱 Plantillas SMS Segmentadas")
            
            # Mostrar estadísticas de archivos generados
            st.write(f"**Se generaron {len(archivos_sms)} plantillas SMS segmentadas por tipo:**")
            for archivo in archivos_sms:
                st.caption(f"• {archivo}")
            
            # Botón de descarga
            fecha_sms = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                "⬇️ Descargar ZIP Plantillas SMS",
                data=zip_sms_bytes,
                file_name=f"SMS_Bankard_Segmentado_{fecha_sms}.zip",
                mime="application/zip",
            )
            st.caption("📱 **Plantillas SMS segmentadas por tipo** (solo registros sin exclusión)")
            st.caption(f"🔗 **Enlace acortado**: {enlace_acortado}")
        else:
            st.warning("No se pudo generar las plantillas SMS. Verifica que haya registros sin exclusión con teléfonos válidos.")

    st.success("✅ Limpieza Bankard completada. Descarga tus archivos.")

# =============================
# Entrada principal
# =============================
modo = st.sidebar.radio(
    "Selecciona el flujo de limpieza",
    ("Credimax", "Bankard"),
    key="modo_limpieza",
)

if modo == "Credimax":
    run_credimax()
else:
    run_bankard()
