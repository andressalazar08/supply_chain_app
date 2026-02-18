"""
Script de migración para agregar sistema de jerarquía admin maestro/profesores
"""

from app import app
from extensions import db
from models import Usuario, Empresa
from sqlalchemy import text

def migrate():
    with app.app_context():
        print("="*60)
        print("INICIANDO MIGRACIÓN: Sistema de Admin Maestro")
        print("="*60)
        
        # Agregar columnas a Usuario
        try:
            with db.engine.connect() as conn:
                # Verificar si las columnas ya existen
                result = conn.execute(text("PRAGMA table_info(usuarios)"))
                columns = [row[1] for row in result]
                
                if 'es_super_admin' not in columns:
                    print("\n✓ Agregando columna 'es_super_admin' a usuarios...")
                    conn.execute(text("ALTER TABLE usuarios ADD COLUMN es_super_admin BOOLEAN DEFAULT 0"))
                    conn.commit()
                else:
                    print("\n- Columna 'es_super_admin' ya existe")
                
                if 'profesor_id' not in columns:
                    print("✓ Agregando columna 'profesor_id' a usuarios...")
                    conn.execute(text("ALTER TABLE usuarios ADD COLUMN profesor_id INTEGER"))
                    conn.commit()
                else:
                    print("- Columna 'profesor_id' ya existe")
        except Exception as e:
            print(f"✗ Error al modificar tabla usuarios: {e}")
        
        # Agregar columna a Empresa
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(empresas)"))
                columns = [row[1] for row in result]
                
                if 'profesor_id' not in columns:
                    print("✓ Agregando columna 'profesor_id' a empresas...")
                    conn.execute(text("ALTER TABLE empresas ADD COLUMN profesor_id INTEGER"))
                    conn.commit()
                else:
                    print("- Columna 'profesor_id' ya existe")
        except Exception as e:
            print(f"✗ Error al modificar tabla empresas: {e}")
        
        # Configurar usuario admin como super admin
        try:
            admin = Usuario.query.filter_by(username='admin').first()
            if admin:
                admin.es_super_admin = True
                db.session.commit()
                print("\n✓ Usuario 'admin' configurado como Super Admin")
            else:
                print("\n⚠ Usuario 'admin' no encontrado")
        except Exception as e:
            print(f"✗ Error al configurar super admin: {e}")
        
        # Asignar empresas existentes al admin maestro
        try:
            admin = Usuario.query.filter_by(es_super_admin=True).first()
            if admin:
                empresas = Empresa.query.filter_by(profesor_id=None).all()
                for empresa in empresas:
                    empresa.profesor_id = admin.id
                db.session.commit()
                print(f"✓ {len(empresas)} empresas asignadas al admin maestro")
        except Exception as e:
            print(f"✗ Error al asignar empresas: {e}")
        
        print("\n" + "="*60)
        print("MIGRACIÓN COMPLETADA")
        print("="*60)

if __name__ == '__main__':
    migrate()
