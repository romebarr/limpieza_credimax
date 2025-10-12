"""
Script de prueba para verificar que los módulos funcionan correctamente.
"""

# Probar imports de los módulos (sin streamlit)
try:
    # Módulos comunes
    from modules.common.validators import validar_cedula_10, normalizar_celular_ec
    from modules.common.formatters import a_nombre_propio, cupo_a_texto_miles_coma
    from modules.common.utils import df_to_excel_bytes, procesar_archivo_excel_exclusiones
    
    # Módulos de integración
    from modules.integrations.bitly_no_streamlit import acortar_enlace_bitly
    
    # Módulos de Credimax
    from modules.credimax.processor import preparar_zip_por_campana
    # from modules.credimax.sms_generator import generar_plantilla_sms_credimax_segmentada  # Requiere streamlit
    
    # Módulos de Bankard
    from modules.bankard.processor import preparar_zip_bankard
    from modules.bankard.cleaner import limpiar_cupo_bankard, limpiar_nombres_bankard
    from modules.bankard.exclusions import cargar_exclusiones_consolidadas
    from modules.bankard.bin_corrector import cargar_memoria_correcciones, calcular_similitud_bin
    # from modules.bankard.sms_generator import generar_plantilla_sms_bankard_segmentada  # Requiere streamlit
    
    print("✅ Todos los imports funcionan correctamente")
    
    # Probar algunas funciones básicas
    print(f"✅ validar_cedula_10('1234567890'): {validar_cedula_10('1234567890')}")
    print(f"✅ normalizar_celular_ec('0987654321'): {normalizar_celular_ec('0987654321')}")
    print(f"✅ a_nombre_propio('juan perez'): {a_nombre_propio('juan perez')}")
    print(f"✅ cupo_a_texto_miles_coma(1000): {cupo_a_texto_miles_coma(1000)}")
    print(f"✅ calcular_similitud_bin('Visa Oro', 'Visa Oro'): {calcular_similitud_bin('Visa Oro', 'Visa Oro')}")
    
    print("\n🎉 Todos los módulos de Bankard están funcionando correctamente!")
    
except ImportError as e:
    print(f"❌ Error de import: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
