# Lista de Funciones - Limpieza Credimax & Bankard

## 📋 Funciones Comunes de Validación y Limpieza

| Función | Propósito | Parámetros | Retorna |
|---------|-----------|------------|---------|
| `validar_cedula_10(cedula)` | Valida cédulas ecuatorianas de 10 dígitos | `cedula`: valor a validar | `bool`: True si es válida |
| `normalizar_celular_ec(valor)` | Normaliza celulares ecuatorianos a 10 dígitos | `valor`: número a normalizar | `str`: celular normalizado o NaN |
| `a_nombre_propio(s)` | Convierte texto a formato nombres propios | `s`: texto a convertir | `str`: texto en formato propio |
| `cupo_a_texto_miles_coma(valor)` | Formatea números con separadores de miles | `valor`: número a formatear | `str`: número con comas |
| `strip_accents(s)` | Remueve acentos de texto | `s`: texto a procesar | `str`: texto sin acentos |
| `norm(v)` | Normaliza texto para comparaciones | `v`: texto a normalizar | `str`: texto normalizado |
| `formatear_cuota(valor)` | Formatea valores como cuotas con 2 decimales | `valor`: valor a formatear | `str`: cuota formateada |
| `safe_filename(s)` | Convierte texto en nombre de archivo seguro | `s`: texto a convertir | `str`: nombre seguro |
| `extraer_solo_numeros(valor)` | Extrae solo dígitos de un valor | `valor`: valor a procesar | `int`: número extraído |
| `pad_10_digitos(valor)` | Normaliza valor a exactamente 10 dígitos | `valor`: valor a normalizar | `str`: valor de 10 dígitos |

## 🔗 Funciones de Utilidades

| Función | Propósito | Parámetros | Retorna |
|---------|-----------|------------|---------|
| `acortar_enlace_bitly(url_larga)` | Acorta enlaces usando API de Bitly | `url_larga`: URL original | `str`: URL acortada |
| `df_to_excel_bytes(df, sheet_name, header)` | Convierte DataFrame a bytes Excel | `df`: DataFrame, `sheet_name`: nombre hoja, `header`: incluir encabezados | `bytes`: contenido Excel |

## 🏦 Funciones Específicas Credimax

| Función | Propósito | Parámetros | Retorna |
|---------|-----------|------------|---------|
| `preparar_zip_por_campana(df, col_campana)` | Genera ZIP segmentado por campaña | `df`: DataFrame Credimax, `col_campana`: columna campaña | `tuple`: (bytes_zip, columnas) |
| `generar_plantilla_sms_credimax_segmentada(df, sms_texto, sms_link, col_campana)` | Genera plantillas SMS por campaña | `df`: DataFrame, `sms_texto`: texto SMS, `sms_link`: enlace, `col_campana`: columna campaña | `tuple`: (bytes_zip, archivos) |
| `run_credimax()` | Flujo principal de procesamiento Credimax | Ninguno | `None` |

## 🏛️ Funciones Específicas Bankard

| Función | Propósito | Parámetros | Retorna |
|---------|-----------|------------|---------|
| `limpiar_cupo_bankard(df)` | Limpia columna cupo extrayendo solo números | `df`: DataFrame Bankard | `DataFrame`: DataFrame limpio |
| `filtrar_vigencia_bankard(df)` | Filtra registros por vigencia | `df`: DataFrame Bankard | `tuple`: (df_filtrado, excluidos) |
| `limpiar_telefonos_cedulas_bankard(df)` | Normaliza teléfonos y cédulas a 10 dígitos | `df`: DataFrame Bankard | `DataFrame`: DataFrame normalizado |
| `limpiar_nombres_bankard(df)` | Limpia nombres en formato propio | `df`: DataFrame Bankard | `DataFrame`: DataFrame con nombres limpios |
| `preparar_zip_bankard(df, col_tipo, col_exclusion)` | Genera ZIP segmentado por tipo y exclusión | `df`: DataFrame, `col_tipo`: columna tipo, `col_exclusion`: columna exclusión | `tuple`: (bytes_zip, columnas) |
| `generar_plantilla_sms_bankard_segmentada(df, sms_texto, sms_link, col_tipo, col_exclusion)` | Genera plantillas SMS por tipo | `df`: DataFrame, `sms_texto`: texto SMS, `sms_link`: enlace, `col_tipo`: columna tipo, `col_exclusion`: columna exclusión | `tuple`: (bytes_zip, archivos) |
| `run_bankard()` | Flujo principal de procesamiento Bankard | Ninguno | `None` |

## 🧠 Funciones del Sistema Inteligente de BINs

