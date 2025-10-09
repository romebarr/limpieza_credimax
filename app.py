 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/app.py b/app.py
index 96adc6688e7b8016a5bfc55121d6ab82df932db2..f0bbc4100919cd200ddc58621149471b3813e886 100644
--- a/app.py
+++ b/app.py
@@ -1,408 +1,815 @@
 import io
-import os
+import json
 import re
-import zipfile
 import unicodedata
+import zipfile
 from datetime import datetime
 from pathlib import Path
 
 import numpy as np
 import pandas as pd
 import streamlit as st
 
 # =============================
 # Config básica
 # =============================
 st.set_page_config(page_title="Limpieza Credimax – SM Growth Lab", layout="wide")
-st.title("🧹 Limpieza y Exportación por Campaña – Credimax")
-st.caption("Sube la base, aplicamos validaciones/normalizaciones y reescritura de 'Campaña Growth'. Descarga resultados.")
+st.title("🧹 Limpieza y Exportación – Credimax & Bankard")
+st.caption(
+    "Sube la base correspondiente, aplicamos validaciones/normalizaciones y preparamos las "
+    "descargas segmentadas según las reglas de cada flujo."
+)
 
 # =============================
-# Helpers
+# Helpers – Credimax
 # =============================
 COLUMNAS_ESPERADAS = [
-    "MIS","CEDULA","FECHA NACIMIENTO","primer_nombre","primer_apellido","CELULAR","CORREO CLIENTE",
-    "SEGMENTO","CUPO","Plazo","Tasa","Ind_Tasa_Exclusiva","Vigencia","Ind_Campaña_Vigente",
-    "Producto","Ind_Perfil_Campaña","CANAL","IND_DESEMBOLSO","Campaña Growth","CUPO_TARJETA_BK",
-    "MARCA_TARJETA_BK","BASE MARIO","CUOTA","TESTEO CUOTA"
+    "MIS",
+    "CEDULA",
+    "FECHA NACIMIENTO",
+    "primer_nombre",
+    "primer_apellido",
+    "CELULAR",
+    "CORREO CLIENTE",
+    "SEGMENTO",
+    "CUPO",
+    "Plazo",
+    "Tasa",
+    "Ind_Tasa_Exclusiva",
+    "Vigencia",
+    "Ind_Campaña_Vigente",
+    "Producto",
+    "Ind_Perfil_Campaña",
+    "CANAL",
+    "IND_DESEMBOLSO",
+    "Campaña Growth",
+    "CUPO_TARJETA_BK",
+    "MARCA_TARJETA_BK",
+    "BASE MARIO",
+    "CUOTA",
+    "TESTEO CUOTA",
 ]
 
-# Segmentos
-SEG_AFL = {"ELITE", "PREMIUM"}   # Afluente
-SEG_MAS = {"SILVER", "PRESTIGE"} # Masivo
+SEG_AFL = {"ELITE", "PREMIUM"}  # Afluente
+SEG_MAS = {"SILVER", "PRESTIGE"}  # Masivo
 
-# Marcas válidas por defecto (sin subida de archivos)
 MARCAS_VALIDAS_DEFAULT = [
-    "Visa Clásica", "Visa Oro", "Visa Infinite", "Visa Platinum", "Visa Signature"
+    "Visa Clásica",
+    "Visa Oro",
+    "Visa Infinite",
+    "Visa Platinum",
+    "Visa Signature",
+]
+
+# =============================
+# Helpers – Bankard
+# =============================
+VALORES_BIN_PERMITIDOS = [
+    "Visa Oro",
+    "Visa Platinum",
+    "Mastercard Black",
+    "Mastercard Clásica",
+    "Mastercard Oro",
+    "Visa Clásica",
+    "Visa Infinite",
+    "Visa Signature",
 ]
 
+MEMORIA_CORRECCIONES_PATH = Path("memoria_correcciones_bin.json")
+EXCLUSIONES_BANKARD_DIR = Path("data/exclusiones_bankard")
+EXCLUSIONES_BANKARD_DIR.mkdir(parents=True, exist_ok=True)
+
 
+# =============================
+# Funciones comunes
+# =============================
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
-    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
+    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
 
 
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
-    return (str(s)
-            .replace('/', '_').replace('\\', '_')
-            .replace(':', '').replace('*', '')
-            .replace('?', '').replace('"', '')
-            .replace('<', '').replace('>', '')
-            .replace('|', '').strip())
+    return (
+        str(s)
+        .replace("/", "_")
+        .replace("\\", "_")
+        .replace(":", "")
+        .replace("*", "")
+        .replace("?", "")
+        .replace('"', "")
+        .replace("<", "")
+        .replace(">", "")
+        .replace("|", "")
+        .strip()
+    )
 
 
 def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "base") -> bytes:
     buf = io.BytesIO()
     with pd.ExcelWriter(buf, engine="openpyxl") as writer:
         df.to_excel(writer, index=False, sheet_name=sheet_name)
     buf.seek(0)
     return buf.read()
 
-# =============================
-# Sidebar – Solo la base y la opción ZIP
-# =============================
-st.sidebar.header("1) Sube la base")
-base_file = st.sidebar.file_uploader("Base Credimax (.xlsx)", type=["xlsx"])  # dtype=str
-
-st.sidebar.header("2) Exportación por campaña")
-export_por_campana = st.sidebar.checkbox("Generar ZIP por 'Campaña Growth'", value=True)
 
