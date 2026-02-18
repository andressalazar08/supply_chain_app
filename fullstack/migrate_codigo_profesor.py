"""
Script de migración para agregar el campo codigo_profesor a la tabla usuarios
"""

from app import app, db
from models import Usuario
import sqlite3

def migrate():
    print("🔄 Iniciando migración para agregar codigo_profesor...")
    
    with app.app_context():
        # Obtener la ruta de la base de datos
        import os
        db_path = os.path.join(app.instance_path, 'supply_chain.db')
        print(f"  📂 Base de datos: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'codigo_profesor' in columns:
            print("  ℹ️  Columna codigo_profesor ya existe")
        else:
            print("  ➕ Agregando columna: codigo_profesor")
            try:
                cursor.execute("ALTER TABLE usuarios ADD COLUMN codigo_profesor VARCHAR(20)")
                conn.commit()
                print("  ✅ Columna codigo_profesor agregada exitosamente")
            except Exception as e:
                print(f"  ❌ Error al agregar columna: {e}")
                conn.rollback()
        
        # Crear índice único para codigo_profesor
        try:
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_codigo_profesor 
                ON usuarios(codigo_profesor) 
                WHERE codigo_profesor IS NOT NULL
            """)
            conn.commit()
            print("  ✅ Índice UNIQUE agregado a codigo_profesor")
        except Exception as e:
            print(f"  ⚠️  Error al crear índice: {e}")
        
        conn.close()
        
        print("\n✨ ¡Migración completada exitosamente!")
        
        # Mostrar resumen
        usuarios = Usuario.query.all()
        docentes = Usuario.query.filter_by(tipo_usuario='docente').count()
        estudiantes = Usuario.query.filter_by(tipo_usuario='estudiante').count()
        
        print("\n📊 Resumen de usuarios:")
        print(f"  Total: {len(usuarios)}")
        print(f"  Docentes: {docentes}")
        print(f"  Estudiantes: {estudiantes}")

if __name__ == '__main__':
    migrate()
