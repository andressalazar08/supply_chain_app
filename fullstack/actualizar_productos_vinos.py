"""
Script para actualizar los productos a 4 tipos de vino con 2 referencias cada uno
"""
from app import app
from extensions import db
from models import Producto

def actualizar_productos_vinos():
    with app.app_context():
        # Eliminar todos los productos existentes
        Producto.query.delete()
        
        # Definir los 4 tipos de vino con 2 referencias cada uno (750ml y 1L)
        productos = [
            # Sangre de la Vid (Vino Tinto Premium)
            {
                'codigo': 'SV-750',
                'nombre': 'Sangre de la Vid 750ml',
                'categoria': 'Vino Tinto',
                'costo_unitario': 45000,
                'precio_base': 75000,
                'precio_actual': 75000,
                'precio_sugerido': 75000,
                'demanda_promedio': 120,
                'desviacion_demanda': 25,
                'elasticidad_precio': 1.8,
                'tiempo_entrega': 3,
                'activo': True
            },
            {
                'codigo': 'SV-1L',
                'nombre': 'Sangre de la Vid 1L',
                'categoria': 'Vino Tinto',
                'costo_unitario': 58000,
                'precio_base': 95000,
                'precio_actual': 95000,
                'precio_sugerido': 95000,
                'demanda_promedio': 85,
                'desviacion_demanda': 20,
                'elasticidad_precio': 1.6,
                'tiempo_entrega': 3,
                'activo': True
            },
            
            # Elixir Dorado (Vino Blanco Premium)
            {
                'codigo': 'ED-750',
                'nombre': 'Elixir Dorado 750ml',
                'categoria': 'Vino Blanco',
                'costo_unitario': 42000,
                'precio_base': 70000,
                'precio_actual': 70000,
                'precio_sugerido': 70000,
                'demanda_promedio': 110,
                'desviacion_demanda': 22,
                'elasticidad_precio': 1.7,
                'tiempo_entrega': 3,
                'activo': True
            },
            {
                'codigo': 'ED-1L',
                'nombre': 'Elixir Dorado 1L',
                'categoria': 'Vino Blanco',
                'costo_unitario': 54000,
                'precio_base': 90000,
                'precio_actual': 90000,
                'precio_sugerido': 90000,
                'demanda_promedio': 75,
                'desviacion_demanda': 18,
                'elasticidad_precio': 1.5,
                'tiempo_entrega': 3,
                'activo': True
            },
            
            # Susurro Rosado (Vino Rosado)
            {
                'codigo': 'SR-750',
                'nombre': 'Susurro Rosado 750ml',
                'categoria': 'Vino Rosado',
                'costo_unitario': 38000,
                'precio_base': 62000,
                'precio_actual': 62000,
                'precio_sugerido': 62000,
                'demanda_promedio': 95,
                'desviacion_demanda': 20,
                'elasticidad_precio': 1.9,
                'tiempo_entrega': 3,
                'activo': True
            },
            {
                'codigo': 'SR-1L',
                'nombre': 'Susurro Rosado 1L',
                'categoria': 'Vino Rosado',
                'costo_unitario': 49000,
                'precio_base': 80000,
                'precio_actual': 80000,
                'precio_sugerido': 80000,
                'demanda_promedio': 65,
                'desviacion_demanda': 16,
                'elasticidad_precio': 1.7,
                'tiempo_entrega': 3,
                'activo': True
            },
            
            # Oceano Profundo (Vino Azul/Especial)
            {
                'codigo': 'OP-750',
                'nombre': 'Oceano Profundo 750ml',
                'categoria': 'Vino Especial',
                'costo_unitario': 52000,
                'precio_base': 85000,
                'precio_actual': 85000,
                'precio_sugerido': 85000,
                'demanda_promedio': 80,
                'desviacion_demanda': 18,
                'elasticidad_precio': 2.0,
                'tiempo_entrega': 4,
                'activo': True
            },
            {
                'codigo': 'OP-1L',
                'nombre': 'Oceano Profundo 1L',
                'categoria': 'Vino Especial',
                'costo_unitario': 68000,
                'precio_base': 110000,
                'precio_actual': 110000,
                'precio_sugerido': 110000,
                'demanda_promedio': 55,
                'desviacion_demanda': 14,
                'elasticidad_precio': 1.8,
                'tiempo_entrega': 4,
                'activo': True
            }
        ]
        
        # Crear los productos
        for prod_data in productos:
            producto = Producto(**prod_data)
            db.session.add(producto)
        
        db.session.commit()
        print(f"✅ {len(productos)} productos de vino creados exitosamente:")
        
        # Mostrar resumen
        for producto in Producto.query.all():
            print(f"  - {producto.codigo}: {producto.nombre} | Costo: ${producto.costo_unitario:,.0f} | Precio: ${producto.precio_actual:,.0f}")

if __name__ == '__main__':
    print("🍷 Actualizando catálogo de productos a vinos...")
    actualizar_productos_vinos()
    print("\n✅ Catálogo actualizado correctamente")
