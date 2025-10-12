"""
Script de prueba para verificar que los módulos core funcionan correctamente.

Este script prueba solo los módulos que no dependen de Streamlit.
"""

def test_common_modules():
    """Prueba los módulos comunes."""
    try:
        from modules.common.validators import validar_cedula_10, normalizar_celular_ec
        from modules.common.formatters import a_nombre_propio, cupo_a_texto_miles_coma
        from modules.common.utils import df_to_excel_bytes
        
        # Probar funciones básicas
        assert validar_cedula_10('1234567890') == True
        assert normalizar_celular_ec('0987654321') == '0987654321'
        assert a_nombre_propio('juan perez') == 'Juan Perez'
        assert cupo_a_texto_miles_coma(1000) == '1,000'
        
        print("✅ Módulos comunes funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en módulos comunes: {e}")
        return False

def test_bankard_core():
    """Prueba los módulos core de Bankard."""
    try:
        from modules.bankard.cleaner import limpiar_cupo_bankard, limpiar_nombres_bankard
        from modules.bankard.bin_corrector import calcular_similitud_bin, cargar_memoria_correcciones
        from modules.bankard.exclusions import cargar_exclusiones_consolidadas
        
        # Probar funciones básicas
        assert calcular_similitud_bin('Visa Oro', 'Visa Oro') == 1.0
        assert calcular_similitud_bin('Visa Oro', 'Visa Platinum') < 1.0
        
        # Probar carga de memoria
        memoria = cargar_memoria_correcciones()
        assert isinstance(memoria, dict)
        
        # Probar carga de exclusiones
        exclusiones, estadisticas = cargar_exclusiones_consolidadas()
        assert isinstance(exclusiones, dict)
        assert isinstance(estadisticas, dict)
        
        print("✅ Módulos core de Bankard funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en módulos core de Bankard: {e}")
        return False

def test_credimax_core():
    """Prueba los módulos core de Credimax."""
    try:
        from modules.credimax.processor import preparar_zip_por_campana
        
        # Crear DataFrame de prueba
        import pandas as pd
        df = pd.DataFrame({
            'Campaña Growth': ['Campaña A', 'Campaña B'],
            'IND_DESEMBOLSO': ['0', '0'],
            'CELULAR': ['0987654321', '0998765432'],
            'primer_nombre': ['Juan Perez', 'Maria Garcia'],
            'CORREO CLIENTE': ['juan@test.com', 'maria@test.com'],
            'CUPO': ['1000', '2000'],
            'CUOTA': ['100.50', '200.75'],
            'Tasa': ['15.5', '16.0'],
            'CUPO_TARJETA_BK': ['5000', '6000'],
            'MARCA_TARJETA_BK': ['Visa Oro', 'Mastercard']
        })
        
        # Probar generación de ZIP
        zip_bytes, archivos = preparar_zip_por_campana(df, "Campaña Growth")
        
        print("✅ Módulos core de Credimax funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en módulos core de Credimax: {e}")
        return False

def test_integrations():
    """Prueba los módulos de integración."""
    try:
        from modules.integrations.bitly_no_streamlit import acortar_enlace_bitly
        
        # Probar función de acortamiento (sin hacer llamada real)
        url = "https://example.com"
        resultado = acortar_enlace_bitly(url)
        assert isinstance(resultado, str)
        
        print("✅ Módulos de integración funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en módulos de integración: {e}")
        return False

def test_data_processing():
    """Prueba el procesamiento de datos completo."""
    try:
        import pandas as pd
        from modules.common.validators import validar_cedula_10, normalizar_celular_ec
        from modules.common.formatters import a_nombre_propio, cupo_a_texto_miles_coma
        from modules.bankard.cleaner import limpiar_cupo_bankard
        
        # Crear DataFrame de prueba
        df = pd.DataFrame({
            'CEDULA': ['1234567890', '0987654321', '1111111111'],
            'CELULAR': ['0987654321', '0998765432', 'invalid'],
            'primer_nombre': ['juan perez', 'maria garcia', 'pedro lopez'],
            'cupo': [1000, 2000, 3000]
        })
        
        # Aplicar transformaciones
        df['CEDULA'] = df['CEDULA'].apply(lambda x: x if validar_cedula_10(x) else None)
        df['CELULAR'] = df['CELULAR'].apply(normalizar_celular_ec)
        df['primer_nombre'] = df['primer_nombre'].apply(a_nombre_propio)
        df = limpiar_cupo_bankard(df)
        
        # Verificar resultados
        assert df['CEDULA'].iloc[0] == '1234567890'
        assert df['CELULAR'].iloc[0] == '0987654321'
        assert df['primer_nombre'].iloc[0] == 'Juan Perez'
        assert df['cupo'].iloc[0] == 1000
        
        print("✅ Procesamiento de datos completo funciona correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en procesamiento de datos: {e}")
        return False

def main():
    """Función principal de prueba."""
    print("🧪 Iniciando pruebas de módulos core...")
    
    tests = [
        ("Módulos Comunes", test_common_modules),
        ("Módulos Core Bankard", test_bankard_core),
        ("Módulos Core Credimax", test_credimax_core),
        ("Módulos de Integración", test_integrations),
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
        print("🎉 ¡Todas las pruebas pasaron! Los módulos core están listos.")
        return True
    else:
        print("❌ Algunas pruebas fallaron. Revisa los errores.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
