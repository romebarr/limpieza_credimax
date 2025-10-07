import io
import os
import re
import zipfile
import unicodedata
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Limpieza Credimax – SM Growth Lab", layout="wide")
st.title("🧹 Limpieza y Exportación por Campaña – Credimax")
st.caption("Sube la base, aplica validaciones/normalizaciones, ajusta marcas, reescribe 'Campaña Growth' y descarga todo.")

# =============================
# Helpers generales
# =============================
COLUMNAS_ESPERADAS = [
    "MIS","CEDULA","FECHA NACIMIENTO","primer_nombre","primer_apellido","CELULAR","CORREO CLIENTE",
    "SEGMENTO","CUPO","Plazo","Tasa","Ind_Tasa_Exclusiva","Vigencia","Ind_Campaña_Vigente",
    "Producto","Ind_Perfil_Campaña","CANAL","IND_DESEMBOLSO","Campaña Growth","CUPO_TARJETA_BK",
    "MARCA_TARJETA_BK","BASE MARIO","CUOTA","TESTEO CUOTA"
]

SEG_AFL = {"ELITE", "PREMIUM"}   # Afluente
SEG_MAS = {"SILVER", "PRESTIGE"} # Masivo


def read_txt_lines(file) -> list:
    try:
        content = file.read().decode("utf-8") if hasattr(file, "read") else str(file)
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        return lines
    except Exception:
        return []


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


# =============================
# Sidebar – Inputs
# =============================
st.sidebar.header("1) Sube archivos")
base_file = st.sidebar.file_uploader("Base Credimax (.xlsx)", type=["xlsx"])  # dtype=str

col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    mapa_file = st.file_uploader("Mapa Cambios (opcional .xlsx)", type=["xlsx"], key="mapa")
with col_sb2:
    marcas_file = st.file_uploader("Marcas válidas (opcional .txt)", type=["txt"], key="marcas")

st.sidebar.header("2) Exportación por campaña")
export_por_campana = st.sidebar.checkbox("Generar ZIP por 'Campaña Growth'", value=True)

# =============================
# Carga base
# =============================
if not base_file:
    st.info("👆 Sube la base para empezar.")
    st.stop()

try:
    df = pd.read_excel(base_file, dtype=str)
except Exception as e:
    st.error(f"No se pudo leer el Excel: {e}")
    st.stop()

# Asegurar columnas esperadas
for col in COLUMNAS_ESPERADAS:
    if col not in df.columns:
        df[col] = np.nan

st.subheader("👀 Vista previa de la base")
st.dataframe(df.head(200), use_container_width=True)

# =============================
# Parte 3 – Validaciones y normalizaciones
# =============================
st.divider()
st.subheader("⚙️ Validaciones y normalizaciones")

with st.expander("Configurar reglas"):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        apply_nombre_propio = st.checkbox("Nombres propios", value=True)
    with c2:
        validar_cedula = st.checkbox("Flag CEDULA válida (10 díg)", value=True)
    with c3:
        normalizar_cel = st.checkbox("Normalizar CELULAR a 10 díg (sin borrar vacíos)", value=True)
    with c4:
        normalizar_cupos = st.checkbox("Formatear CUPO* a '1,000'", value=True)

# Aplicar
if validar_cedula:
    df["CEDULA_VALIDO"] = df["CEDULA"].apply(validar_cedula_10)

if normalizar_cel:
    df["CELULAR"] = df["CELULAR"].apply(normalizar_celular_ec)
    df["CELULAR_VALIDO"] = df["CELULAR"].notna() & (df["CELULAR"].str.len() == 10)

if apply_nombre_propio:
    df["primer_nombre"] = df["primer_nombre"].apply(a_nombre_propio)
    df["primer_apellido"] = df["primer_apellido"].apply(a_nombre_propio)

if normalizar_cupos:
    df["CUPO"] = df["CUPO"].apply(cupo_a_texto_miles_coma)
    df["CUPO_TARJETA_BK"] = df["CUPO_TARJETA_BK"].apply(cupo_a_texto_miles_coma)

st.success("Normalizaciones aplicadas.")
st.dataframe(df.head(50), use_container_width=True)

