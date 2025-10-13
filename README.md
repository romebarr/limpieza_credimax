# 🧹 Limpieza Credimax & Bankard

Aplicación Streamlit modular para normalizar bases de clientes de Credimax y Bankard, validar campos críticos y generar descargas segmentadas listas para uso operativo. Incluye funcionalidades avanzadas como plantillas SMS consolidadas, acortamiento de enlaces con Bitly, sistema inteligente de corrección de BINs, y asignación automática de campañas.

---

## 🚀 Características Principales

### 🎯 Funcionalidades Core
- **✅ Procesamiento Dual**: Flujos especializados para Credimax y Bankard
- **✅ Validación Inteligente**: Cédulas, celulares, nombres y cupos
- **✅ Segmentación Automática**: Archivos separados por campaña/tipo
- **✅ Plantillas SMS Consolidadas**: Un solo archivo con múltiples segmentos
- **✅ Selector de Segmentos**: Control total sobre qué segmentos incluir en SMS
- **✅ Acortamiento de Enlaces**: Integración con Bitly para enlaces profesionales
- **✅ Sistema de Exclusiones**: Gestión consolidada de cédulas a excluir
- **✅ Corrección Inteligente de BINs**: Auto-corrección con memoria persistente
- **✅ Asignación Automática de Campañas**: Reglas de negocio para Credimax
- **✅ Arquitectura Modular**: Código organizado en módulos para fácil mantenimiento

### 🏗️ Arquitectura Modular

```
limpieza_credimax/
├── app.py                              # Aplicación principal
├── modules/                            # Módulos organizados por funcionalidad
│   ├── common/                         # Funciones comunes
│   │   ├── validators.py               # Validaciones (cédulas, celulares)
│   │   ├── formatters.py               # Formateadores (nombres, cupos, fechas)
│   │   └── utils.py                    # Utilidades (Excel, archivos)
│   ├── integrations/                   # Integraciones externas
│   │   └── bitly.py                    # Acortamiento de enlaces
│   ├── credimax/                       # Lógica específica de Credimax
│   │   ├── processor.py                # Procesamiento y ZIP segmentado
│   │   ├── sms_generator.py            # Generación de plantillas SMS
│   │   └── campaign_assigner.py        # Asignación automática de campañas
│   ├── bankard/                        # Lógica específica de Bankard
│   │   ├── processor.py                # Procesamiento y ZIP segmentado
│   │   ├── cleaner.py                  # Limpieza de datos
│   │   ├── exclusions.py               # Gestión de exclusiones
│   │   ├── bin_corrector.py            # Sistema inteligente de BINs
│   │   ├── sms_generator.py            # Generación de plantillas SMS
│   │   └── column_detector.py          # Detección automática de columnas
│   └── ui/                             # Componentes de interfaz
│       ├── main_ui.py                  # UI principal y layout
│       ├── credimax_ui.py              # UI específica de Credimax
│       └── bankard_ui.py               # UI específica de Bankard
├── data/                               # Datos y configuraciones
│   └── exclusiones_bankard/            # Archivos de exclusión (50+)
├── memoria_correcciones_bin.json       # Memoria de correcciones de BINs
├── memoria_estadisticas_bin.json       # Estadísticas de uso de BINs
├── exclusiones_consolidadas.json       # Base consolidada de exclusiones
├── requirements.txt                    # Dependencias de Python
├── README.md                           # Esta documentación
└── FUNCIONES.md                        # Documentación de funciones
```

---

## 📋 Requisitos

### Software Necesario
- **Python**: 3.10 o superior
- **Streamlit**: Framework web
- **Pandas**: Manipulación de datos
- **NumPy**: Operaciones numéricas
- **OpenPyXL**: Lectura/escritura de Excel
- **Requests**: Llamadas API (Bitly)

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/romebarr/limpieza_credimax.git
cd limpieza_credimax

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar aplicación
streamlit run app.py
```

La interfaz se abre en `http://localhost:8501` y permite seleccionar el flujo deseado desde la barra lateral.

---

## 🏦 Flujo Credimax

### 📊 Procesamiento de Datos

#### Validaciones Aplicadas
- **✅ Cédulas**: Verificación de formato ecuatoriano (10 dígitos)
- **✅ Celulares**: Normalización a formato estándar (10 dígitos)
- **✅ Nombres**: Formato de nombres propios (Primera Letra Mayúscula)
- **✅ Cupos**: Separadores de miles con comas (1,000)
- **✅ Tasas**: Limpieza de símbolos especiales (%)