| Función | Propósito | Parámetros | Retorna |
|---------|-----------|------------|---------|
| `cargar_memoria_correcciones()` | Carga correcciones manuales de BINs | Ninguno | `dict`: memoria de correcciones |
| `cargar_estadisticas_bin()` | Carga estadísticas de uso de BINs | Ninguno | `dict`: estadísticas |
| `guardar_memoria_correcciones(memoria)` | Guarda correcciones de BINs | `memoria`: diccionario de correcciones | `None` |
| `guardar_estadisticas_bin(estadisticas)` | Guarda estadísticas de BINs | `estadisticas`: diccionario de estadísticas | `None` |
| `calcular_similitud_bin(bin_original, bin_candidato)` | Calcula similitud entre BINs | `bin_original`: BIN original, `bin_candidato`: BIN candidato | `float`: similitud (0-1) |
| `generar_sugerencias_inteligentes(bin_problema, memoria_correcciones, estadisticas)` | Genera sugerencias para BINs problemáticos | `bin_problema`: BIN problemático, `memoria_correcciones`: correcciones, `estadisticas`: estadísticas | `list`: lista de sugerencias |
| `actualizar_estadisticas_bin(bin_original, bin_corregido, estadisticas)` | Actualiza estadísticas de uso | `bin_original`: BIN original, `bin_corregido`: BIN corregido, `estadisticas`: estadísticas | `None` |
| `detectar_bins_no_permitidos_inteligente(df, memoria_correcciones, estadisticas)` | Detecta BINs no permitidos con sugerencias | `df`: DataFrame, `memoria_correcciones`: correcciones, `estadisticas`: estadísticas | `tuple`: (bins_problematicos, sugerencias) |
| `aplicar_correcciones_bin(df, memoria_correcciones, estadisticas)` | Aplica correcciones de BINs | `df`: DataFrame, `memoria_correcciones`: correcciones, `estadisticas`: estadísticas | `DataFrame`: DataFrame corregido |

## 📁 Funciones del Sistema de Exclusiones

| Función | Propósito | Parámetros | Retorna |
|---------|-----------|------------|---------|
| `cargar_cedulas_excluir_uploads(files)` | Carga exclusiones desde archivos subidos | `files`: lista de archivos subidos | `tuple`: (set_cedulas, errores) |
| `cargar_exclusiones_consolidadas()` | Carga archivo JSON consolidado de exclusiones | Ninguno | `tuple`: (cedulas_excluidas, estadisticas) |
| `guardar_exclusiones_consolidadas(cedulas_data, estadisticas)` | Guarda exclusiones consolidadas | `cedulas_data`: datos de cédulas, `estadisticas`: estadísticas | `None` |
| `procesar_archivo_exclusiones(archivo_path, cedulas_consolidadas, estadisticas)` | Procesa archivo de exclusiones | `archivo_path`: ruta archivo, `cedulas_consolidadas`: cédulas, `estadisticas`: estadísticas | `tuple`: (success, message) |
| `procesar_archivo_excel_exclusiones(archivo_path, nombre_archivo)` | Procesa archivo Excel de exclusiones | `archivo_path`: ruta archivo, `nombre_archivo`: nombre archivo | `tuple`: (cedulas_set, error_message) |
| `cargar_cedulas_excluir_directorio(path)` | Carga exclusiones desde directorio (legacy) | `path`: ruta del directorio | `tuple`: (set_cedulas, errores, archivos) |
| `consolidar_exclusiones_desde_directorio()` | Consolida archivos Excel en JSON | Ninguno | `tuple`: (success, message) |
| `marcar_exclusiones_varios(df, cedulas_excluir)` | Marca registros como excluidos | `df`: DataFrame, `cedulas_excluir`: set de cédulas | `DataFrame`: DataFrame con exclusiones marcadas |

## 🔧 Funciones de Utilidades de DataFrame

| Función | Propósito | Parámetros | Retorna |
|---------|-----------|------------|---------|
| `ensure_column_from(df, target, sources, fill_value)` | Asegura que existe una columna objetivo | `df`: DataFrame, `target`: columna objetivo, `sources`: columnas fuente, `fill_value`: valor por defecto | `str`: nombre de columna |

## 📊 Resumen por Categorías

- **Funciones Comunes**: 10 funciones para validación y limpieza de datos
- **Funciones de Utilidades**: 2 funciones para manejo de archivos y enlaces
- **Funciones Credimax**: 3 funciones específicas para procesamiento Credimax
- **Funciones Bankard**: 7 funciones específicas para procesamiento Bankard
- **Sistema Inteligente BINs**: 9 funciones para corrección automática de BINs
- **Sistema de Exclusiones**: 8 funciones para manejo de exclusiones
- **Utilidades DataFrame**: 1 función para manipulación de columnas

**Total**: 40 funciones organizadas en 7 categorías principales
