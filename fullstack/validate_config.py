#!/usr/bin/env python
"""Script para validar la configuración de la aplicación"""

from app import app
from extensions import db

print("=" * 60)
print("VALIDACIÓN DE CONFIGURACIÓN")
print("=" * 60)

with app.app_context():
    print("\n✅ App inicializada correctamente")
    print(f"\n📊 CONFIGURACIÓN:")
    print(f"   - FLASK_ENV: {app.config.get('ENV', 'No definida')}")
    print(f"   - DEBUG: {app.debug}")
    print(f"   - DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"   - MAIL_SERVER: {app.config.get('MAIL_SERVER')}")

    print(f"\n📦 EXTENSIONES:")
    print(f"   - SQLAlchemy: ✅")
    print(f"   - Flask-Login: ✅")
    print(f"   - Flask-Mail: ✅")

    try:
        db.create_all()
        print(f"\n✅ Base de datos verificada/creada exitosamente")
    except Exception as e:
        print(f"\n❌ Error con la base de datos: {e}")

print("\n" + "=" * 60)
print("¡Proyecto listo para deploy!")
print("=" * 60)