-if not base_file:
-    st.info("👆 Sube la base para continuar.")
-    st.stop()
+def pad_10_digitos(valor):
+    if pd.isna(valor):
+        return ""
+    s = re.sub(r"\D", "", str(valor))
+    if s == "":
+        return ""
+    if len(s) < 10:
+        s = s.zfill(10)
+    elif len(s) > 10:
+        s = s[:10]
+    return s
 
-# =============================
-# Proceso automático (sin UI intermedia)
-# =============================
-try:
-    df = pd.read_excel(base_file, dtype=str)
-except Exception as e:
-    st.error(f"No se pudo leer el Excel: {e}")
-    st.stop()
-
-# Asegurar columnas esperadas
-for col in COLUMNAS_ESPERADAS:
-    if col not in df.columns:
-        df[col] = np.nan
-
-# 1) Validaciones/normalizaciones automáticas
-# CEDULA flag
-df["CEDULA_VALIDO"] = df["CEDULA"].apply(validar_cedula_10)
-
-# CELULAR normalizado (sin borrar vacíos)
-df["CELULAR"] = df["CELULAR"].apply(normalizar_celular_ec)
-df["CELULAR_VALIDO"] = df["CELULAR"].notna() & (df["CELULAR"].str.len() == 10)
-
-# Nombres propios
-df["primer_nombre"] = df["primer_nombre"].apply(a_nombre_propio)
-df["primer_apellido"] = df["primer_apellido"].apply(a_nombre_propio)
-
-# CUPOs a '1,000'
-df["CUPO"] = df["CUPO"].apply(cupo_a_texto_miles_coma)
-df["CUPO_TARJETA_BK"] = df["CUPO_TARJETA_BK"].apply(cupo_a_texto_miles_coma)
-
-# MARCA_TARJETA_BK: forzar a NaN cuando no esté en lista válida (comparación normalizada)
-valid_norms = {norm(x) for x in MARCAS_VALIDAS_DEFAULT}
-marca_norm = df["MARCA_TARJETA_BK"].apply(lambda x: norm(x) if pd.notna(x) else x)
-mask_invalid_marcas = df["MARCA_TARJETA_BK"].notna() & (~marca_norm.isin(valid_norms))
-invalid_ejemplos = (
-    df.loc[mask_invalid_marcas, "MARCA_TARJETA_BK"].dropna().astype(str).str.strip().value_counts().head(10)
-)
-if mask_invalid_marcas.any():
-    df.loc[mask_invalid_marcas, "MARCA_TARJETA_BK"] = np.nan
-    st.warning(
-        f"Se detectaron **{int(mask_invalid_marcas.sum())}** marcas de tarjeta no válidas. "
-        "Fueron limpiadas a vacío (NaN). Revisa las tarjetas en el origen.")
-    if len(invalid_ejemplos):
-        st.caption("Ejemplos más frecuentes no válidos:")
-        st.write(invalid_ejemplos)
-
-
-# 2) Reglas determinísticas Campaña Growth
-for col in ["Campaña Growth", "CANAL", "Producto", "SEGMENTO", "TESTEO CUOTA"]:
-    if col not in df.columns:
-        df[col] = np.nan
-
-canal_n = df["CANAL"].apply(norm)
-prod_n  = df["Producto"].apply(norm)
-seg_n   = df["SEGMENTO"].apply(norm)
-test_n  = df["TESTEO CUOTA"].apply(norm)
-
-is_online   = (canal_n == "ONLINE")
-is_no_cli   = prod_n.isin({"CREDIMAX ONLINE NO CLIENTES", "CREDIMAX ONLINE NO CLIENTE", "CREDIMAX ONLINE NOCLIENTES"})
-is_afluente = seg_n.isin(SEG_AFL)
-is_masivo   = seg_n.isin(SEG_MAS)
-test_es_si  = test_n.isin({"SI", "1", "TRUE", "X"})
-
-# Guardar original y construir final
-df["Campaña Growth Original"] = df["Campaña Growth"]
-camp_final = df["Campaña Growth"].astype("object").copy()
-
-mask_no_cli_afl = is_online & is_no_cli & is_afluente
-mask_no_cli_mas = is_online & is_no_cli & is_masivo
-mask_online_otros = is_online & (~is_no_cli)
-mask_elite = mask_online_otros & (seg_n == "ELITE")
-mask_premium = mask_online_otros & (seg_n == "PREMIUM")
-mask_masivo_base = mask_online_otros & is_masivo
-mask_masivo_cuotas = mask_masivo_base & test_es_si
-mask_masivo_sin_cuotas = mask_masivo_base & (~test_es_si)
-
-camp_final.loc[mask_no_cli_afl] = "Credimax Online No Clientes Afluente"
-camp_final.loc[mask_no_cli_mas] = "Credimax Online No Clientes Masivo"
-camp_final.loc[mask_elite] = "Credimax Online Elite"
-camp_final.loc[mask_premium] = "Credimax Online Premium"
-camp_final.loc[mask_masivo_cuotas] = "Credimax Online Masivo Cuotas"
-camp_final.loc[mask_masivo_sin_cuotas] = "Credimax Online Masivo"
-
-df["Campaña Growth"] = camp_final
-
-# Comparación para reporte
-df_cmp = df.copy()
-df_cmp["Coincide (Original vs Reglas)"] = (
-    df_cmp["Campaña Growth Original"].fillna("").str.strip() ==
-    df_cmp["Campaña Growth"].fillna("").str.strip()
-)
-df_cmp["Cambio Aplicado (Original -> Final)"] = ~df_cmp["Coincide (Original vs Reglas)"]
 
 # =============================
