"""
Script para inicializar inventarios de vinos para todas las empresas
"""
from app import app
from extensions import db
from models import Empresa, Producto, Inventario
import random

def inicializar_inventarios():
    with app.app_context():
        empresas = Empresa.query.all()
        productos = Producto.query.filter_by(activo=True).all()
        
        if not empresas:
            print("⚠️ No hay empresas registradas")
            return
        
        if not productos:
            print("⚠️ No hay productos registrados")
            return
        
        print(f"🍷 Inicializando inventarios para {len(empresas)} empresas y {len(productos)} productos...")
        
        for empresa in empresas:
            print(f"\n  Empresa: {empresa.nombre}")
            
            for producto in productos:
                # Verificar si ya existe inventario
                inventario_existente = Inventario.query.filter_by(
                    empresa_id=empresa.id,
                    producto_id=producto.id
                ).first()
                
                if inventario_existente:
                    print(f"    ⏭️ {producto.nombre} - Ya existe (Stock: {inventario_existente.cantidad_actual})")
                    continue
                
                # Crear inventario inicial con cantidades variables
                # Productos de 750ml tienen más stock que los de 1L
                if '750ml' in producto.nombre:
                    cantidad_inicial = random.randint(200, 400)
                else:  # 1L
                    cantidad_inicial = random.randint(100, 250)
                
                inventario = Inventario(
                    empresa_id=empresa.id,
                    producto_id=producto.id,
                    cantidad_actual=cantidad_inicial,
                    cantidad_reservada=0,
                    punto_reorden=50,
                    stock_seguridad=20,
                    costo_promedio=producto.costo_unitario
                )
                
                db.session.add(inventario)
                print(f"    ✅ {producto.nombre} - Stock inicial: {cantidad_inicial} und")
        
        db.session.commit()
        print("\n✅ Inventarios inicializados correctamente")

if __name__ == '__main__':
    inicializar_inventarios()
