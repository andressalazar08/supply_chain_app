"""
Script simple para probar que todo funciona
"""

if __name__ == '__main__':
    print("=" * 50)
    print("VERIFICACION DE SISTEMA")
    print("=" * 50)
    
    try:
        print("\n[1/4] Importando extensions...")
        from extensions import db
        print("      OK - extensions")
        
        print("\n[2/4] Importando app...")
        from app import app
        print("      OK - app")
        
        print("\n[3/4] Importando models...")
        from models import Usuario, Empresa, Producto, Simulacion
        print("      OK - models")
        
        print("\n[4/4] Importando routes...")
        from routes import auth, profesor, estudiante
        print("      OK - routes")
        
        print("\n" + "=" * 50)
        print("TODOS LOS IMPORTS FUNCIONAN CORRECTAMENTE")
        print("=" * 50)
        print("\nPuedes ejecutar:")
        print("  1. python init_db.py  (para crear la base de datos)")
        print("  2. python app.py      (para iniciar la aplicacion)")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
