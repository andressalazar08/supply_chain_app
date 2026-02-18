"""
Script para ajustar valores iniciales de la simulación activa:
- Inventarios: 120 (750ml) / 80 (1L)
- Capital: $18,000,000
"""

from app import app, db
from models import Simulacion, Empresa, Inventario, Producto

def actualizar_valores_iniciales():
    with app.app_context():
        try:
            # Obtener simulación activa
            simulacion = Simulacion.query.filter_by(activa=True).first()
            
            if not simulacion:
                print("❌ No hay simulación activa")
                return
            
            print(f"📊 Actualizando valores iniciales de: {simulacion.nombre}")
            print(f"   Día actual: {simulacion.dia_actual}")
            
            # 1. ACTUALIZAR CAPITAL DE EMPRESAS
            empresas = Empresa.query.filter_by(simulacion_id=simulacion.id).all()
            print(f"\n💰 Actualizando capital de {len(empresas)} empresas...")
            
            for empresa in empresas:
                capital_anterior = empresa.capital_actual
                empresa.capital_actual = 18000000  # $18M
                print(f"   {empresa.nombre}: ${capital_anterior:,.0f} → $18,000,000")
            
            # 2. ACTUALIZAR INVENTARIOS
            productos = Producto.query.filter_by(activo=True).all()
            print(f"\n📦 Actualizando inventarios para {len(empresas)} empresas...")
            
            inventarios_actualizados = 0
            for empresa in empresas:
                for producto in productos:
                    inventario = Inventario.query.filter_by(
                        empresa_id=empresa.id,
                        producto_id=producto.id
                    ).first()
                    
                    if inventario:
                        # Determinar cantidad según tipo de producto
                        if '750ml' in producto.nombre:
                            cantidad_nueva = 120
                        else:  # 1L
                            cantidad_nueva = 80
                        
                        cantidad_anterior = inventario.cantidad_actual
                        inventario.cantidad_actual = cantidad_nueva
                        
                        # Ajustar punto de reorden y stock de seguridad
                        inventario.punto_reorden = 50
                        inventario.stock_seguridad = 20
                        
                        if cantidad_anterior != cantidad_nueva:
                            inventarios_actualizados += 1
                            print(f"   {empresa.nombre} - {producto.nombre}: {cantidad_anterior:.0f} → {cantidad_nueva}")
            
            # GUARDAR CAMBIOS
            db.session.commit()
            
            print(f"\n✅ Actualización completada:")
            print(f"   - {len(empresas)} empresas con capital de $18,000,000")
            print(f"   - {inventarios_actualizados} inventarios ajustados")
            print(f"   - 750ml: 120 unidades")
            print(f"   - 1L: 80 unidades")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    actualizar_valores_iniciales()
