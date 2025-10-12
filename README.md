# Limpieza Credimax & Bankard

Aplicación Streamlit para normalizar bases de clientes de Credimax y Bankard,
validar campos críticos y generar descargas segmentadas listas para uso
operativo.

## Requisitos

1. Python 3.10 o superior.
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

```bash
streamlit run app.py
```

La interfaz se abre en el navegador y permite seleccionar el flujo deseado
desde la barra lateral.

## Flujo Credimax

* Limpieza y validación de cédulas, celulares, nombres y cupos.
* Reasignación de la columna `Campaña Growth` según reglas determinísticas.
* Descargas disponibles:
  * Base limpia general.
  * Comparativo de campañas (original vs calculada).
  * ZIP opcional segmentado por campaña con las columnas:
    `CELULAR`, `primer_nombre_credimax`, `correo`, `monto_credito_aprob`,
    `cuota_credimax`, `Tasa_Credito_Aprob`, `Cupo_Aprobado_OB_BK`,
    `Marca_BK_OB`.
  * **Plantillas SMS segmentadas por campaña** (nuevo):
    - Variables personalizables: `<#monto#>`, `<#tasa#>`, `<#link#>`
    - Archivos Excel con 2 columnas: `celular` y `mensaje`
    - ZIP con plantillas separadas por cada campaña

## Flujo Bankard

1. **Base Bankard**: carga un Excel con las columnas del banco.
2. **Exclusiones**:
   * Puedes subir archivos puntuales (columna `IDENTIFICACION`).
   * Coloca archivos `.xlsx` permanentes en `data/exclusiones_bankard/` para
     que se apliquen en cada ejecución. Los nombres de los archivos cargados
     se listan en la barra lateral.
3. Limpiezas aplicadas:
   * Normalización de `cupo`, `BIN`, teléfonos y cédulas.
   * Filtro por vigencia actual.
   * Cruce con exclusiones (`SI`/`NO`).
4. Descargas disponibles:
   * Base limpia completa.
   * ZIP segmentado por `TIPO` y bandera de exclusión (`SI`/`NO`).
   * **Plantillas SMS segmentadas por tipo** (nuevo):
     - Variables personalizables: `<#marca#>`, `<#cupo#>`, `<#link#>`
     - Archivos Excel con 2 columnas: `telefono` y `mensaje`
     - ZIP con plantillas separadas por cada tipo (solo sin exclusión)

### Mantener la carpeta de exclusiones

La carpeta `data/exclusiones_bankard/` incluye un `.gitignore` para evitar
versionar datos sensibles. Asegúrate de crear los archivos de exclusión en tu
entorno local o servidor de despliegue y actualizarlos según corresponda.

## Plantillas SMS Segmentadas

### Credimax
- **Segmentación**: Por campaña (igual que ZIP de datos)
- **Variables**: `<#monto#>`, `<#tasa#>`, `<#link#>`
- **Filtros**: Solo registros con `IND_DESEMBOLSO = "0"` y celulares válidos
- **Archivos**: `SMS_{Campaña}_{fecha}.xlsx` en ZIP `SMS_Credimax_Segmentado_{fecha}.zip`

### Bankard
- **Segmentación**: Por tipo de tarjeta (igual que ZIP de datos)
- **Variables**: `<#marca#>`, `<#cupo#>`, `<#link#>`
- **Filtros**: Solo registros con `exclusion = "NO"` y teléfonos válidos
- **Archivos**: `SMS_Bankard_{Tipo}_{fecha}.xlsx` en ZIP `SMS_Bankard_Segmentado_{fecha}.zip`

### Uso
1. Activar checkbox "Generar plantilla SMS" en la barra lateral
2. Configurar texto del SMS con variables personalizables
3. Ingresar enlace que reemplazará `<#link#>`
4. Descargar ZIP con plantillas segmentadas listas para envío masivo

## Actualización de la memoria de BIN

Cuando aparecen valores en `BIN` fuera de la lista permitida, la aplicación
solicita correcciones desde la interfaz y guarda las equivalencias en el archivo
`memoria_correcciones_bin.json`.

## Soporte

Para dudas o ajustes adicionales, consulta con el equipo de Marketing Directo o
actualiza el código en `app.py`.