#### Flujo de Procesamiento
```
1. Carga de archivo Excel
   ↓
2. Validación y limpieza básica
   ↓
3. Asignación automática de campañas
   ↓
4. Generación de base limpia
   ↓
5. Generación de ZIP segmentado
   ↓
6. Selector de segmentos para SMS
   ↓
7. Generación de plantilla SMS consolidada
```

### 🎯 Asignación Automática de Campañas

La columna `Campaña Growth` se reasigna **automáticamente** según reglas de negocio:

#### Reglas de Asignación

| Condiciones | Campaña Asignada |
|-------------|------------------|
| **CANAL = ONLINE** + **Producto = No Clientes** + **Segmento = ELITE/PREMIUM** | `Credimax Online No Clientes Afluente` |
| **CANAL = ONLINE** + **Producto = No Clientes** + **Segmento = SILVER/PRESTIGE** | `Credimax Online No Clientes Masivo` |
| **CANAL = ONLINE** + **Segmento = ELITE** | `Credimax Online Elite` |
| **CANAL = ONLINE** + **Segmento = PREMIUM** | `Credimax Online Premium` |
| **CANAL = ONLINE** + **Segmento = SILVER/PRESTIGE** + **TESTEO CUOTA = SI** | `Credimax Online Masivo Cuotas` |
| **CANAL = ONLINE** + **Segmento = SILVER/PRESTIGE** + **TESTEO CUOTA ≠ SI** | `Credimax Online Masivo` |

#### Características
- **Reescritura**: Si ya existen valores en `Campaña Growth`, se reescriben con los nuevos
- **Comparativo**: Se genera archivo de comparación mostrando cambios aplicados
- **Estadísticas**: Dashboard con distribución de registros por campaña
- **Validación**: Verifica columnas necesarias: `CANAL`, `Producto`, `SEGMENTO`, `TESTEO CUOTA`

### 📥 Descargas Disponibles

#### 1. Base Limpia General
```
📄 Base_Credimax_LIMPIA_20251012_1430.xlsx
- Todos los registros procesados
- Validaciones aplicadas
- Campañas asignadas
```

#### 2. Comparativo de Campañas
```
📄 Base_Credimax_COMPARACION_CAMPANA_GROWTH_20251012.xlsx
Columnas:
- CEDULA
- Campaña Growth Original
- Campaña Growth (nueva)
- Cambio Aplicado (TRUE/FALSE)
```

#### 3. ZIP Segmentado por Campaña
```
📦 Credimax_Segmentado_20251012.zip
├── Credimax_Credimax Online Elite_20251012.xlsx
├── Credimax_Credimax Online Premium_20251012.xlsx
├── Credimax_Credimax Online Masivo_20251012.xlsx
├── Credimax_Credimax Online Masivo Cuotas_20251012.xlsx
├── Credimax_Credimax Online No Clientes Afluente_20251012.xlsx
└── Credimax_Credimax Online No Clientes Masivo_20251012.xlsx

Columnas exportadas:
- primer_nombre_credimax
- correo
- monto_credito_aprob
- cuota_credimax
- Tasa_Credito_Aprob
- Cupo_Aprobado_OB_BK
- Marca_BK_OB
- CELULAR
- Campaña Growth
```

#### 4. Plantilla SMS Consolidada 📱
```
📄 Plantilla_SMS_Credimax_20251012_1430.xlsx
- UN SOLO archivo con todos los segmentos seleccionados
- Sin encabezados (listo para importación)
- Variables reemplazadas con valores reales
- Enlaces acortados con Bitly
```

### 📱 Sistema de Plantillas SMS - Credimax

#### Variables Disponibles
- `<#monto#>` → Valor de columna `CUPO` (con separadores de miles)
- `<#tasa#>` → Valor de columna `Tasa` (sin símbolo %)
- `<#link#>` → Enlace acortado con Bitly (dominio mkt-bb.com)

#### Ejemplo de Uso
```
Texto ingresado:
En Banco Bolivariano, tienes un prestamo aprobado de $<#monto#> con una tasa del <#tasa#>% por tiempo limitado. Solicitalo aqui ahora: <#link#>

Enlace ingresado:
https://www.bancabolivariano.com/credito-consumo

Resultado en plantilla:
0987654321 | En Banco Bolivariano, tienes un prestamo aprobado de $5,000 con una tasa del 12.5% por tiempo limitado. Solicitalo aqui ahora: https://mkt-bb.com/abc123
```

