"""
Script para migrar la base de datos agregando nuevos campos
- simulacion_id a Empresa
- nombre, capital_inicial_empresas, activa a Simulacion
"""
from app import app
from extensions import db
from sqlalchemy import text

def migrar_base_datos():
    with app.app_context():
        try:
            print("🔧 Iniciando migración de base de datos...")
            
            # Agregar campos a Simulacion
            print("\n📊 Migrando tabla 'simulacion'...")
            
            # Agregar campo 'nombre'
            try:
                db.session.execute(text("""
                    ALTER TABLE simulacion 
                    ADD COLUMN nombre VARCHAR(100) DEFAULT 'Simulación'
                """))
                print("  ✅ Campo 'nombre' agregado")
            except Exception as e:
                if "Duplicate column name" in str(e) or "duplicate column" in str(e):
                    print("  ⏭️  Campo 'nombre' ya existe")
                else:
                    print(f"  ⚠️  Error en 'nombre': {e}")
            
            # Agregar campo 'capital_inicial_empresas'
            try:
                db.session.execute(text("""
                    ALTER TABLE simulacion 
                    ADD COLUMN capital_inicial_empresas FLOAT DEFAULT 50000000.0
                """))
                print("  ✅ Campo 'capital_inicial_empresas' agregado")
            except Exception as e:
                if "Duplicate column name" in str(e) or "duplicate column" in str(e):
                    print("  ⏭️  Campo 'capital_inicial_empresas' ya existe")
                else:
                    print(f"  ⚠️  Error en 'capital_inicial_empresas': {e}")
            
            # Agregar campo 'activa'
            try:
                db.session.execute(text("""
                    ALTER TABLE simulacion 
                    ADD COLUMN activa BOOLEAN DEFAULT TRUE
                """))
                print("  ✅ Campo 'activa' agregado")
            except Exception as e:
                if "Duplicate column name" in str(e) or "duplicate column" in str(e):
                    print("  ⏭️  Campo 'activa' ya existe")
                else:
                    print(f"  ⚠️  Error en 'activa': {e}")
            
            # Agregar campo simulacion_id a Empresa
            print("\n🏢 Migrando tabla 'empresas'...")
            
            try:
                db.session.execute(text("""
                    ALTER TABLE empresas 
                    ADD COLUMN simulacion_id INTEGER
                """))
                print("  ✅ Campo 'simulacion_id' agregado")
            except Exception as e:
                if "Duplicate column name" in str(e) or "duplicate column" in str(e):
                    print("  ⏭️  Campo 'simulacion_id' ya existe")
                else:
                    print(f"  ⚠️  Error en 'simulacion_id': {e}")
            
            # Agregar foreign key si no existe (esto puede fallar en algunos motores)
            try:
                db.session.execute(text("""
                    ALTER TABLE empresas 
                    ADD CONSTRAINT fk_empresas_simulacion 
                    FOREIGN KEY (simulacion_id) REFERENCES simulacion(id)
                """))
                print("  ✅ Foreign key agregada")
            except Exception as e:
                if "Duplicate foreign key" in str(e) or "already exists" in str(e):
                    print("  ⏭️  Foreign key ya existe")
                else:
                    print(f"  ⚠️  Foreign key no agregada (puede ser normal): {e}")
            
            # Actualizar simulación actual como activa
            print("\n🔄 Actualizando simulación actual...")
            try:
                db.session.execute(text("""
                    UPDATE simulacion SET activa = TRUE WHERE id = 1
                """))
                print("  ✅ Simulación actual marcada como activa")
            except Exception as e:
                print(f"  ⚠️  Error actualizando simulación: {e}")
            
            # Asignar todas las empresas a la simulación activa
            print("\n🔗 Asignando empresas a simulación activa...")
            try:
                db.session.execute(text("""
                    UPDATE empresas SET simulacion_id = 1 WHERE simulacion_id IS NULL
                """))
                print("  ✅ Empresas asignadas a simulación activa")
            except Exception as e:
                print(f"  ⚠️  Error asignando empresas: {e}")
            
            db.session.commit()
            print("\n✅ Migración completada exitosamente")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error durante la migración: {e}")
            raise

if __name__ == '__main__':
    migrar_base_datos()
