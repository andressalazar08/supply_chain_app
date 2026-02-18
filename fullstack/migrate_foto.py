"""
Script de migración para agregar el campo foto_perfil a la tabla usuarios
"""

from app import app, db
from models import Usuario
import sqlite3
import os

def migrate():
    print("🔄 Iniciando migración para agregar foto_perfil...")
    
    with app.app_context():
        # Obtener la ruta de la base de datos
        db_path = os.path.join(app.instance_path, 'supply_chain.db')
        print(f"  📂 Base de datos: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'foto_perfil' in columns:
            print("  ℹ️  Columna foto_perfil ya existe")
        else:
            print("  ➕ Agregando columna: foto_perfil")
            try:
                cursor.execute("ALTER TABLE usuarios ADD COLUMN foto_perfil VARCHAR(255)")
                conn.commit()
                print("  ✅ Columna foto_perfil agregada exitosamente")
            except Exception as e:
                print(f"  ❌ Error al agregar columna: {e}")
                conn.rollback()
        
        conn.close()
        
        # Crear directorio para fotos de perfil
        upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'perfiles')
        os.makedirs(upload_folder, exist_ok=True)
        print(f"  📁 Directorio de uploads creado: {upload_folder}")
        
        print("\n✨ ¡Migración completada exitosamente!")

if __name__ == '__main__':
    migrate()