#### Selector de Segmentos
```
Usuario puede seleccionar qué campañas incluir:
✅ Credimax Online Elite          (1,200 registros)
✅ Credimax Online Masivo         (1,500 registros)
✅ Credimax Online Masivo Cuotas  (842 registros)
❌ No Clientes Afluente           (DESELECCIONADO)
❌ No Clientes Masivo             (DESELECCIONADO)

Resultado: 1 archivo con 3,542 registros (Elite + Masivo + Masivo Cuotas)
```

---

## 🏛️ Flujo Bankard

### 📊 Procesamiento de Datos

#### Validaciones y Limpiezas
- **✅ Normalización de Cupos**: Extracción de solo números + formato con comas
- **✅ Corrección Inteligente de BINs**: Sistema con memoria y aprendizaje
- **✅ Filtro por Vigencia**: Exclusión de registros vencidos
- **✅ Normalización de Contactos**: Teléfonos y cédulas a 10 dígitos
- **✅ Limpieza de Nombres**: Formato de nombres propios
- **✅ Detección Automática de Columnas**: Identifica `TIPO` y `exclusion`

#### Flujo de Procesamiento
```
1. Carga de archivo Excel
   ↓
2. Detección automática de columnas TIPO y exclusion
   ↓
3. Carga de exclusiones consolidadas
   ↓
4. Limpieza básica (cupos, teléfonos, nombres)
   ↓
5. Filtro por vigencia
   ↓
6. Marcado de exclusiones
   ↓
7. Corrección interactiva de BINs
   ↓
8. Generación de base limpia
   ↓
9. Generación de ZIP segmentado
   ↓
10. Selector de segmentos para SMS
   ↓
11. Generación de plantilla SMS consolidada
```

### 🚫 Sistema de Exclusiones Avanzado

#### Fuentes de Exclusión
1. **Sistema Consolidado**: `exclusiones_consolidadas.json` (5,776+ cédulas)
2. **Carpeta de Datos**: Procesamiento automático de `data/exclusiones_bankard/`
3. **Carga Manual**: Subida de archivos individuales en la interfaz
4. **Método Legacy**: Compatibilidad con sistema anterior

#### Estructura de Archivos
```
data/exclusiones_bankard/
├── Base de exclusion_0728.xlsx
├── Base Exclusion 0805.xlsx
├── TC_FILTRO_COMUNICA_2024_*.xlsx
├── Base Exclusion con Respuesta por Mora_*.xlsx
└── ... (50+ archivos)
```

#### Estadísticas de Exclusión
```
📊 Dashboard en la interfaz:
- Total de cédulas excluidas: 5,776
- Registros marcados para exclusión: 2,340
- Registros válidos (NO excluidos): 8,660
```

### 🧠 Sistema Inteligente de Corrección de BINs

#### Características Principales
- **✅ Detección Automática**: Identifica BINs fuera de la lista permitida
- **✅ Sugerencias Inteligentes**: Algoritmo de similitud (SequenceMatcher)
- **✅ Interfaz Interactiva**: Usuario confirma o rechaza correcciones
- **✅ Memoria Persistente**: Guarda correcciones en JSON
- **✅ Estadísticas de Uso**: Rastrea patrones y frecuencias
- **✅ Auto-corrección Agresiva**: Aplica correcciones de alta confianza automáticamente

#### BINs Permitidos
```python
VALORES_BIN_PERMITIDOS = {
    "Visa Oro", "Visa Clásica", "Visa Signature", "Visa Infinite",
    "Visa Platinum", "Mastercard Oro", "Mastercard Clásica",
    "Mastercard Black"
}
```

#### Sistema de Prioridades de Corrección
```
Prioridad 1: Memoria de correcciones confirmadas
   ↓
Prioridad 2: Valores ya permitidos (sin cambios)
   ↓
Prioridad 3: Sugerencias con confianza > 60%
   ↓
Prioridad 4: Normalización de texto (.title())
   ↓
Prioridad 5: Corrección automática agresiva (> 50%)
   ↓
Prioridad 6: Mapeo básico de variaciones comunes
   ↓
Sin corrección: Marca como "BIN NO VÁLIDO"
```