-# Salida minimalista: Resumen + Descargas
+# Funciones específicas Credimax
 # =============================
-st.subheader("🧠 Reescritura de 'Campaña Growth' (reglas)")
-
-col_r1, col_r2, col_r3 = st.columns(3)
-with col_r1:
-    st.metric("No Clientes Afluente", int(mask_no_cli_afl.sum()))
-    st.metric("Masivo (sin cuotas)", int(mask_masivo_sin_cuotas.sum()))
-with col_r2:
-    st.metric("No Clientes Masivo", int(mask_no_cli_mas.sum()))
-    st.metric("Elite", int(mask_elite.sum()))
-with col_r3:
-    st.metric("Masivo (cuotas)", int(mask_masivo_cuotas.sum()))
-    st.metric("Premium", int(mask_premium.sum()))
-
-st.divider()
-st.subheader("📦 Descargas")
-
-# Export 1: Base limpia final (Excel)
-st.download_button(
-    "⬇️ Base Credimax LIMPIA FINAL.xlsx",
-    data=df_to_excel_bytes(df, sheet_name="base"),
-    file_name="Base Credimax LIMPIA FINAL.xlsx",
-    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
-)
-
-# Export 2: Comparación Campaña Growth
-cmp_cols = [
-    "SEGMENTO","Producto","Ind_Perfil_Campaña","CANAL","TESTEO CUOTA",
-    "Campaña Growth Original","Campaña Growth",
-    "Coincide (Original vs Reglas)","Cambio Aplicado (Original -> Final)"
-]
-
-st.download_button(
-    "⬇️ Base Credimax COMPARACION CAMPANA GROWTH.xlsx",
-    data=df_to_excel_bytes(df_cmp[cmp_cols], sheet_name="comparacion"),
-    file_name="Base Credimax COMPARACION CAMPANA GROWTH.xlsx",
-    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
-)
-
-# ZIP por campaña (según toggle)
-if export_por_campana:
-    col_campana = "Campaña Growth"
-    for col in [col_campana, "IND_DESEMBOLSO", "CELULAR"]:
-        if col not in df.columns:
-            df[col] = np.nan
+def preparar_zip_por_campana(df: pd.DataFrame, col_campana: str = "Campaña Growth"):
+    """Genera el ZIP segmentado por campaña y devuelve (bytes_zip, columnas_exportadas)."""
+    columnas_necesarias = {
+        col_campana,
+        "IND_DESEMBOLSO",
+        "CELULAR",
+        "primer_nombre",
+        "CORREO CLIENTE",
+        "CUPO",
+        "CUOTA",
+        "Tasa",
+        "CUPO_TARJETA_BK",
+        "MARCA_TARJETA_BK",
+    }
 
-    # Filtrar IND_DESEMBOLSO == '0'
-    df_exp = df[df['IND_DESEMBOLSO'] == '0'].copy()
+    df_trabajo = df.copy()
+    for col in columnas_necesarias:
+        if col not in df_trabajo.columns:
+            df_trabajo[col] = np.nan
 
-    # Trim campaña y quitar vacíos
+    df_exp = df_trabajo[df_trabajo["IND_DESEMBOLSO"] == "0"].copy()
     df_exp[col_campana] = df_exp[col_campana].astype(str).str.strip()
-    mask_no_vacio = df_exp[col_campana].notna() & (df_exp[col_campana].str.len() > 0) & (df_exp[col_campana].str.lower() != 'nan')
+    mask_no_vacio = (
+        df_exp[col_campana].notna()
+        & (df_exp[col_campana] != "")
+        & (~df_exp[col_campana].str.lower().eq("nan"))
+    )
     df_exp = df_exp[mask_no_vacio].copy()
 
-    # Mapeo columnas de salida
+    if df_exp.empty:
+        return None, []
+
     mapeo_columnas = {
-        'primer_nombre': 'nombre',
-        'CORREO CLIENTE': 'correo',
-        'CUPO': 'monto_credito_aprob',
-        'CUOTA': 'cuota_credimax',
-        'Tasa': 'Tasa_Credito_Aprob',
-        'CUPO_TARJETA_BK': 'Cupo_Aprobado_OB_BK',
-        'MARCA_TARJETA_BK': 'Marca_BK_OB'
+        "primer_nombre": "primer_nombre_credimax",
+        "CORREO CLIENTE": "correo",
+        "CUPO": "monto_credito_aprob",
+        "CUOTA": "cuota_credimax",
+        "Tasa": "Tasa_Credito_Aprob",
+        "CUPO_TARJETA_BK": "Cupo_Aprobado_OB_BK",
+        "MARCA_TARJETA_BK": "Marca_BK_OB",
     }
 
