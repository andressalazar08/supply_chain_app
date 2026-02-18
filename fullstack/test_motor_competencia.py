"""
Script de prueba para verificar el motor de competencia
Ajusta precios de diferentes empresas y simula un día
"""
from app import app
from extensions import db
from models import Empresa, Producto, Simulacion, Inventario
from utils.procesamiento_dias import procesar_ventas_dia

def probar_motor_competencia():
    with app.app_context():
        # Obtener simulación y empresas
        simulacion = Simulacion.query.first()
        empresas = Empresa.query.all()
        
        if not simulacion or len(empresas) < 2:
            print("⚠️ Necesitas al menos 2 empresas y una simulación activa")
            return
        
        # Obtener primer producto para prueba
        producto = Producto.query.first()
        
        if not producto:
            print("⚠️ No hay productos disponibles")
            return
        
        print(f"🍷 Prueba de Motor de Competencia")
        print(f"Simulación Día: {simulacion.dia_actual}")
        print(f"Producto de prueba: {producto.nombre}")
        print(f"Precio base: ${producto.precio_actual:,.0f}\n")
        
        # Configurar precios diferentes para cada empresa
        print("📊 Configurando escenario de competencia:")
        
        # Empresa 1: Precio muy alto
        print(f"\n  {empresas[0].nombre}:")
        print(f"    - Precio: ${producto.precio_actual * 1.6:,.0f} (60% sobre base)")
        print(f"    - Estrategia: Precio premium")
        
        if len(empresas) > 1:
            # Empresa 2: Precio competitivo
            print(f"\n  {empresas[1].nombre}:")
            print(f"    - Precio: ${producto.precio_actual:,.0f} (precio base)")
            print(f"    - Estrategia: Precio competitivo")
        
        if len(empresas) > 2:
            # Empresa 3: Precio bajo
            print(f"\n  {empresas[2].nombre}:")
            print(f"    - Precio: ${producto.precio_actual * 0.8:,.0f} (20% bajo base)")
            print(f"    - Estrategia: Precio agresivo")
        
        print("\n" + "="*60)
        print("🎯 Procesando ventas del día con motor de competencia...")
        print("="*60 + "\n")
        
        # Procesar ventas para cada empresa
        for empresa in empresas:
            print(f"📦 {empresa.nombre}:")
            ventas = procesar_ventas_dia(simulacion, empresa)
            
            # Mostrar resultados
            total_vendido = sum([v.cantidad_vendida for v in ventas if v.producto_id == producto.id])
            total_perdido = sum([v.cantidad_perdida for v in ventas if v.producto_id == producto.id])
            total_ingresos = sum([v.ingreso_total for v in ventas if v.producto_id == producto.id])
            
            print(f"  ✅ Ventas realizadas: {total_vendido:.0f} unidades")
            print(f"  ❌ Ventas perdidas: {total_perdido:.0f} unidades")
            print(f"  💰 Ingresos: ${total_ingresos:,.0f}")
            
            # Mostrar inventario restante
            inv = Inventario.query.filter_by(
                empresa_id=empresa.id,
                producto_id=producto.id
            ).first()
            
            if inv:
                print(f"  📊 Stock restante: {inv.cantidad_actual:.0f} unidades\n")
        
        print("\n✅ Prueba completada - Revisa los resultados arriba")
        print("💡 Las empresas con precios competitivos deberían tener más ventas")

if __name__ == '__main__':
    probar_motor_competencia()