#### Mapeo Básico de Variaciones
```
"visa gold" → "Visa Oro"
"visa oro" → "Visa Oro"
"visa oro bk plus" → "Visa Oro"
"visa platinum" → "Visa Platinum"
"visa platinum bk plus" → "Visa Platinum"
"visa signature" → "Visa Signature"
"visa infinite" → "Visa Infinite"
"visa clásica" → "Visa Clásica"
"visa clasica" → "Visa Clásica"
"visa clasica bk plus" → "Visa Clásica"
"mastercard black" → "Mastercard Black"
"mastercard classic" → "Mastercard Clásica"
"mastercard clásica" → "Mastercard Clásica"
"mastercard oro" → "Mastercard Oro"
```

#### Interfaz de Corrección
```
⚠️ Se encontraron 5 BINs no permitidos

💾 Estado de memoria de correcciones:
- Correcciones guardadas: 12
- Última actualización: 2025-10-12 14:30

🔧 Correcciones sugeridas:
┌─────────────────┬─────────────────┬────────────┐
│ BIN Original    │ Sugerencia      │ Confianza  │
├─────────────────┼─────────────────┼────────────┤
│ Visa Gold       │ Visa Oro        │ 85%        │
│ Visa Platino    │ Visa Platinum   │ 80%        │
│ MC Black        │ Mastercard Black│ 75%        │
└─────────────────┴─────────────────┴────────────┘

[✅ Aceptar] [✏️ Corregir Manualmente] [❌ Mantener Original]

💾 Guardar correcciones en memoria
```

### 📥 Descargas Disponibles

#### 1. Base Limpia Completa
```
📄 Bankard_General_20251012.xlsx
- Todos los registros procesados
- Validaciones aplicadas
- Exclusiones marcadas
- BINs corregidos
```

#### 2. ZIP Segmentado por Tipo
```
📦 Bankard_Segmentado_20251012.zip
├── Bankard_Visa_Oro_20251012.xlsx
├── Bankard_Visa_Platinum_20251012.xlsx
├── Bankard_Visa_Clásica_20251012.xlsx
├── Bankard_Visa_Signature_20251012.xlsx
├── Bankard_Mastercard_Black_20251012.xlsx
└── Bankard_No_Clientes_20251012.xlsx  (cuando no hay columna TIPO)

Columnas exportadas (solo registros NO excluidos):
- primer_nombre_bankard
- Cupo_Aprobado_OB_BK (con formato: 3,000)
- Marca_BK_OB
- correo
- telefono
```

#### 3. Plantilla SMS Consolidada 📱
```
📄 Plantilla_SMS_Bankard_20251012_1430.xlsx
- UN SOLO archivo con todos los segmentos seleccionados
- Solo registros sin exclusión
- Sin encabezados (listo para importación)
- Variables reemplazadas con valores reales
- Cupos formateados con separadores de miles
- Enlaces acortados con Bitly
```

### 📱 Sistema de Plantillas SMS - Bankard

#### Variables Disponibles
- `<#marca#>` → Valor de columna `BIN` (ej: "Visa Oro")
- `<#cupo#>` → Valor de columna `cupo` (con separadores de miles)
- `<#link#>` → Enlace acortado con Bitly (dominio mkt-bb.com)

#### Ejemplo de Uso
```
Texto ingresado:
Felicidades! Tu Bankard <#marca#> ha sido aprobada con un cupo de $<#cupo#>. Obtenla en minutos aqui: <#link#>

Enlace ingresado:
https://www.bancabolivariano.com/tarjeta-credito

Resultado en plantilla:
0987654321 | Felicidades! Tu Bankard Visa Oro ha sido aprobada con un cupo de $4,500. Obtenla en minutos aqui: https://mkt-bb.com/xyz789
```

#### Selector de Segmentos
```
Usuario puede seleccionar qué tipos incluir:
✅ Visa Oro           (1,300 registros)
✅ Visa Platinum      (800 registros)
❌ Visa Clásica       (DESELECCIONADO)
❌ Mastercard Black   (DESELECCIONADO)
❌ No Clientes        (DESELECCIONADO)

Resultado: 1 archivo con 2,100 registros (Visa Oro + Visa Platinum)
```

---

## 📱 Sistema de Plantillas SMS Consolidadas

### 🎯 Características Generales

