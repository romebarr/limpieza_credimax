"""
Script de prueba para verificar que app_modular.py funciona correctamente.

Este script simula la ejecución de la aplicación modularizada sin Streamlit.
"""

def test_imports():
    """Prueba que todos los imports funcionan correctamente."""
    try:
        # Imports principales
        import pandas as pd
        import numpy as np
        from datetime import datetime
        
        # Imports de módulos UI
        from modules.ui.main_ui import (
            configurar_pagina, mostrar_header, mostrar_selector_flujo, 
            mostrar_info_flujo, mostrar_uploader_archivo, mostrar_sidebar_info
        )
        from modules.ui.credimax_ui import (
            mostrar_sidebar_credimax, mostrar_resultados_credimax, 
            mostrar_downloads_credimax, mostrar_validaciones_credimax
        )
        from modules.ui.bankard_ui import (
            mostrar_sidebar_bankard, mostrar_resultados_bankard,
            mostrar_downloads_bankard, mostrar_validaciones_bankard
        )
        
        # Imports de procesamiento
        from modules.credimax.processor import preparar_zip_por_campana
        from modules.credimax.sms_generator import generar_plantilla_sms_credimax_segmentada
        from modules.bankard.processor import preparar_zip_bankard
        from modules.bankard.cleaner import (
            limpiar_cupo_bankard, filtrar_vigencia_bankard, 
            limpiar_telefonos_cedulas_bankard, limpiar_nombres_bankard
        )
        from modules.bankard.exclusions import (
            cargar_cedulas_excluir_uploads, cargar_exclusiones_consolidadas,
            consolidar_exclusiones_desde_directorio, marcar_exclusiones_varios
        )
        from modules.bankard.bin_corrector import (
            cargar_memoria_correcciones, cargar_estadisticas_bin,
            detectar_bins_no_permitidos_inteligente, aplicar_correcciones_bin
        )
        from modules.bankard.sms_generator import generar_plantilla_sms_bankard_segmentada
        
        # Imports comunes
        from modules.common.validators import validar_cedula_10, normalizar_celular_ec
        from modules.common.formatters import a_nombre_propio, cupo_a_texto_miles_coma
        from modules.common.utils import df_to_excel_bytes
        
        print("✅ Todos los imports funcionan correctamente")
        return True
        
    except ImportError as e:
        print(f"❌ Error de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_functions():
    """Prueba que las funciones principales funcionan."""
    try:
        from modules.common.validators import validar_cedula_10, normalizar_celular_ec
        from modules.common.formatters import a_nombre_propio, cupo_a_texto_miles_coma
        from modules.bankard.bin_corrector import calcular_similitud_bin
        
        # Probar funciones básicas
        assert validar_cedula_10('1234567890') == True
        assert normalizar_celular_ec('0987654321') == '0987654321'
        assert a_nombre_propio('juan perez') == 'Juan Perez'
        assert cupo_a_texto_miles_coma(1000) == '1,000'
        assert calcular_similitud_bin('Visa Oro', 'Visa Oro') == 1.0
        
        print("✅ Todas las funciones funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en funciones: {e}")
        return False

def test_data_processing():
    """Prueba el procesamiento de datos básico."""
    try:
        import pandas as pd
        from modules.common.validators import validar_cedula_10, normalizar_celular_ec
        from modules.common.formatters import a_nombre_propio, cupo_a_texto_miles_coma
        
        # Crear DataFrame de prueba
        df = pd.DataFrame({
            'CEDULA': ['1234567890', '0987654321', '1111111111'],
            'CELULAR': ['0987654321', '0998765432', 'invalid'],
            'primer_nombre': ['juan perez', 'maria garcia', 'pedro lopez'],
            'CUPO': [1000, 2000, 3000]
        })
        
        # Aplicar transformaciones
        df['CEDULA'] = df['CEDULA'].apply(lambda x: x if validar_cedula_10(x) else None)
        df['CELULAR'] = df['CELULAR'].apply(normalizar_celular_ec)
        df['primer_nombre'] = df['primer_nombre'].apply(a_nombre_propio)
        df['CUPO'] = df['CUPO'].apply(cupo_a_texto_miles_coma)
        
        # Verificar resultados
        assert df['CEDULA'].iloc[0] == '1234567890'
        assert df['CELULAR'].iloc[0] == '0987654321'
        assert df['primer_nombre'].iloc[0] == 'Juan Perez'
        assert df['CUPO'].iloc[0] == '1,000'
        
        print("✅ Procesamiento de datos funciona correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en procesamiento: {e}")
        return False

def main():
    """Función principal de prueba."""
    print("🧪 Iniciando pruebas de app_modular.py...")
    
    tests = [
        ("Imports", test_imports),
        ("Funciones", test_functions),
        ("Procesamiento de Datos", test_data_processing)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Probando {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} falló")
    
    print(f"\n📊 Resultados: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! app_modular.py está listo.")
        return True
    else:
        print("❌ Algunas pruebas fallaron. Revisa los errores.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