-    for col in list(mapeo_columnas.keys()) + [col_campana, "IND_DESEMBOLSO", "CELULAR"]:
-        if col not in df_exp.columns:
-            df_exp[col] = np.nan
-
-    # Formateo cuota a 2 decimales
     df_exp["CUOTA"] = df_exp["CUOTA"].apply(formatear_cuota)
 
     columnas_originales = list(mapeo_columnas.keys()) + [col_campana, "CELULAR"]
     df_exp = df_exp[columnas_originales].copy()
     df_exp = df_exp.rename(columns=mapeo_columnas)
 
-    # Normalizar celulares (no eliminar vacíos)
     def cel_10(s):
         if pd.isna(s):
             return np.nan
-        dig = re.sub(r"[^0-9]", "", str(s))
+        dig = re.sub(r"\D+", "", str(s))
         return dig if len(dig) == 10 else s
 
     df_exp["CELULAR"] = df_exp["CELULAR"].apply(cel_10)
 
-    # Construir ZIP en memoria
+    columnas_exportadas = [
+        "CELULAR",
+        "primer_nombre_credimax",
+        "correo",
+        "monto_credito_aprob",
+        "cuota_credimax",
+        "Tasa_Credito_Aprob",
+        "Cupo_Aprobado_OB_BK",
+        "Marca_BK_OB",
+    ]
+
+    for col in columnas_exportadas:
+        if col not in df_exp.columns:
+            df_exp[col] = np.nan
+
     fecha_archivo = datetime.now().strftime("%d-%m")
     zip_buf = io.BytesIO()
 
     with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
         for nombre, grupo in df_exp.groupby(col_campana, dropna=False):
             if pd.isna(nombre):
                 continue
             nombre_archivo = safe_filename(nombre)
-            if not nombre_archivo or nombre_archivo.lower() == 'nan':
+            if not nombre_archivo or nombre_archivo.lower() == "nan":
                 continue
+
             grupo_salida = grupo.drop(columns=[col_campana]).copy()
-            cols = ["CELULAR"] + [c for c in grupo_salida.columns if c != "CELULAR"]
-            grupo_salida = grupo_salida[cols]
+            grupo_salida = grupo_salida.reindex(columns=columnas_exportadas)
             excel_bytes = df_to_excel_bytes(grupo_salida, sheet_name="base")
             zf.writestr(f"{nombre_archivo}_{fecha_archivo}.xlsx", excel_bytes)
 
     zip_buf.seek(0)
+    return zip_buf.read(), columnas_exportadas
 
