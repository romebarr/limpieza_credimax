import io
import os
import re
import zipfile
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# =============================
# Config básica
# =============================
st.set_page_config(page_title="Limpieza Credimax – SM Growth Lab", layout="wide")
st.title("🧹 Limpieza y Exportación por Campaña – Credimax")
st.caption("Sube la base, aplicamos validaciones/normalizaciones y reescritura de 'Campaña Growth'. Descarga resultados.")

# =============================
# Helpers
# =============================
COLUMNAS_ESPERADAS = [
    "MIS","CEDULA","FECHA NACIMIENTO","primer_nombre","primer_apellido","CELULAR","CORREO CLIENTE",
    "SEGMENTO","CUPO","Plazo","Tasa","Ind_Tasa_Exclusiva","Vigencia","Ind_Campaña_Vigente",
    "Producto","Ind_Perfil_Campaña","CANAL","IND_DESEMBOLSO","Campaña Growth","CUPO_TARJETA_BK",
    "MARCA_TARJETA_BK","BASE MARIO","CUOTA","TESTEO CUOTA"
]

# Segmentos
SEG_AFL = {"ELITE", "PREMIUM"}   # Afluente
SEG_MAS = {"SILVER", "PRESTIGE"} # Masivo

# Marcas válidas por defecto (sin subida de archivos)
MARCAS_VALIDAS_DEFAULT = [
    "Visa Clásica", "Visa Oro", "Visa Infinite", "Visa Platinum", "Visa Signature"
]


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
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


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
    return (str(s)
            .replace('/', '_').replace('\\', '_')
            .replace(':', '').replace('*', '')
            .replace('?', '').replace('"', '')
            .replace('<', '').replace('>', '')
            .replace('|', '').strip())


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "base") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    buf.seek(0)
    return buf.read()


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

    mapeo_columnas = {
        "primer_nombre": "primer_nombre_credimax",
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
        "primer_nombre_credimax",
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
# Sidebar – Solo la base y la opción ZIP
# =============================
st.sidebar.header("1) Sube la base")
base_file = st.sidebar.file_uploader("Base Credimax (.xlsx)", type=["xlsx"])  # dtype=str

st.sidebar.header("2) Exportación por campaña")
export_por_campana = st.sidebar.checkbox("Generar ZIP por 'Campaña Growth'", value=True)

if not base_file:
    st.info("👆 Sube la base para continuar.")
    st.stop()

# =============================
# Proceso automático (sin UI intermedia)
# =============================
try:
    df = pd.read_excel(base_file, dtype=str)
except Exception as e:
    st.error(f"No se pudo leer el Excel: {e}")
    st.stop()

# Asegurar columnas esperadas
for col in COLUMNAS_ESPERADAS:
    if col not in df.columns:
        df[col] = np.nan

# 1) Validaciones/normalizaciones automáticas
# CEDULA flag
df["CEDULA_VALIDO"] = df["CEDULA"].apply(validar_cedula_10)

# CELULAR normalizado (sin borrar vacíos)
df["CELULAR"] = df["CELULAR"].apply(normalizar_celular_ec)
df["CELULAR_VALIDO"] = df["CELULAR"].notna() & (df["CELULAR"].str.len() == 10)

# Nombres propios
df["primer_nombre"] = df["primer_nombre"].apply(a_nombre_propio)
df["primer_apellido"] = df["primer_apellido"].apply(a_nombre_propio)

# CUPOs a '1,000'
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
        "Fueron limpiadas a vacío (NaN). Revisa las tarjetas en el origen.")
    if len(invalid_ejemplos):
        st.caption("Ejemplos más frecuentes no válidos:")
        st.write(invalid_ejemplos)


# 2) Reglas determinísticas Campaña Growth
for col in ["Campaña Growth", "CANAL", "Producto", "SEGMENTO", "TESTEO CUOTA"]:
    if col not in df.columns:
        df[col] = np.nan

canal_n = df["CANAL"].apply(norm)
prod_n  = df["Producto"].apply(norm)
seg_n   = df["SEGMENTO"].apply(norm)
test_n  = df["TESTEO CUOTA"].apply(norm)

is_online   = (canal_n == "ONLINE")
is_no_cli   = prod_n.isin({"CREDIMAX ONLINE NO CLIENTES", "CREDIMAX ONLINE NO CLIENTE", "CREDIMAX ONLINE NOCLIENTES"})
is_afluente = seg_n.isin(SEG_AFL)
is_masivo   = seg_n.isin(SEG_MAS)
test_es_si  = test_n.isin({"SI", "1", "TRUE", "X"})

# Guardar original y construir final
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

# Comparación para reporte
df_cmp = df.copy()
df_cmp["Coincide (Original vs Reglas)"] = (
    df_cmp["Campaña Growth Original"].fillna("").str.strip() ==
    df_cmp["Campaña Growth"].fillna("").str.strip()
)
df_cmp["Cambio Aplicado (Original -> Final)"] = ~df_cmp["Coincide (Original vs Reglas)"]

# =============================
# Salida minimalista: Resumen + Descargas
# =============================
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

# Export 1: Base limpia final (Excel)
st.download_button(
    "⬇️ Base Credimax LIMPIA FINAL.xlsx",
    data=df_to_excel_bytes(df, sheet_name="base"),
    file_name="Base Credimax LIMPIA FINAL.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# Export 2: Comparación Campaña Growth
cmp_cols = [
    "SEGMENTO","Producto","Ind_Perfil_Campaña","CANAL","TESTEO CUOTA",
    "Campaña Growth Original","Campaña Growth",
    "Coincide (Original vs Reglas)","Cambio Aplicado (Original -> Final)"
]

st.download_button(
    "⬇️ Base Credimax COMPARACION CAMPANA GROWTH.xlsx",
    data=df_to_excel_bytes(df_cmp[cmp_cols], sheet_name="comparacion"),
    file_name="Base Credimax COMPARACION CAMPANA GROWTH.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# ZIP por campaña (según toggle)
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

st.success("✅ Listo. Descarga tus archivos.")