#### Innovación: Un Solo Archivo
**Antes:** Múltiples archivos (uno por segmento) en un ZIP
**Ahora:** UN SOLO archivo consolidado con todos los segmentos seleccionados

#### Ventajas
- ✅ **Simplicidad**: Un archivo para importar a sistemas de envío
- ✅ **Eficiencia**: No necesitas descomprimir ZIP ni seleccionar archivos
- ✅ **Visibilidad**: Desglose claro de registros por segmento
- ✅ **Control**: Sabes exactamente cuántos SMS se enviarán
- ✅ **Flexibilidad**: Puedes cambiar selección y regenerar rápidamente

#### Formato de Archivo
```
┌───────────────┬─────────────────────────────────────────┐
│ CELULAR/TEL   │ MENSAJE PERSONALIZADO                   │
├───────────────┼─────────────────────────────────────────┤
│ 0987654321    │ En Banco Bolivariano, tienes un pres... │
│ 0998765432    │ En Banco Bolivariano, tienes un pres... │
│ 0912345678    │ Felicidades! Tu Bankard Visa Oro ha ... │
│ ...           │ ...                                     │
└───────────────┴─────────────────────────────────────────┘

✅ Sin encabezados (header=False)
✅ Columna 1: Número de contacto
✅ Columna 2: Mensaje personalizado con variables reemplazadas
✅ Formato Excel (.xlsx)
```

### 🔗 Integración con Bitly

#### Configuración
- **Token de Acceso**: `d9dad23cd1329e489dcbe9c52cd1770e856c50d5`
- **Dominio Personalizado**: `mkt-bb.com`
- **API Endpoint**: `https://api-ssl.bitly.com/v4/shorten`

#### Funcionamiento
```python
# Enlace original
https://www.bancabolivariano.com/credito-consumo?utm_source=sms&utm_campaign=elite

# Enlace acortado (Bitly)
https://mkt-bb.com/abc123

# Se reemplaza automáticamente en todos los mensajes
```

#### Beneficios
- **✅ Enlaces Cortos**: Ahorran caracteres en SMS
- **✅ Dominio Personalizado**: Mayor confianza y branding
- **✅ Rastreo**: Bitly proporciona estadísticas de clics
- **✅ Profesional**: Aspecto más limpio y profesional

### 🎛️ Selector de Segmentos Interactivo

#### Flujo de Usuario
```
1. Procesamiento completo de datos
   ↓
2. Generación de archivos segmentados
   ↓
3. Visualización de estadísticas
   ↓
4. Aparece selector de segmentos para SMS
   ↓
5. Usuario selecciona segmentos deseados
   ↓
6. Clic en "🚀 Generar Plantilla SMS"
   ↓
7. Descarga de archivo consolidado único
```

#### Interfaz
```
┌─────────────────────────────────────────────┐
│ 📱 Generación de Plantillas SMS             │
├─────────────────────────────────────────────┤
│ ℹ️ Selecciona los segmentos que deseas      │
│    incluir en las plantillas SMS            │
│                                             │
│ Segmentos para SMS:                         │
│ ┌─────────────────────────────────────────┐ │
│ │ ☑ Credimax Online Elite                 │ │
│ │ ☑ Credimax Online Masivo                │ │
│ │ ☑ Credimax Online Masivo Cuotas         │ │
│ │ ☐ Credimax Online No Clientes Afluente  │ │
│ │ ☐ Credimax Online No Clientes Masivo    │ │
│ │ ☐ Credimax Online Premium               │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ [🚀 Generar Plantilla SMS]                  │
│                                             │
│ ✅ Se generó plantilla SMS con 3,542        │
│    registros                                │
│                                             │
│ 📋 Segmentos incluidos en la plantilla ▼    │
│    • Credimax Online Elite: 1,200 registros │
│    • Credimax Online Masivo: 1,500 registros│
│    • Credimax Online Masivo Cuotas: 842...  │
│                                             │
│ [⬇️ Descargar Plantilla SMS]                │
└─────────────────────────────────────────────┘
```

---

## 🔧 Configuración Técnica

