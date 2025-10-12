# 🧹 Limpieza Credimax & Bankard

Aplicación Streamlit para normalizar bases de clientes de Credimax y Bankard, validar campos críticos y generar descargas segmentadas listas para uso operativo. Incluye funcionalidades avanzadas como plantillas SMS personalizables, acortamiento de enlaces con Bitly, y sistema inteligente de corrección de BINs.

## 🚀 Características Principales

- **Procesamiento Dual**: Flujos especializados para Credimax y Bankard
- **Validación Inteligente**: Cédulas, celulares, nombres y cupos
- **Segmentación Automática**: Archivos separados por campaña/tipo
- **Plantillas SMS**: Generación automática con variables personalizables
- **Acortamiento de Enlaces**: Integración con Bitly para enlaces profesionales
- **Sistema de Exclusiones**: Gestión consolidada de cédulas a excluir
- **Corrección Inteligente**: Auto-corrección de BINs con aprendizaje automático
- **Exportación Optimizada**: Archivos listos para sistemas de envío masivo

## 📋 Requisitos

### Software
- Python 3.10 o superior
- Streamlit
- Pandas, NumPy, OpenPyXL
- Requests (para Bitly)

### Instalación
```bash
# Clonar repositorio
git clone https://github.com/romebarr/limpieza_credimax.git
cd limpieza_credimax

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
streamlit run app.py
```

La interfaz se abre en `http://localhost:8501` y permite seleccionar el flujo deseado desde la barra lateral.

## 🏦 Flujo Credimax

### Procesamiento de Datos
- **Validación de Cédulas**: Verificación de formato ecuatoriano (10 dígitos)
- **Normalización de Celulares**: Formato estándar de 10 dígitos
- **Limpieza de Nombres**: Formato de nombres propios (Primera Letra Mayúscula)
- **Formateo de Cupos**: Separadores de miles (1,000)
- **Validación de Marcas**: Solo marcas de tarjeta permitidas

### Reglas de Segmentación Automática
La columna `Campaña Growth` se reasigna automáticamente según:
- **Canal**: ONLINE
- **Producto**: No Clientes vs Clientes
- **Segmento**: Afluente (ELITE/PREMIUM) vs Masivo (SILVER/PRESTIGE)
- **Testeo de Cuotas**: SI/NO

### Descargas Disponibles
1. **Base Limpia General**: `Base Credimax LIMPIA FINAL CON SEGMENTO.xlsx`
2. **Comparativo de Campañas**: `Base Credimax COMPARACION CAMPANA GROWTH.xlsx`
3. **ZIP Segmentado por Campaña**: Archivos separados por cada campaña
4. **Plantillas SMS Segmentadas** 📱:
   - Variables: `<#monto#>`, `<#tasa#>`, `<#link#>`
   - Archivos sin encabezados para importación directa
   - Enlaces acortados con Bitly (mkt-bb.com)

## 🏛️ Flujo Bankard

### Sistema de Exclusiones Avanzado
- **Sistema Consolidado**: JSON con 5,776+ cédulas de exclusión
- **Carga desde Carpeta**: Procesa automáticamente archivos en `data/exclusiones_bankard/`
- **Carga Manual**: Subida de archivos individuales
- **Método Legacy**: Compatibilidad con sistema anterior

### Limpiezas Aplicadas
- **Normalización de Cupos**: Extracción de solo números
- **Corrección Inteligente de BINs**: Sistema de aprendizaje automático
- **Filtro por Vigencia**: Exclusión de registros vencidos
- **Normalización de Contactos**: Teléfonos y cédulas a 10 dígitos
- **Limpieza de Nombres**: Formato de nombres propios

### Descargas Disponibles
1. **Base Limpia Completa**: `Bankard_General_{fecha}.xlsx`
2. **ZIP Segmentado**: Por tipo y exclusión (SI/NO)
3. **Plantillas SMS Segmentadas** 📱:
   - Variables: `<#marca#>`, `<#cupo#>`, `<#link#>`
   - Solo registros sin exclusión
   - Cupos formateados con separadores de miles
   - Enlaces acortados con Bitly

## 📱 Plantillas SMS Segmentadas

### Características Generales
- **Acortamiento Automático**: Enlaces acortados con Bitly (dominio mkt-bb.com)
- **Variables Personalizables**: Reemplazo automático de valores específicos
- **Exportación Sin Encabezados**: Archivos listos para importación directa
- **Segmentación Inteligente**: Archivos separados por segmento de negocio

### Credimax SMS
- **Segmentación**: Por campaña (igual que ZIP de datos)
- **Variables**: `<#monto#>`, `<#tasa#>`, `<#link#>`
- **Filtros**: Solo registros con `IND_DESEMBOLSO = "0"` y celulares válidos
- **Archivos**: `SMS_{Campaña}_{fecha}.xlsx` en ZIP `SMS_Credimax_Segmentado_{fecha}.zip`

