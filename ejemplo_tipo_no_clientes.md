# Ejemplo: Columna TIPO para No Clientes

## 📋 Escenario

Cuando subes un archivo de Bankard **No Clientes** que no tiene la columna `TIPO`, el sistema automáticamente:

1. **Detecta** que no existe la columna `TIPO` o `TIPO `
2. **Crea** la columna `TIPO ` automáticamente
3. **Asigna** el valor "No Clientes" a todos los registros
4. **Muestra** un mensaje informativo en la interfaz

## 🔄 Proceso Automático

### **Antes del Procesamiento:**
```
Archivo Excel subido:
├── primer_nombre
├── cupo
├── BIN
├── correo
└── telefono
```

### **Después del Procesamiento:**
```
DataFrame procesado:
├── primer_nombre
├── cupo
├── BIN
├── correo
├── telefono
└── TIPO  ← Creada automáticamente con valor "No Clientes"
```

## 📁 Archivos Generados

### **Base Bankard LIMPIA.xlsx**
- Todos los registros con `TIPO = "No Clientes"`
- 5 columnas mapeadas según especificación

### **ZIP Segmentado**
- Archivos: `No_Clientes_SI_1110.xlsx`, `No_Clientes_NO_1110.xlsx`
- Segmentación por exclusión (SI/NO)
- Mismo mapeo de columnas

## 💡 Mensaje en la Interfaz

Cuando se detecta que no hay columna TIPO:
> ℹ️ **Columna TIPO no encontrada** - Se asignó automáticamente 'No Clientes' a todos los registros

## ✅ Beneficios

- **Sin configuración manual**: El sistema detecta automáticamente
- **Consistencia**: Todos los archivos tienen la columna TIPO
- **Segmentación**: Funciona igual que archivos con TIPO existente
- **Flexibilidad**: Maneja tanto clientes como no clientes