# =============================
# Parte 5 – MARCA_TARJETA_BK (válidos + mapa de cambios)
# =============================
st.divider()
st.subheader("🏷️ Normalización de 'MARCA_TARJETA_BK'")

# Cargar insumos opcionales
if marcas_file is not None:
    marcas_validas = read_txt_lines(marcas_file)
else:
    marcas_validas = [
        "Visa Clásica", "Visa Oro", "Visa Infinite", "Visa Platinum", "Visa Signature"
    ]

if mapa_file is not None:
    try:
        mapa_df_in = pd.read_excel(mapa_file, dtype=str)
        mapa_renombrado = dict(zip(mapa_df_in.get("Valor Original", []), mapa_df_in.get("Nuevo Valor", [])))
    except Exception:
        mapa_renombrado = {}
else:
    mapa_renombrado = {}

valores_unicos = set(df["MARCA_TARJETA_BK"].dropna().unique())
pendientes = [v for v in valores_unicos if v not in marcas_validas and v not in mapa_renombrado]

st.write(f"Valores únicos detectados (no mapeados/validados): **{len(pendientes)}**")

if pendientes:
    pending_df = pd.DataFrame({
        "Valor Original": pendientes,
        "Acción": ["REEMPLAZAR"] * len(pendientes),
        "Nuevo Valor": [""] * len(pendientes),
        "Marcar como válido": [False] * len(pendientes)
    })

    edited = st.data_editor(
        pending_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Acción": st.column_config.SelectboxColumn(options=["REEMPLAZAR", "DEJAR_NULO"]) ,
            "Marcar como válido": st.column_config.CheckboxColumn()
        }
    )

    # Construir actualizaciones a listas/mapas
    for _, row in edited.iterrows():
        val = row["Valor Original"]
        if row.get("Marcar como válido", False):
            if val not in marcas_validas:
                marcas_validas.append(val)
            mapa_renombrado[val] = val
        else:
            accion = row.get("Acción")
            if accion == "DEJAR_NULO":
                mapa_renombrado[val] = None
            else:  # REEMPLAZAR
                nuevo = row.get("Nuevo Valor") or None
                mapa_renombrado[val] = nuevo

# Aplicar reemplazos
if mapa_renombrado:
    df["MARCA_TARJETA_BK"] = df["MARCA_TARJETA_BK"].replace(mapa_renombrado)

# Descargas de insumos actualizados
col_m1, col_m2 = st.columns(2)
with col_m1:
    marcas_txt = "\n".join(sorted(dict.fromkeys(marcas_validas)))
    st.download_button(
        "⬇️ Descargar 'marcas_validas_marca_tarjeta.txt'",
        data=marcas_txt.encode("utf-8"),
        file_name="marcas_validas_marca_tarjeta.txt",
        mime="text/plain",
    )
