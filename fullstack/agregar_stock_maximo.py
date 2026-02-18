"""
Script para agregar campo stock_maximo a productos y asignar valores realistas
basados en la demanda promedio de cada producto.

Stock máximo = demanda_promedio × 7 días de cobertura
"""

from app import app, db
from models import Producto
from sqlalchemy import text

def agregar_stock_maximo():
    with app.app_context():
        try:
            print("="*80)
            print("📊 AGREGANDO CAMPO STOCK_MAXIMO A PRODUCTOS")
            print("="*80)
            
            # 1. Agregar columna si no existe
            print("\n1️⃣ Verificando si la columna existe...")
            try:
                # Intentar agregar la columna
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE productos ADD COLUMN stock_maximo FLOAT DEFAULT 500'))
                    conn.commit()
                print("   ✅ Columna stock_maximo agregada exitosamente")
            except Exception as e:
                if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                    print("   ℹ️  La columna stock_maximo ya existe")
                else:
                    print(f"   ⚠️  Error al agregar columna: {e}")
            
            # 2. Asignar valores realistas basados en demanda
            print("\n2️⃣ Asignando valores de stock_maximo por producto...")
            productos = Producto.query.filter_by(activo=True).all()
            
            print(f"\n   Productos encontrados: {len(productos)}")
            print(f"   {'Producto':<30} {'Demanda/día':<15} {'Stock Máximo':<15}")
            print(f"   {'-'*60}")
            
            for producto in productos:
                # Calcular stock máximo = 7 días de demanda promedio
                # Esto permite una semana de cobertura máxima
                stock_maximo = int(producto.demanda_promedio * 7)
                
                producto.stock_maximo = stock_maximo
                
                print(f"   {producto.nombre:<30} {producto.demanda_promedio:<15.0f} {stock_maximo:<15}")
            
            # 3. Guardar cambios
            db.session.commit()
            
            print("\n" + "="*80)
            print("✅ PROCESO COMPLETADO")
            print("="*80)
            print("\n📋 RESUMEN DEL SISTEMA DE SOBRESTOCK:")
            print("\n   • Stock Máximo = Demanda Promedio × 7 días")
            print("   • Inventario > Stock Máximo = SOBRESTOCK")
            print("   • Penalización: 0.5% adicional sobre el valor del exceso")
            print("   • Costo total por sobrestock: 0.3% normal + 0.5% exceso = 0.8%")
            print("\n   Ejemplo:")
            print("   - Producto con demanda de 100 unidades/día")
            print("   - Stock máximo: 700 unidades")
            print("   - Si tiene 900 unidades:")
            print("     * Exceso: 200 unidades")
            print("     * Costo normal (900 × $50k × 0.3%): $135,000")
            print("     * Costo sobrestock (200 × $50k × 0.5%): $50,000")
            print("     * TOTAL DIARIO: $185,000")
            print("\n   🎯 Esto incentiva a mantener niveles óptimos de inventario")
            print("="*80)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    agregar_stock_maximo()