### 📦 Dependencias (requirements.txt)
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
requests>=2.31.0
```

### 🌐 Variables de Entorno
```bash
# Bitly Configuration
BITLY_ACCESS_TOKEN="d9dad23cd1329e489dcbe9c52cd1770e856c50d5"
BITLY_DOMAIN="mkt-bb.com"
BITLY_API_URL="https://api-ssl.bitly.com/v4/shorten"
```

### 📁 Archivos de Configuración

#### memoria_correcciones_bin.json
```json
{
  "Visa Gold": "Visa Oro",
  "Visa Platino": "Visa Platinum",
  "MC Black": "Mastercard Black",
  ...
}
```

#### memoria_estadisticas_bin.json
```json
{
  "Visa Gold": {
    "count": 45,
    "ultima_vez": "2025-10-12",
    "correccion_mas_comun": "Visa Oro"
  },
  ...
}
```

#### exclusiones_consolidadas.json
```json
{
  "cedulas_excluir": [
    "1234567890",
    "0987654321",
    ...
  ],
  "fecha_actualizacion": "2025-10-12",
  "total_cedulas": 5776,
  "fuentes": [
    "Base de exclusion_0728.xlsx",
    "TC_FILTRO_COMUNICA_2024_08_21.xlsx",
    ...
  ]
}
```

---

## 📊 Arquitectura y Módulos

### 🏗️ Estructura de Módulos

#### modules/common/ - Funciones Comunes
```python
validators.py
├── validar_cedula_10()          # Validación de cédulas ecuatorianas
└── normalizar_celular_ec()      # Normalización de celulares

formatters.py
├── a_nombre_propio()            # Formato de nombres propios
├── cupo_a_texto_miles_coma()    # Formato de cupos con comas
├── formatear_cuota()            # Formato de cuotas
├── strip_accents()              # Eliminar acentos
├── norm()                       # Normalización de texto
└── safe_filename()              # Nombres de archivo seguros

utils.py
├── df_to_excel_bytes()          # DataFrame a bytes Excel
├── pad_10_digitos()             # Padding de dígitos
├── ensure_column_from()         # Asegurar columna existe
└── procesar_archivo_excel_exclusiones()  # Procesar Excel
```

#### modules/integrations/ - Integraciones
```python
bitly.py
└── acortar_enlace_bitly()       # Acortamiento de enlaces
```

#### modules/credimax/ - Lógica Credimax
```python
processor.py
└── preparar_zip_por_campana()   # ZIP segmentado

sms_generator.py
├── generar_plantilla_sms_credimax_segmentada()     # SMS por segmento
└── generar_plantilla_sms_credimax_consolidada()    # SMS consolidado

campaign_assigner.py
├── asignar_campanas_automaticamente()  # Asignación de campañas
└── mostrar_estadisticas_campanas()     # Estadísticas UI
```

#### modules/bankard/ - Lógica Bankard
```python
processor.py
└── preparar_zip_bankard()       # ZIP segmentado

cleaner.py
├── limpiar_cupo_bankard()       # Limpieza de cupos
├── filtrar_vigencia_bankard()   # Filtro por vigencia
├── limpiar_telefonos_cedulas_bankard()  # Limpieza de contactos
└── limpiar_nombres_bankard()    # Limpieza de nombres

exclusions.py
├── cargar_cedulas_excluir_uploads()         # Carga desde uploads
├── cargar_exclusiones_consolidadas()        # Carga desde JSON
├── guardar_exclusiones_consolidadas()       # Guardar a JSON
├── procesar_archivo_exclusiones()           # Procesar un archivo
├── cargar_cedulas_excluir_directorio()      # Carga desde carpeta
├── consolidar_exclusiones_desde_directorio() # Consolidar múltiples
└── marcar_exclusiones_varios()              # Marcar en DataFrame

bin_corrector.py
├── cargar_memoria_correcciones()            # Cargar JSON correcciones
├── guardar_memoria_correcciones()           # Guardar JSON correcciones
├── cargar_estadisticas_bin()                # Cargar estadísticas
├── guardar_estadisticas_bin()               # Guardar estadísticas
├── calcular_similitud_bin()                 # Similitud entre textos
├── detectar_bins_no_permitidos_inteligente() # Detectar BINs problemáticos
├── aplicar_correcciones_bin()               # Aplicar correcciones
├── mostrar_sugerencias_interactivas_bin()   # UI de correcciones
└── mostrar_estado_memoria_bin()             # UI estado de memoria

sms_generator.py
├── generar_plantilla_sms_bankard_segmentada()   # SMS por segmento
└── generar_plantilla_sms_bankard_consolidada()  # SMS consolidado