with col_m2:
    mapa_out_df = pd.DataFrame(list(mapa_renombrado.items()), columns=["Valor Original", "Nuevo Valor"])
    st.download_button(
        "⬇️ Descargar 'mapa_cambios_marca_tarjeta.xlsx'",
        data=df_to_excel_bytes(mapa_out_df, "mapa"),
        file_name="mapa_cambios_marca_tarjeta.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# =============================
# Parte 8 – Reglas determinísticas Campaña Growth
# =============================
st.divider()
st.subheader("🧠 Reescritura de 'Campaña Growth' (reglas)")

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

# Escribir final y comparación
df["Campaña Growth"] = camp_final

cmp_cols = [
    "SEGMENTO","Producto","Ind_Perfil_Campaña","CANAL","TESTEO CUOTA",
    "Campaña Growth Original","Campaña Growth"
]

df_cmp = df.copy()
df_cmp["Coincide (Original vs Reglas)"] = (
    df_cmp["Campaña Growth Original"].fillna("").str.strip() ==
    df_cmp["Campaña Growth"].fillna("").str.strip()
)
df_cmp["Cambio Aplicado (Original -> Final)"] = ~df_cmp["Coincide (Original vs Reglas)"]

st.markdown("**Resumen aplicado:**")
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

st.dataframe(df_cmp[cmp_cols + ["Coincide (Original vs Reglas)", "Cambio Aplicado (Original -> Final)"]].head(50), use_container_width=True)

# =============================
# Parte 9 – Exportación por campaña (sin borrar filas sin celular, con encabezados)
# =============================
st.divider()
st.subheader("📦 Exportación")

# Export 1: Base limpia final (Excel)
st.download_button(
    "⬇️ Descargar 'Base Credimax LIMPIA FINAL.xlsx'",
    data=df_to_excel_bytes(df, sheet_name="base"),
    file_name="Base Credimax LIMPIA FINAL.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# Export 2: Comparación Campaña Growth
st.download_button(
    "⬇️ Descargar 'Base Credimax COMPARACION CAMPANA GROWTH.xlsx'",
    data=df_to_excel_bytes(df_cmp[cmp_cols + ["Coincide (Original vs Reglas)", "Cambio Aplicado (Original -> Final)"]], sheet_name="comparacion"),
    file_name="Base Credimax COMPARACION CAMPANA GROWTH.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# Export 3: ZIP por campaña
if export_por_campana:
    st.markdown("**ZIP por 'Campaña Growth' (incluye filas sin celular):**")

    # Preparar df válido para export
    col_campana = "Campaña Growth"
    for col in [col_campana, "IND_DESEMBOLSO", "CELULAR"]:
        if col not in df.columns:
            df[col] = np.nan

    # Filtro IND_DESEMBOLSO == '0'
    df_exp = df[df['IND_DESEMBOLSO'] == '0'].copy()

    # Trim y no-vacíos de campaña
    df_exp[col_campana] = df_exp[col_campana].astype(str).str.strip()
    mask_no_vacio = df_exp[col_campana].notna() & (df_exp[col_campana].str.len() > 0) & (df_exp[col_campana].str.lower() != 'nan')
    df_exp = df_exp[mask_no_vacio].copy()

    # Mapeo columnas
    mapeo_columnas = {
        'primer_nombre': 'nombre',
        'CORREO CLIENTE': 'correo',
        'CUPO': 'monto_credito_aprob',
        'CUOTA': 'cuota_credimax',
        'Tasa': 'Tasa_Credito_Aprob',
        'CUPO_TARJETA_BK': 'Cupo_Aprobado_OB_BK',
        'MARCA_TARJETA_BK': 'Marca_BK_OB'
    }

    for col in list(mapeo_columnas.keys()) + [col_campana, "IND_DESEMBOLSO", "CELULAR"]:
        if col not in df_exp.columns:
            df_exp[col] = np.nan

    # Formateo CUOTA
    df_exp["CUOTA"] = df_exp["CUOTA"].apply(formatear_cuota)

    columnas_originales = list(mapeo_columnas.keys()) + [col_campana, "CELULAR"]
    df_exp = df_exp[columnas_originales].copy()
    df_exp = df_exp.rename(columns=mapeo_columnas)

    # Normalizar celulares (no eliminar vacíos)
    def cel_10(s):
        if pd.isna(s):
            return np.nan
        dig = re.sub(r"\D+", "", str(s))
        return dig if len(dig) == 10 else s

    df_exp["CELULAR"] = df_exp["CELULAR"].apply(cel_10)

    # Generar ZIP en memoria
    fecha_archivo = datetime.now().strftime("%d-%m")
    zip_buf = io.BytesIO()

    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for nombre, grupo in df_exp.groupby(col_campana, dropna=False):
            if pd.isna(nombre):
                continue
            nombre_archivo = safe_filename(nombre)
            if not nombre_archivo or nombre_archivo.lower() == 'nan':
                continue

            # Quitar columna campaña, ordenar poniendo CELULAR primero
            grupo_salida = grupo.drop(columns=[col_campana]).copy()
            cols = ["CELULAR"] + [c for c in grupo_salida.columns if c != "CELULAR"]
            grupo_salida = grupo_salida[cols]

            excel_bytes = df_to_excel_bytes(grupo_salida, sheet_name="base")
            zf.writestr(f"{nombre_archivo}_{fecha_archivo}.xlsx", excel_bytes)

    zip_buf.seek(0)

    st.download_button(
        "⬇️ Descargar ZIP por campaña",
        data=zip_buf,
        file_name=f"archivos_por_campana_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
        mime="application/zip",
    )

st.success("✅ Proceso completado. Puedes descargar los archivos arriba.")