### Bankard SMS
- **Segmentación**: Por tipo de tarjeta (igual que ZIP de datos)
- **Variables**: `<#marca#>`, `<#cupo#>`, `<#link#>`
- **Filtros**: Solo registros con `exclusion = "NO"` y teléfonos válidos
- **Archivos**: `SMS_Bankard_{Tipo}_{fecha}.xlsx` en ZIP `SMS_Bankard_Segmentado_{fecha}.zip`

### Uso de Plantillas SMS
1. **Activar Funcionalidad**: Checkbox "Generar plantilla SMS" en la barra lateral
2. **Configurar Texto**: Ingresar mensaje con variables personalizables
3. **Definir Enlace**: URL que reemplazará `<#link#>` (se acorta automáticamente)
4. **Descargar**: ZIP con plantillas segmentadas listas para envío masivo

## 🧠 Sistema Inteligente de BINs

### Características
- **Aprendizaje Automático**: Mejora correcciones con el uso
- **Sugerencias Inteligentes**: Algoritmo de similitud (Levenshtein)
- **Memoria Persistente**: Guarda correcciones en `memoria_correcciones_bin.json`
- **Estadísticas de Uso**: Rastrea patrones en `memoria_estadisticas_bin.json`

### Funcionamiento
1. **Detección**: Identifica BINs fuera de la lista permitida
2. **Sugerencias**: Genera opciones basadas en similitud y historial
3. **Auto-corrección**: Aplica correcciones con alta confianza (>80%)
4. **Aprendizaje**: Actualiza estadísticas para futuras sugerencias

## 📁 Gestión de Exclusiones

### Sistema Consolidado
- **Archivo Principal**: `exclusiones_consolidadas.json` (5,776+ cédulas)
- **Actualización Automática**: Procesa archivos en `data/exclusiones_bankard/`
- **Métodos de Carga**:
  - Consolidación desde carpeta
  - Subida de archivos individuales
  - Método legacy (compatibilidad)

### Estructura de Archivos
```
data/exclusiones_bankard/
├── Base de exclusion_0728.xlsx
├── Base Exclusion 0805.xlsx
├── TC_FILTRO_COMUNICA-*.xlsx
└── ... (50+ archivos)
```

## 🔧 Configuración Técnica

### Variables de Entorno
- **Bitly Token**: `d9dad23cd1329e489dcbe9c52cd1770e856c50d5`
- **Dominio Personalizado**: `mkt-bb.com`
- **API Bitly**: `https://api-ssl.bitly.com/v4/shorten`

### Archivos de Configuración
- `memoria_correcciones_bin.json`: Correcciones manuales de BINs
- `memoria_estadisticas_bin.json`: Estadísticas de uso y patrones
- `exclusiones_consolidadas.json`: Base consolidada de exclusiones

## 📊 Arquitectura del Sistema

### Funciones Principales (40 total)
- **Funciones Comunes**: 10 funciones de validación y limpieza
- **Funciones de Utilidades**: 2 funciones para manejo de archivos
- **Funciones Credimax**: 3 funciones específicas
- **Funciones Bankard**: 7 funciones específicas
- **Sistema Inteligente BINs**: 9 funciones de corrección automática
- **Sistema de Exclusiones**: 8 funciones de gestión
- **Utilidades DataFrame**: 1 función de manipulación

### Flujo de Procesamiento
1. **Carga de Datos**: Validación de archivos Excel
2. **Limpieza**: Normalización y validación de campos
3. **Aplicación de Reglas**: Segmentación y correcciones automáticas
4. **Generación de Salidas**: ZIPs segmentados y plantillas SMS
5. **Exportación**: Archivos listos para uso operativo

## 🚀 Despliegue

### Requisitos del Servidor
- Python 3.10+
- 2GB RAM mínimo
- 1GB espacio en disco
- Acceso a internet (para Bitly)

### Variables de Producción
```bash
# Configurar variables de entorno
export BITLY_ACCESS_TOKEN="d9dad23cd1329e489dcbe9c52cd1770e856c50d5"
export BITLY_DOMAIN="mkt-bb.com"
```

## 📚 Documentación Adicional

- **[Lista de Funciones](FUNCIONES.md)**: Documentación completa de todas las funciones
- **[Mapeo de Columnas](mapeo_columnas_bankard.md)**: Especificación de mapeo para Bankard
- **[Ejemplo No Clientes](ejemplo_tipo_no_clientes.md)**: Guía para archivos No Clientes

## 🆘 Soporte

Para dudas, reportes de bugs o solicitudes de nuevas funcionalidades:
- **Equipo**: Marketing Directo - SM Growth Lab
- **Repositorio**: [GitHub](https://github.com/romebarr/limpieza_credimax)
- **Archivo Principal**: `app.py`

## 📝 Changelog

### v2.0.0 (Actual)
- ✅ Plantillas SMS segmentadas
- ✅ Acortamiento de enlaces con Bitly
- ✅ Sistema inteligente de corrección de BINs
- ✅ Gestión consolidada de exclusiones
- ✅ Documentación completa

### v1.0.0 (Inicial)
- ✅ Procesamiento básico Credimax/Bankard
- ✅ Validación y limpieza de datos
- ✅ Segmentación por campaña/tipo