column_detector.py
└── detectar_columnas_bankard()  # Detección automática de columnas
```

#### modules/ui/ - Componentes UI
```python
main_ui.py
├── configurar_pagina()          # Configuración de página
├── mostrar_header()             # Header principal
├── mostrar_selector_flujo()     # Selector Credimax/Bankard
├── mostrar_info_flujo()         # Información del flujo
├── mostrar_uploader_archivo()   # Uploader de archivos
├── mostrar_sidebar_info()       # Info en sidebar
├── limpiar_cache()              # Limpiar caché
└── mostrar_footer()             # Footer

credimax_ui.py
├── mostrar_sidebar_credimax()   # Sidebar Credimax
├── mostrar_resultados_credimax() # Resultados
├── mostrar_downloads_credimax()  # Descargas
└── mostrar_validaciones_credimax() # Validaciones

bankard_ui.py
├── mostrar_sidebar_bankard()    # Sidebar Bankard
├── mostrar_resultados_bankard() # Resultados
├── mostrar_downloads_bankard()  # Descargas
└── mostrar_validaciones_bankard() # Validaciones
```

### 📈 Flujo de Datos

```
┌──────────────────────────────────────────────┐
│          CARGA DE ARCHIVO                    │
└────────────┬─────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│      DETECCIÓN Y VALIDACIÓN                  │
│  • Detección automática de columnas         │
│  • Validación de estructura                  │
│  • Carga de configuraciones                  │
└────────────┬─────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│         LIMPIEZA DE DATOS                    │
│  • Normalización de campos                   │
│  • Validación de cédulas/celulares          │
│  • Formato de cupos y nombres               │
└────────────┬─────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│      PROCESAMIENTO ESPECÍFICO                │
│  Credimax:                                   │
│    • Asignación de campañas                 │
│  Bankard:                                    │
│    • Aplicación de exclusiones              │
│    • Corrección de BINs                     │
│    • Filtro por vigencia                    │
└────────────┬─────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│        GENERACIÓN DE SALIDAS                 │
│  • Base limpia general                       │
│  • ZIP segmentado por campaña/tipo          │
│  • Archivos de comparación                  │
└────────────┬─────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│      SELECTOR DE SEGMENTOS SMS               │
│  • Usuario selecciona segmentos             │
│  • Filtrado de DataFrame                    │
└────────────┬─────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│    GENERACIÓN DE PLANTILLA SMS               │
│  • Acortamiento de enlace (Bitly)           │
│  • Reemplazo de variables                   │
│  • Consolidación en un solo archivo         │
│  • Exportación sin encabezados              │
└──────────────────────────────────────────────┘
```

---

## 🚀 Guía de Uso

### 📖 Paso a Paso - Credimax

1. **Iniciar Aplicación**
   ```bash
   streamlit run app.py
   ```

2. **Seleccionar Flujo**
   - Elegir "Credimax" en la barra lateral

3. **Configurar Opciones**
   - ✅ Marcar "Exportar ZIP segmentado"
   - ✅ Marcar "Generar plantilla SMS"
   - Ingresar texto del SMS con variables
   - Ingresar enlace a acortar

4. **Subir Archivo**
   - Cargar archivo Excel de Credimax
   - Esperar validación automática

5. **Revisar Procesamiento**
   - Ver estadísticas de campañas asignadas
   - Revisar distribución de registros
   - Verificar comparativo de cambios

6. **Descargar Archivos**
   - Descargar base limpia general
   - Descargar comparativo de campañas
   - Descargar ZIP segmentado

7. **Generar SMS**
   - Seleccionar segmentos deseados en el selector
   - Clic en "🚀 Generar Plantilla SMS"
   - Revisar desglose de registros por segmento
   - Descargar archivo único consolidado

### 📖 Paso a Paso - Bankard

1. **Iniciar Aplicación**
   ```bash
   streamlit run app.py
   ```

2. **Seleccionar Flujo**
   - Elegir "Bankard" en la barra lateral

3. **Configurar Exclusiones**
   - Opción 1: Consolidar desde carpeta `data/exclusiones_bankard/`
   - Opción 2: Subir archivos individuales
   - Opción 3: Usar método legacy

4. **Configurar Opciones**
   - ✅ Marcar "Exportar ZIP segmentado"
   - ✅ Marcar "Generar plantilla SMS"
   - Ingresar texto del SMS con variables
   - Ingresar enlace a acortar

5. **Subir Archivo**
   - Cargar archivo Excel de Bankard
   - Esperar detección automática de columnas

6. **Corregir BINs**
   - Revisar BINs problemáticos detectados
   - Ver sugerencias automáticas
   - Aceptar o corregir manualmente
   - Guardar correcciones en memoria

7. **Revisar Estadísticas**
   - Ver distribución de BINs
   - Verificar exclusiones aplicadas
   - Revisar registros por vigencia

8. **Descargar Archivos**
   - Descargar base limpia general
   - Descargar ZIP segmentado

9. **Generar SMS**
   - Seleccionar tipos de tarjeta deseados
   - Clic en "🚀 Generar Plantilla SMS"
   - Revisar desglose de registros por tipo
   - Descargar archivo único consolidado

---

## 🆘 Solución de Problemas

### Error: "ModuleNotFoundError"
```bash
# Solución: Instalar dependencias
pip install -r requirements.txt
```

### Error: "Bitly API failed"
```bash
# Verificar conexión a internet
# Verificar token de acceso en bitly.py
# Nota: Si Bitly falla, devuelve el enlace original
```

### Error: "KeyError: 'columna'"
```bash
# Archivo no tiene las columnas esperadas
# Verificar que el archivo corresponde al flujo seleccionado
# Credimax: Requiere CEDULA, CELULAR, CUPO, etc.
# Bankard: Detección automática de TIPO y exclusion
```

### Archivo de Bankard sin columna TIPO
```bash
# Es normal: Significa que es archivo "No Clientes"
# Se genera automáticamente: Bankard_No_Clientes_20251012.xlsx
```

### BINs siguen apareciendo como problemáticos
```bash
# Asegurarse de hacer clic en "💾 Guardar correcciones en memoria"
# Verificar que existe memoria_correcciones_bin.json
# Revisar permisos de escritura del archivo
```

---

## 📚 Documentación Adicional

- **[FUNCIONES.md](FUNCIONES.md)**: Documentación completa de todas las funciones (40+)
- **[mapeo_columnas_bankard.md](mapeo_columnas_bankard.md)**: Especificación de mapeo de columnas
- **[ejemplo_tipo_no_clientes.md](ejemplo_tipo_no_clientes.md)**: Guía para archivos No Clientes

---

## 👥 Equipo y Soporte

### Información del Proyecto
- **Nombre**: Limpieza Credimax & Bankard
- **Versión**: 2.0.0
- **Equipo**: SM Growth Lab - Marketing Directo
- **Última Actualización**: Octubre 2025

### Repositorio
- **GitHub**: [romebarr/limpieza_credimax](https://github.com/romebarr/limpieza_credimax)
- **Archivo Principal**: `app.py`
- **Documentación**: `README.md` (este archivo)

### Contacto
Para dudas, reportes de bugs o solicitudes de nuevas funcionalidades, contactar al equipo de SM Growth Lab.

---

## 📝 Changelog

### v2.0.0 (Octubre 2025) - Actual
- ✅ **Plantillas SMS Consolidadas**: Un solo archivo con múltiples segmentos
- ✅ **Selector de Segmentos**: Control total sobre qué incluir en SMS
- ✅ **Asignación Automática de Campañas**: Credimax con reglas de negocio
- ✅ **Sistema Inteligente de BINs**: Memoria persistente y aprendizaje
- ✅ **Detección Automática de Columnas**: Bankard detecta TIPO y exclusion
- ✅ **Arquitectura Modular**: Código organizado en módulos
- ✅ **Acortamiento con Bitly**: Enlaces profesionales (mkt-bb.com)
- ✅ **Gestión Consolidada de Exclusiones**: Sistema JSON con 5,776+ cédulas
- ✅ **Formato de Cupos**: Separadores de miles en todas las exportaciones
- ✅ **Documentación Completa**: README detallado y FUNCIONES.md

### v1.0.0 (2024) - Inicial
- ✅ Procesamiento básico Credimax/Bankard
- ✅ Validación y limpieza de datos
- ✅ Segmentación por campaña/tipo
- ✅ Exportación de archivos Excel

---

## 📄 Licencia

Este proyecto es de uso interno del equipo SM Growth Lab - Marketing Directo.

---

## 🙏 Agradecimientos

Desarrollado con ❤️ por el equipo de **SM Growth Lab**.

---

**Fin del README** 📚
