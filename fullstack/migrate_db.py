"""
Script para migrar la base de datos existente
Agrega los nuevos campos al modelo Usuario
"""

from app import app, db
from models import Usuario
from sqlalchemy import text

def migrate_database():
    """Migra la base de datos agregando nuevos campos"""
    with app.app_context():
        print("🔄 Iniciando migración de base de datos...")
        
        try:
            # Verificar si las columnas ya existen
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('usuarios')]
            
            # Columnas a agregar
            nuevas_columnas = {
                'email_verified': 'BOOLEAN DEFAULT 0',
                'verification_code': 'VARCHAR(6)',
                'verification_code_expires': 'DATETIME',
                'reset_token': 'VARCHAR(10)',
                'reset_token_expires': 'DATETIME',
                'universidad': 'VARCHAR(200)',
                'sede': 'VARCHAR(100)',
                'codigo_estudiante': 'VARCHAR(20)',
                'carrera': 'VARCHAR(200)',
                'tipo_usuario': 'VARCHAR(20) DEFAULT "estudiante"'
            }
            
            # Agregar columnas si no existen
            for columna, tipo in nuevas_columnas.items():
                if columna not in columns:
                    print(f"  ➕ Agregando columna: {columna}")
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(text(f"ALTER TABLE usuarios ADD COLUMN {columna} {tipo}"))
                            conn.commit()
                        print(f"  ✅ Columna {columna} agregada exitosamente")
                    except Exception as e:
                        print(f"  ⚠️  Error al agregar {columna}: {str(e)}")
                else:
                    print(f"  ℹ️  Columna {columna} ya existe")
            
            # Actualizar usuarios existentes
            print("\n📋 Actualizando usuarios existentes...")
            usuarios = Usuario.query.all()
            
            for usuario in usuarios:
                # Marcar usuarios de prueba piloto y admin como verificados
                if usuario.username.startswith('estudiante_') or usuario.username == 'admin':
                    usuario.email_verified = True
                    print(f"  ✓ {usuario.username} marcado como verificado")
                
                # Establecer tipo_usuario si no existe
                if not hasattr(usuario, 'tipo_usuario') or usuario.tipo_usuario is None:
                    if usuario.username == 'admin' or usuario.rol == 'admin':
                        usuario.tipo_usuario = 'docente'
                        print(f"  ✓ {usuario.username} establecido como docente")
                    else:
                        usuario.tipo_usuario = 'estudiante'
                        print(f"  ✓ {usuario.username} establecido como estudiante")
            
            db.session.commit()
            
            # Hacer email único si no lo es
            try:
                print("\n🔐 Agregando restricción UNIQUE a email...")
                with db.engine.connect() as conn:
                    # Primero crear índice único (SQLite no soporta ALTER COLUMN directamente)
                    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_email_unique ON usuarios(email)"))
                    conn.commit()
                print("  ✅ Restricción UNIQUE agregada a email")
            except Exception as e:
                print(f"  ℹ️  Restricción ya existe o error: {str(e)}")
            
            # Hacer codigo_estudiante único
            try:
                print("\n🔐 Agregando restricción UNIQUE a codigo_estudiante...")
                with db.engine.connect() as conn:
                    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_codigo_estudiante_unique ON usuarios(codigo_estudiante)"))
                    conn.commit()
                print("  ✅ Restricción UNIQUE agregada a codigo_estudiante")
            except Exception as e:
                print(f"  ℹ️  Restricción ya existe o error: {str(e)}")
            
            # Hacer rol nullable
            try:
                print("\n🔧 Haciendo campo 'rol' nullable...")
                # En SQLite no se puede modificar columnas directamente, pero los nuevos usuarios tendrán rol=NULL
                print("  ℹ️  Los nuevos usuarios se crearán con rol=NULL (se asigna después)")
            except Exception as e:
                print(f"  ℹ️  {str(e)}")
            
            print("\n✨ ¡Migración completada exitosamente!")
            print("\n📊 Resumen de usuarios:")
            print(f"  Total: {len(usuarios)}")
            print(f"  Verificados: {sum(1 for u in usuarios if u.email_verified)}")
            
        except Exception as e:
            print(f"\n❌ Error durante la migración: {str(e)}")
            db.session.rollback()
            return False
        
        return True


if __name__ == '__main__':
    success = migrate_database()
    if success:
        print("\n✅ Base de datos lista para el nuevo sistema de autenticación")
    else:
        print("\n❌ Hubo problemas durante la migración")
