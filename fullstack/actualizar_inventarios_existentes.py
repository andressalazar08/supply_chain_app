"""
Script para actualizar inventarios existentes con cantidades iniciales
"""
from app import app
from extensions import db
from models import Inventario, Producto
import random

def actualizar_inventarios():
    with app.app_context():
        inventarios = Inventario.query.all()
        
        print(f"🍷 Actualizando {len(inventarios)} inventarios...")
        
        for inv in inventarios:
            producto = Producto.query.get(inv.producto_id)
            
            if not producto:
                continue
            
            # Solo actualizar si tiene stock 0
            if inv.cantidad_actual == 0:
                # Productos de 750ml tienen más stock que los de 1L
                if '750ml' in producto.nombre:
                    inv.cantidad_actual = random.randint(200, 400)
                else:  # 1L
                    inv.cantidad_actual = random.randint(100, 250)
                
                inv.costo_promedio = producto.costo_unitario
                inv.punto_reorden = 50
                inv.stock_seguridad = 20
                
                print(f"  ✅ {producto.nombre} - Nuevo stock: {inv.cantidad_actual} und")
        
        db.session.commit()
        print("\n✅ Todos los inventarios actualizados correctamente")

if __name__ == '__main__':
    actualizar_inventarios()
