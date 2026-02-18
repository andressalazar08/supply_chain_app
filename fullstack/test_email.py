"""
Script de prueba para verificar configuración de correo
"""

from app import app
from utils.email_utils import enviar_correo_verificacion, enviar_correo_recuperacion
import sys

def test_email_config():
    """Prueba la configuración de correo"""
    with app.app_context():
        print("=" * 60)
        print("🧪 PRUEBA DE CONFIGURACIÓN DE CORREO")
        print("=" * 60)
        
        # Mostrar configuración actual
        print("\n📋 Configuración actual:")
        print(f"  Servidor: {app.config.get('MAIL_SERVER')}")
        print(f"  Puerto: {app.config.get('MAIL_PORT')}")
        print(f"  TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"  Usuario: {app.config.get('MAIL_USERNAME')}")
        print(f"  Password: {'***' if app.config.get('MAIL_PASSWORD') else 'NO CONFIGURADO'}")
        print(f"  Remitente: {app.config.get('MAIL_DEFAULT_SENDER')}")
        
        # Verificar si está configurado
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            print("\n❌ ERROR: Credenciales de correo no configuradas")
            print("\n📝 Para configurar:")
            print("  Windows PowerShell:")
            print('    $env:MAIL_USERNAME="tu-correo@gmail.com"')
            print('    $env:MAIL_PASSWORD="tu-contraseña-de-app"')
            print("\n  Linux/Mac:")
            print('    export MAIL_USERNAME="tu-correo@gmail.com"')
            print('    export MAIL_PASSWORD="tu-contraseña-de-app"')
            return False
        
        # Solicitar correo de prueba
        print("\n" + "=" * 60)
        correo_prueba = input("📧 Ingresa un correo para enviar prueba: ").strip()
        
        if not correo_prueba or '@' not in correo_prueba:
            print("❌ Correo inválido")
            return False
        
        # Prueba 1: Correo de verificación
        print("\n🔄 Enviando correo de verificación de prueba...")
        try:
            success, mensaje = enviar_correo_verificacion(
                app.mail,
                correo_prueba,
                "123456"
            )
            
            if success:
                print("✅ Correo de verificación enviado exitosamente")
            else:
                print(f"❌ Error: {mensaje}")
                return False
        except Exception as e:
            print(f"❌ Excepción al enviar: {str(e)}")
            return False
        
        # Prueba 2: Correo de recuperación
        print("\n🔄 Enviando correo de recuperación de prueba...")
        try:
            success, mensaje = enviar_correo_recuperacion(
                app.mail,
                correo_prueba,
                "Temp1234"
            )
            
            if success:
                print("✅ Correo de recuperación enviado exitosamente")
            else:
                print(f"❌ Error: {mensaje}")
                return False
        except Exception as e:
            print(f"❌ Excepción al enviar: {str(e)}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("=" * 60)
        print(f"\n📨 Revisa tu bandeja de entrada en: {correo_prueba}")
        print("   (También revisa spam/promociones)")
        return True


def test_email_validation():
    """Prueba la validación de correos institucionales"""
    from utils.email_utils import validar_correo_institucional
    
    print("\n" + "=" * 60)
    print("🧪 PRUEBA DE VALIDACIÓN DE CORREOS")
    print("=" * 60)
    
    casos_prueba = [
        ("estudiante@universidad.edu.co", True),
        ("profesor@unal.edu.co", True),
        ("test@gmail.com", True),  # Temporal para pruebas
        ("invalido@yahoo.com", False),
        ("test@outlook.com", False),
    ]
    
    print("\n📋 Probando validación de dominios:")
    for correo, esperado in casos_prueba:
        resultado = validar_correo_institucional(correo)
        simbolo = "✅" if resultado == esperado else "❌"
        estado = "Válido" if resultado else "Rechazado"
        print(f"  {simbolo} {correo}: {estado}")
    
    print("\n💡 Recuerda personalizar los dominios en utils/email_utils.py")


if __name__ == '__main__':
    print("\n🚀 Iniciando pruebas del sistema de correo...\n")
    
    # Prueba de validación
    test_email_validation()
    
    # Preguntar si quiere probar envío
    print("\n" + "=" * 60)
    respuesta = input("\n¿Quieres enviar correos de prueba? (s/n): ").strip().lower()
    
    if respuesta in ['s', 'si', 'y', 'yes']:
        success = test_email_config()
        if not success:
            sys.exit(1)
    else:
        print("\n✅ Prueba de validación completada")
        print("💡 Para probar el envío, ejecuta el script nuevamente")
    
    print("\n✨ Pruebas finalizadas\n")