-    st.download_button(
-        "⬇️ Descargar ZIP por campaña",
-        data=zip_buf,
-        file_name=f"Campanas_segmentadas_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
-        mime="application/zip",
+
+# =============================
+# Funciones específicas Bankard
+# =============================
+def cargar_memoria_correcciones():
+    if MEMORIA_CORRECCIONES_PATH.exists():
+        try:
+            return json.loads(MEMORIA_CORRECCIONES_PATH.read_text(encoding="utf-8"))
+        except json.JSONDecodeError:
+            return {}
+    return {}
+
+
+def guardar_memoria_correcciones(memoria):
+    MEMORIA_CORRECCIONES_PATH.write_text(
+        json.dumps(memoria, ensure_ascii=False, indent=2), encoding="utf-8"
+    )
+
+
+def limpiar_cupo_bankard(df):
+    df = df.copy()
+    if "cupo" not in df.columns:
+        df["cupo"] = 0
+        return df
+
+    def solo_numero(val):
+        if pd.isna(val):
+            return 0
+        dig = re.sub(r"[^0-9]", "", str(val))
+        if dig == "":
+            return 0
+        return int(dig)
+
+    df["cupo"] = df["cupo"].apply(solo_numero)
+    return df
+
+
+def detectar_bins_no_permitidos(df, memoria):
+    if "BIN" not in df.columns:
+        return []
+    valores_actuales = {
+        str(x).strip() for x in df["BIN"].dropna().unique().tolist()
+    }
+    permitidos = set(VALORES_BIN_PERMITIDOS)
+    memorizados = set(memoria.keys())
+    return sorted(v for v in valores_actuales if v not in permitidos and v not in memorizados)
+
+
+def aplicar_correcciones_bin(df, memoria):
+    df = df.copy()
+    if "BIN" not in df.columns:
+        df["BIN"] = np.nan
+        return df
+
+    def corregir(valor):
+        if pd.isna(valor):
+            return valor
+        val = str(valor).strip()
+        if val in memoria and memoria[val]:
+            return memoria[val]
+        if val in VALORES_BIN_PERMITIDOS:
+            return val
+        return val.title()
+
+    df["BIN"] = df["BIN"].apply(corregir)
+    return df
+
+
+def filtrar_vigencia_bankard(df):
+    df = df.copy()
+    col_vigencia = None
+    for posible in ["VIGENICA. BASE", "VIGENCIA. BASE", "VIGENCIA BASE"]:
+        if posible in df.columns:
+            col_vigencia = posible
+            break
+    if not col_vigencia:
+        return df, 0
+
+    fechas = pd.to_datetime(df[col_vigencia], errors="coerce")
+    hoy = datetime.now().date()
+    mascara = fechas.dt.date >= hoy
+    mascara = mascara.fillna(False)
+    excluidos = int((~mascara).sum())
+    df_filtrado = df[mascara].copy()
+    return df_filtrado, excluidos
+
+
+def limpiar_telefonos_cedulas_bankard(df):
+    df = df.copy()
+    if "telefono" not in df.columns:
+        df["telefono"] = ""
+    if "cedula" not in df.columns:
+        df["cedula"] = ""
+    df["telefono"] = df["telefono"].apply(pad_10_digitos)
+    df["cedula"] = df["cedula"].apply(pad_10_digitos)
+    return df
+
+
+def cargar_cedulas_excluir_uploads(files):
+    cedulas = set()
+    errores = []
+    for upload in files or []:
+        try:
+            upload.seek(0)
+        except Exception:
+            pass
+        try:
+            df_exc = pd.read_excel(upload, dtype=str)
+        except Exception as exc:
+            errores.append(f"{upload.name}: {exc}")
+            continue
+        if "IDENTIFICACION" not in df_exc.columns:
+            errores.append(f"{upload.name}: no contiene columna 'IDENTIFICACION'")
+            continue
+        cedulas.update(df_exc["IDENTIFICACION"].astype(str).apply(pad_10_digitos))
+    return cedulas, errores
+
+
+def cargar_cedulas_excluir_directorio(path: Path):
+    cedulas = set()
+    errores = []
+    archivos = []
+    if not path.exists():
+        return cedulas, errores, archivos
+
+    for archivo in path.glob("*.xlsx"):
+        if archivo.name.startswith("~$"):
+            continue
+        try:
+            df_exc = pd.read_excel(archivo, dtype=str)
+        except Exception as exc:
+            errores.append(f"{archivo.name}: {exc}")
+            continue
+        if "IDENTIFICACION" not in df_exc.columns:
+            errores.append(
+                f"{archivo.name}: no contiene columna 'IDENTIFICACION'"
+            )
+            continue
+        cedulas.update(
+            df_exc["IDENTIFICACION"].astype(str).apply(pad_10_digitos)
+        )
+        archivos.append(archivo.name)
+
+    return cedulas, errores, archivos
+
+
+def marcar_exclusiones_varios(df, cedulas_excluir):
+    df = df.copy()
+    if "exclusion" in df.columns:
+        base = df["exclusion"].astype(str)
+    elif "Excluir" in df.columns:
+        base = df["Excluir"].astype(str)
+    else:
+        base = pd.Series("NO", index=df.index)
+
+    def normalizar(valor):
+        return "SI" if str(valor).strip().upper() == "SI" else "NO"
+
+    df["exclusion"] = base.apply(normalizar)
+
+    if cedulas_excluir:
+        df["cedula"] = df["cedula"].astype(str)
+        mask = df["cedula"].isin(cedulas_excluir)
+        df.loc[mask, "exclusion"] = "SI"
+
+    return df
+
+
+def ensure_column_from(df, target, sources=(), fill_value=""):
+    if target in df.columns:
+        return target
+    for src in sources:
+        if src in df.columns:
+            df[target] = df[src]
+            return target
+    df[target] = fill_value
+    return target
+
+
+def preparar_zip_bankard(df, col_tipo="TIPO ", col_exclusion="exclusion"):
+    if col_tipo not in df.columns or col_exclusion not in df.columns:
+        return None, []
+
+    hoy_str = datetime.now().strftime("%d%m")
+    zip_buf = io.BytesIO()
+    archivos = 0
+    columnas_exportadas = df.columns.tolist()
+
+    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
+        for tipo in sorted(df[col_tipo].dropna().astype(str).unique()):
+            for excl in ["SI", "NO"]:
+                subset = df[
+                    (df[col_tipo].astype(str) == tipo)
+                    & (df[col_exclusion].astype(str).str.upper() == excl)
+                ].copy()
+                if subset.empty:
+                    continue
+                if "cupo" in subset.columns:
+                    subset["cupo"] = subset["cupo"].apply(
+                        lambda x: f"{int(x):,}" if str(x).strip() != "" else ""
+                    )
+                nombre_tipo = safe_filename(tipo) or "SIN_TIPO"
+                nombre_archivo = f"{nombre_tipo}_{excl}_{hoy_str}.xlsx"
+                zf.writestr(nombre_archivo, df_to_excel_bytes(subset, sheet_name="base"))
+                archivos += 1
+
+    if archivos == 0:
+        return None, []
+
+    zip_buf.seek(0)
+    return zip_buf.read(), columnas_exportadas
+
+
+# =============================
+# Flujos de ejecución
+# =============================
+def run_credimax():
+    st.sidebar.header("1) Sube la base Credimax")
+    base_file = st.sidebar.file_uploader(
+        "Base Credimax (.xlsx)", type=["xlsx"], key="base_credimax"
     )
 
-# Export 3: ZIP por campaña (manteniendo filas sin celular y encabezados)
-if export_por_campana:
-    col_campana = "Campaña Growth"
-    for col in [col_campana, "IND_DESEMBOLSO", "CELULAR"]:
+    st.sidebar.header("2) Exportación por campaña")
+    export_por_campana = st.sidebar.checkbox(
+        "Generar ZIP por 'Campaña Growth'", value=True, key="zip_credimax"
+    )
+
+    if not base_file:
+        st.info("👆 Sube la base para continuar.")
+        return
+
+    try:
+        df = pd.read_excel(base_file, dtype=str)
+    except Exception as e:
+        st.error(f"No se pudo leer el Excel: {e}")
+        return
+
+    for col in COLUMNAS_ESPERADAS:
         if col not in df.columns:
             df[col] = np.nan
 
-    df_exp = df[df['IND_DESEMBOLSO'] == '0'].copy()
+    df["CEDULA_VALIDO"] = df["CEDULA"].apply(validar_cedula_10)
+    df["CELULAR"] = df["CELULAR"].apply(normalizar_celular_ec)
+    df["CELULAR_VALIDO"] = df["CELULAR"].notna() & (df["CELULAR"].str.len() == 10)
 
-    df_exp[col_campana] = df_exp[col_campana].astype(str).str.strip()
-    mask_no_vacio = df_exp[col_campana].notna() & (df_exp[col_campana].str.len() > 0) & (df_exp[col_campana].str.lower() != 'nan')
-    df_exp = df_exp[mask_no_vacio].copy()
+    df["primer_nombre"] = df["primer_nombre"].apply(a_nombre_propio)
+    df["primer_apellido"] = df["primer_apellido"].apply(a_nombre_propio)
 
-    mapeo_columnas = {
-        'primer_nombre': 'nombre',
-        'CORREO CLIENTE': 'correo',
-        'CUPO': 'monto_credito_aprob',
-        'CUOTA': 'cuota_credimax',
-        'Tasa': 'Tasa_Credito_Aprob',
-        'CUPO_TARJETA_BK': 'Cupo_Aprobado_OB_BK',
-        'MARCA_TARJETA_BK': 'Marca_BK_OB'
-    }
+    df["CUPO"] = df["CUPO"].apply(cupo_a_texto_miles_coma)
+    df["CUPO_TARJETA_BK"] = df["CUPO_TARJETA_BK"].apply(cupo_a_texto_miles_coma)
 
-    for col in list(mapeo_columnas.keys()) + [col_campana, "IND_DESEMBOLSO", "CELULAR"]:
-        if col not in df_exp.columns:
-            df_exp[col] = np.nan
+    valid_norms = {norm(x) for x in MARCAS_VALIDAS_DEFAULT}
+    marca_norm = df["MARCA_TARJETA_BK"].apply(lambda x: norm(x) if pd.notna(x) else x)
+    mask_invalid_marcas = df["MARCA_TARJETA_BK"].notna() & (~marca_norm.isin(valid_norms))
+    invalid_ejemplos = (
+        df.loc[mask_invalid_marcas, "MARCA_TARJETA_BK"].dropna().astype(str).str.strip().value_counts().head(10)
+    )
+    if mask_invalid_marcas.any():
+        df.loc[mask_invalid_marcas, "MARCA_TARJETA_BK"] = np.nan
+        st.warning(
+            f"Se detectaron **{int(mask_invalid_marcas.sum())}** marcas de tarjeta no válidas. "
+            "Fueron limpiadas a vacío (NaN). Revisa las tarjetas en el origen."
+        )
+        if len(invalid_ejemplos):
+            st.caption("Ejemplos más frecuentes no válidos:")
+            st.write(invalid_ejemplos)
+
+    for col in ["Campaña Growth", "CANAL", "Producto", "SEGMENTO", "TESTEO CUOTA"]:
+        if col not in df.columns:
+            df[col] = np.nan
 
-    df_exp["CUOTA"] = df_exp["CUOTA"].apply(formatear_cuota)
+    canal_n = df["CANAL"].apply(norm)
+    prod_n = df["Producto"].apply(norm)
+    seg_n = df["SEGMENTO"].apply(norm)
+    test_n = df["TESTEO CUOTA"].apply(norm)
+
+    is_online = canal_n == "ONLINE"
+    is_no_cli = prod_n.isin({
+        "CREDIMAX ONLINE NO CLIENTES",
+        "CREDIMAX ONLINE NO CLIENTE",
+        "CREDIMAX ONLINE NOCLIENTES",
+    })
+    is_afluente = seg_n.isin(SEG_AFL)
+    is_masivo = seg_n.isin(SEG_MAS)
+    test_es_si = test_n.isin({"SI", "1", "TRUE", "X"})
+
+    df["Campaña Growth Original"] = df["Campaña Growth"]
+    camp_final = df["Campaña Growth"].astype("object").copy()
+
+    mask_no_cli_afl = is_online & is_no_cli & is_afluente
+    mask_no_cli_mas = is_online & is_no_cli & is_masivo
+    mask_online_otros = is_online & (~is_no_cli)
+    mask_elite = mask_online_otros & (seg_n == "ELITE")
+    mask_premium = mask_online_otros & (seg_n == "PREMIUM")
+    mask_masivo_base = mask_online_otros & is_masivo
+    mask_masivo_cuotas = mask_masivo_base & test_es_si
+    mask_masivo_sin_cuotas = mask_masivo_base & (~test_es_si)
+
+    camp_final.loc[mask_no_cli_afl] = "Credimax Online No Clientes Afluente"
+    camp_final.loc[mask_no_cli_mas] = "Credimax Online No Clientes Masivo"
+    camp_final.loc[mask_elite] = "Credimax Online Elite"
+    camp_final.loc[mask_premium] = "Credimax Online Premium"
+    camp_final.loc[mask_masivo_cuotas] = "Credimax Online Masivo Cuotas"
+    camp_final.loc[mask_masivo_sin_cuotas] = "Credimax Online Masivo"
+
+    df["Campaña Growth"] = camp_final
+
+    df_cmp = df.copy()
+    df_cmp["Coincide (Original vs Reglas)"] = (
+        df_cmp["Campaña Growth Original"].fillna("").str.strip()
+        == df_cmp["Campaña Growth"].fillna("").str.strip()
+    )
+    df_cmp["Cambio Aplicado (Original -> Final)"] = ~df_cmp["Coincide (Original vs Reglas)"]
 
-    columnas_originales = list(mapeo_columnas.keys()) + [col_campana, "CELULAR"]
-    df_exp = df_exp[columnas_originales].copy()
-    df_exp = df_exp.rename(columns=mapeo_columnas)
+    st.subheader("🧠 Reescritura de 'Campaña Growth' (reglas)")
 
-    def cel_10(s):
-        if pd.isna(s):
-            return np.nan
-        dig = re.sub(r"\D+", "", str(s))
-        return dig if len(dig) == 10 else s
+    col_r1, col_r2, col_r3 = st.columns(3)
+    with col_r1:
+        st.metric("No Clientes Afluente", int(mask_no_cli_afl.sum()))
+        st.metric("Masivo (sin cuotas)", int(mask_masivo_sin_cuotas.sum()))
+    with col_r2:
+        st.metric("No Clientes Masivo", int(mask_no_cli_mas.sum()))
+        st.metric("Elite", int(mask_elite.sum()))
+    with col_r3:
+        st.metric("Masivo (cuotas)", int(mask_masivo_cuotas.sum()))
+        st.metric("Premium", int(mask_premium.sum()))
 
-    df_exp["CELULAR"] = df_exp["CELULAR"].apply(cel_10)
+    st.divider()
+    st.subheader("📦 Descargas")
 
-    fecha_archivo = datetime.now().strftime("%d-%m")
-    zip_buf = io.BytesIO()
+    st.download_button(
+        "⬇️ Base Credimax LIMPIA FINAL.xlsx",
+        data=df_to_excel_bytes(df, sheet_name="base"),
+        file_name="Base Credimax LIMPIA FINAL.xlsx",
+        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
+    )
 
-    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
-        for nombre, grupo in df_exp.groupby(col_campana, dropna=False):
-            if pd.isna(nombre):
-                continue
-            nombre_archivo = safe_filename(nombre)
-            if not nombre_archivo or nombre_archivo.lower() == 'nan':
-                continue
+    cmp_cols = [
+        "SEGMENTO",
+        "Producto",
+        "Ind_Perfil_Campaña",
+        "CANAL",
+        "TESTEO CUOTA",
+        "Campaña Growth Original",
+        "Campaña Growth",
+        "Coincide (Original vs Reglas)",
+        "Cambio Aplicado (Original -> Final)",
+    ]
 
-            grupo_salida = grupo.drop(columns=[col_campana]).copy()
-            cols = ["CELULAR"] + [c for c in grupo_salida.columns if c != "CELULAR"]
-            grupo_salida = grupo_salida[cols]
+    st.download_button(
+        "⬇️ Base Credimax COMPARACION CAMPANA GROWTH.xlsx",
+        data=df_to_excel_bytes(df_cmp[cmp_cols], sheet_name="comparacion"),
+        file_name="Base Credimax COMPARACION CAMPANA GROWTH.xlsx",
+        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
+    )
 
-            excel_bytes = df_to_excel_bytes(grupo_salida, sheet_name="base")
-            zf.writestr(f"{nombre_archivo}_{fecha_archivo}.xlsx", excel_bytes)
+    if export_por_campana:
+        zip_bytes, columnas_segmentadas = preparar_zip_por_campana(df)
+
+        if zip_bytes:
+            st.download_button(
+                "⬇️ Descargar ZIP por campaña",
+                data=zip_bytes,
+                file_name=f"Campanas_segmentadas_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
+                mime="application/zip",
+            )
+            st.caption(
+                "Columnas en cada archivo segmentado: "
+                + ", ".join(columnas_segmentadas)
+            )
+        else:
+            st.info(
+                "No hay registros con IND_DESEMBOLSO = '0' y campaña válida para generar el ZIP."
+            )
+
+    st.success("✅ Limpieza Credimax completada. Descarga tus archivos.")
+
+
+def run_bankard():
+    st.sidebar.header("1) Sube la base Bankard")
+    base_file = st.sidebar.file_uploader(
+        "Base Bankard (.xlsx)", type=["xlsx"], key="base_bankard"
+    )
 
-    zip_buf.seek(0)
+    st.sidebar.header("2) Exclusiones (opcional)")
+    exclusion_files = st.sidebar.file_uploader(
+        "Archivos de exclusión (.xlsx)",
+        type=["xlsx"],
+        accept_multiple_files=True,
+        key="exclusiones_bankard",
+    )
+    st.sidebar.caption("Se utilizará la columna 'IDENTIFICACION' de cada archivo para excluir cédulas.")
+    st.sidebar.caption(
+        "También puedes dejar archivos .xlsx permanentes en "
+        f"`{EXCLUSIONES_BANKARD_DIR}` para cargarlos automáticamente."
+    )
+
+    (
+        cedulas_persistentes,
+        errores_persistentes,
+        archivos_persistentes,
+    ) = cargar_cedulas_excluir_directorio(EXCLUSIONES_BANKARD_DIR)
+    if cedulas_persistentes:
+        st.sidebar.info(
+            f"{len(cedulas_persistentes)} cédulas serán excluidas desde la carpeta permanente."
+        )
+    if archivos_persistentes:
+        st.sidebar.caption("Archivos permanentes detectados:")
+        for nombre_archivo in sorted(archivos_persistentes):
+            st.sidebar.write(f"• {nombre_archivo}")
+    elif not errores_persistentes:
+        st.sidebar.caption(
+            "No hay archivos permanentes en `data/exclusiones_bankard` todavía."
+        )
+    if errores_persistentes:
+        for msg in errores_persistentes:
+            st.sidebar.warning(f"Exclusión local omitida: {msg}")
+
+    if not base_file:
+        st.info("👆 Sube la base para continuar.")
+        return
+
+    try:
+        df = pd.read_excel(base_file, dtype=str)
+    except Exception as e:
+        st.error(f"No se pudo leer el Excel: {e}")
+        return
+
+    df = limpiar_cupo_bankard(df)
+    memoria = cargar_memoria_correcciones()
+    pendientes = detectar_bins_no_permitidos(df, memoria)
+
+    if pendientes:
+        st.warning(
+            f"Se encontraron **{len(pendientes)}** valores en 'BIN' fuera de la lista permitida."
+        )
+        st.caption(
+            "Opciones permitidas: " + ", ".join(VALORES_BIN_PERMITIDOS)
+        )
+        correcciones_inputs = {}
+        with st.form("correcciones_bin"):
+            st.write("Indica cómo reemplazar cada BIN detectado (dejar vacío para ignorar).")
+            for valor in pendientes:
+                correcciones_inputs[valor] = st.text_input(
+                    f"Nuevo valor para '{valor}'",
+                    value=memoria.get(valor, ""),
+                    key=f"bin_corr_{valor}",
+                )
+            submitted = st.form_submit_button("Guardar correcciones")
+        if submitted:
+            actualizaciones = {
+                origen: nuevo.strip()
+                for origen, nuevo in correcciones_inputs.items()
+                if nuevo.strip()
+            }
+            if actualizaciones:
+                memoria.update(actualizaciones)
+                guardar_memoria_correcciones(memoria)
+                st.success("Correcciones guardadas. Se aplicarán inmediatamente.")
+            else:
+                st.info("No se ingresaron correcciones nuevas.")
+            memoria = cargar_memoria_correcciones()
+
+    df = aplicar_correcciones_bin(df, memoria)
+    df, excluidos_vigencia = filtrar_vigencia_bankard(df)
+    df = limpiar_telefonos_cedulas_bankard(df)
+
+    cedulas_excluir, errores_exclusiones = cargar_cedulas_excluir_uploads(exclusion_files)
+    if cedulas_persistentes:
+        cedulas_excluir.update(cedulas_persistentes)
+    if errores_exclusiones:
+        for msg in errores_exclusiones:
+            st.warning(f"Exclusión omitida: {msg}")
+    total_exclusiones = len(cedulas_excluir)
+    if total_exclusiones:
+        st.caption(
+            "Se aplicaron **" + str(total_exclusiones) + "** cédulas de exclusión (uploads/permanentes)."
+        )
+
+    df = marcar_exclusiones_varios(df, cedulas_excluir)
+    ensure_column_from(df, "TIPO ", sources=["TIPO"], fill_value="")
+
+    total_registros = len(df)
+    excl_si = int((df["exclusion"].astype(str).str.upper() == "SI").sum())
+    excl_no = int((df["exclusion"].astype(str).str.upper() == "NO").sum())
+
+    st.subheader("📋 Resultados Bankard")
+    col_b1, col_b2, col_b3 = st.columns(3)
+    col_b1.metric("Registros totales", total_registros)
+    col_b2.metric("Exclusión = SI", excl_si)
+    col_b3.metric("Exclusión = NO", excl_no)
+
+    if excluidos_vigencia:
+        st.info(
+            f"Se excluyeron {excluidos_vigencia} registros por vigencia vencida o inválida."
+        )
+
+    st.divider()
+    st.subheader("📦 Descargas")
 
     st.download_button(
-        "⬇️ Descargar ZIP por campaña",
-        data=zip_buf,
-        file_name=f"archivos_por_campana_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
-        mime="application/zip",
+        "⬇️ Base Bankard LIMPIA.xlsx",
+        data=df_to_excel_bytes(df, sheet_name="base"),
+        file_name="Base Bankard LIMPIA.xlsx",
+        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
     )
 
-st.success("✅ Listo. Descarga tus archivos.")
+    zip_bytes, columnas_zip = preparar_zip_bankard(df)
+    if zip_bytes:
+        st.download_button(
+            "⬇️ Descargar ZIP por tipo y exclusión",
+            data=zip_bytes,
+            file_name=f"Bankard_segmentado_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
+            mime="application/zip",
+        )
+        st.caption("Columnas en cada archivo segmentado: " + ", ".join(columnas_zip))
+    else:
+        st.info("No hay registros para exportar por tipo y exclusión.")
+
+    st.success("✅ Limpieza Bankard completada. Descarga tus archivos.")
+
+
+# =============================
+# Entrada principal
+# =============================
+modo = st.sidebar.radio(
+    "Selecciona el flujo de limpieza",
+    ("Credimax", "Bankard"),
+    key="modo_limpieza",
+)
+
+if modo == "Credimax":
+    run_credimax()
+else:
+    run_bankard()
 
EOF
)
