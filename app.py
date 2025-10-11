import io
import json
import re
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
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
EXCLUSIONES_BANKARD_DIR.mkdir(parents=True, exist_ok=True)

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


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "base") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
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


def cargar_cedulas_excluir_directorio(path: Path):
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


def preparar_zip_bankard(df, col_tipo="TIPO ", col_exclusion="exclusion"):
    if col_tipo not in df.columns or col_exclusion not in df.columns:
        return None, []

    hoy_str = datetime.now().strftime("%d%m")
    zip_buf = io.BytesIO()
    archivos = 0
    columnas_exportadas = df.columns.tolist()

    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for tipo in sorted(df[col_tipo].dropna().astype(str).unique()):
            for excl in ["SI", "NO"]:
                subset = df[
                    (df[col_tipo].astype(str) == tipo)
                    & (df[col_exclusion].astype(str).str.upper() == excl)
                ].copy()
                if subset.empty:
                    continue
                if "cupo" in subset.columns:
                    subset["cupo"] = subset["cupo"].apply(
                        lambda x: f"{int(x):,}" if str(x).strip() != "" else ""
                    )
                nombre_tipo = safe_filename(tipo) or "SIN_TIPO"
                nombre_archivo = f"{nombre_tipo}_{excl}_{hoy_str}.xlsx"
                zf.writestr(nombre_archivo, df_to_excel_bytes(subset, sheet_name="base"))
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

    st.success("✅ Limpieza Credimax completada. Descarga tus archivos.")


def run_bankard():
    st.sidebar.header("1) Sube la base Bankard")
    base_file = st.sidebar.file_uploader(
        "Base Bankard (.xlsx)", type=["xlsx"], key="base_bankard"
    )

    st.sidebar.header("2) Exclusiones (opcional)")
    exclusion_files = st.sidebar.file_uploader(
        "Archivos de exclusión (.xlsx)",
        type=["xlsx"],
        accept_multiple_files=True,
        key="exclusiones_bankard",
    )
    st.sidebar.caption("Se utilizará la columna 'IDENTIFICACION' de cada archivo para excluir cédulas.")
    st.sidebar.caption(
        "También puedes dejar archivos .xlsx permanentes en "
        f"`{EXCLUSIONES_BANKARD_DIR}` para cargarlos automáticamente."
    )

    (
        cedulas_persistentes,
        errores_persistentes,
        archivos_persistentes,
    ) = cargar_cedulas_excluir_directorio(EXCLUSIONES_BANKARD_DIR)
    if cedulas_persistentes:
        st.sidebar.info(
            f"{len(cedulas_persistentes)} cédulas serán excluidas desde la carpeta permanente."
        )
    if archivos_persistentes:
        st.sidebar.caption("Archivos permanentes detectados:")
        for nombre_archivo in sorted(archivos_persistentes):
            st.sidebar.write(f"• {nombre_archivo}")
    elif not errores_persistentes:
        st.sidebar.caption(
            "No hay archivos permanentes en `data/exclusiones_bankard` todavía."
        )
    if errores_persistentes:
        for msg in errores_persistentes:
            st.sidebar.warning(f"Exclusión local omitida: {msg}")

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

    cedulas_excluir, errores_exclusiones = cargar_cedulas_excluir_uploads(exclusion_files)
    if cedulas_persistentes:
        cedulas_excluir.update(cedulas_persistentes)
    if errores_exclusiones:
        for msg in errores_exclusiones:
            st.warning(f"Exclusión omitida: {msg}")
    total_exclusiones = len(cedulas_excluir)
    if total_exclusiones:
        st.caption(
            "Se aplicaron **" + str(total_exclusiones) + "** cédulas de exclusión (uploads/permanentes)."
        )

    df = marcar_exclusiones_varios(df, cedulas_excluir)
    ensure_column_from(df, "TIPO ", sources=["TIPO"], fill_value="")

    total_registros = len(df)
    excl_si = int((df["exclusion"].astype(str).str.upper() == "SI").sum())
    excl_no = int((df["exclusion"].astype(str).str.upper() == "NO").sum())

    st.subheader("📋 Resultados Bankard")
    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.metric("Registros totales", total_registros)
    col_b2.metric("Exclusión = SI", excl_si)
    col_b3.metric("Exclusión = NO", excl_no)
    
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

    st.download_button(
        "⬇️ Base Bankard LIMPIA.xlsx",
        data=df_to_excel_bytes(df, sheet_name="base"),
        file_name="Base Bankard LIMPIA.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    zip_bytes, columnas_zip = preparar_zip_bankard(df)
    if zip_bytes:
        st.download_button(
            "⬇️ Descargar ZIP por tipo y exclusión",
            data=zip_bytes,
            file_name=f"Bankard_segmentado_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
        )
        st.caption("Columnas en cada archivo segmentado: " + ", ".join(columnas_zip))
    else:
        st.info("No hay registros para exportar por tipo y exclusión.")

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
