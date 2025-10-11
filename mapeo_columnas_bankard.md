# Mapeo de Columnas - Bankard

## 📋 Columnas Exportadas

Los archivos de Bankard ahora exportan **únicamente 5 columnas** con nombres específicos:

| Columna Original | Columna Exportada | Descripción |
|------------------|-------------------|-------------|
| `primer_nombre` | `primer_nombre_bankard` | Nombre del cliente |
| `cupo` | `Cupo_Aprobado_OB_BK` | Cupo aprobado (formateado con comas) |
| `BIN` | `Marca_BK_OB` | Marca de la tarjeta |
| `correo` | `correo` | Correo electrónico |
| `telefono` | `telefono` | Número de teléfono |

## 📁 Archivos de Descarga

### 1. **Base Bankard LIMPIA.xlsx**
- Contiene **todas las cédulas** procesadas
- **5 columnas** con nombres mapeados
- **Cupo formateado** con separadores de miles (ej: 1,000)

### 2. **ZIP por tipo y exclusión**
- Archivos segmentados por `TIPO` y `exclusion`
- **Mismo mapeo** de columnas
- **Estructura**: `{TIPO}_{EXCLUSION}_{FECHA}.xlsx`
- **Ejemplo**: `VISA_ORO_SI_1110.xlsx`

## 🔄 Procesamiento

1. **Limpieza de nombres**: Se aplica formato de nombres propios (Primera Letra Mayúscula)
2. **Mapeo automático**: Las columnas se renombran según el mapeo
3. **Formateo**: Los cupos se formatean con comas (1,000)
4. **Validación**: Se asegura que todas las columnas existan
5. **Limpieza**: Solo se exportan las 5 columnas especificadas

### 🧹 Limpiezas Aplicadas

- **Nombres**: Formato de nombres propios (ej: "juan perez" → "Juan Perez")
- **Cupos**: Formato con separadores de miles (ej: 1000 → "1,000")
- **Teléfonos/Cédulas**: Normalizados a 10 dígitos
- **BINs**: Corregidos automáticamente con sistema inteligente
- **Exclusiones**: Aplicadas desde sistema consolidado (5,776 cédulas)
- **TIPO**: Si no existe columna TIPO, se asigna automáticamente "No Clientes"

## ✅ Ventajas

- **Consistencia**: Nombres de columnas estandarizados
- **Limpieza**: Solo las columnas necesarias
- **Formato**: Cupos legibles con separadores de miles
- **Compatibilidad**: Fácil integración con otros sistemas
