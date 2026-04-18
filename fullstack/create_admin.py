#!/usr/bin/env python
"""
Script para crear un usuario admin en la base de datos
Uso: python create_admin.py
"""

from app import app, db
from models import Usuario
from werkzeug.security import generate_password_hash


def create_admin(username='admin', password='admin123', email='admin@erpeducativo.com'):
    """Crear usuario administrador"""
    with app.app_context():
        # Verificar si el admin ya existe
        admin = Usuario.query.filter_by(username=username).first()
        if admin:
            print(f"❌ El usuario '{username}' ya existe")
            return False

        # Crear nuevo admin
        new_admin = Usuario(
            username=username,
            password=generate_password_hash(password),
            email=email,
            nombre_completo='Administrador del Sistema',
            tipo_usuario='profesor',
            es_super_admin=True,
            rol='admin',
            email_verified=True,
            activo=True
        )

        try:
            db.session.add(new_admin)
            db.session.commit()
            print(f"✅ Administrador creado exitosamente")
            print(f"   Usuario: {username}")
            print(f"   Contraseña: {password}")
            print(f"   Email: {email}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear administrador: {str(e)}")
            return False


if __name__ == '__main__':
    create_admin()
