"""
Script de prueba para el módulo de Compras
Genera requerimientos de compra desde Planeación para probar el flujo completo
"""

from app import app, db
from models import RequerimientoCompra, Producto, Empresa, Simulacion, Usuario, Inventario
from datetime import datetime

def crear_requerimientos_prueba():
    """Crea requerimientos de prueba para cada empresa"""
    with app.app_context():
        simulacion = Simulacion.query.first()
        if not simulacion:
            print("❌ No hay simulación activa")
            return
        
        empresas = Empresa.query.all()
        productos = Producto.query.filter_by(activo=True).all()
        
        if not empresas or not productos:
            print("❌ No hay empresas o productos en la base de datos")
            return
        
        print(f"📦 Creando requerimientos de compra para {len(empresas)} empresas...")
        print(f"📊 Día actual de simulación: {simulacion.dia_actual}")
        
        for empresa in empresas:
            print(f"\n🏢 Empresa: {empresa.nombre}")
            
            # Buscar usuario de planeación de esta empresa
            usuario_planeacion = Usuario.query.filter_by(
                empresa_id=empresa.id,
                rol='planeacion'
            ).first()
            
            if not usuario_planeacion:
                print(f"  ⚠️  No hay usuario de planeación, usando primer usuario")
                usuario_planeacion = Usuario.query.filter_by(empresa_id=empresa.id).first()
            
            if not usuario_planeacion:
                print(f"  ❌ No hay usuarios para esta empresa")
                continue
            
            for i, producto in enumerate(productos):
                # Obtener inventario actual
                inventario = Inventario.query.filter_by(
                    empresa_id=empresa.id,
                    producto_id=producto.id
                ).first()
                
                if not inventario:
                    print(f"  ⚠️  No hay inventario para {producto.nombre}, saltando...")
                    continue
                
                # Crear requerimiento con diferentes urgencias
                dias_adelante = [3, 5, 7, 10, 14][i % 5]  # Variedad de urgencias
                demanda_estimada = [50, 60, 40, 70, 55][i % 5]  # Demanda diaria estimada
                cantidad = [150, 200, 100, 250, 180][i % 5]  # Diferentes cantidades
                
                requerimiento = RequerimientoCompra(
                    empresa_id=empresa.id,
                    producto_id=producto.id,
                    usuario_planeacion_id=usuario_planeacion.id,
                    dia_generacion=simulacion.dia_actual,
                    dia_necesidad=simulacion.dia_actual + dias_adelante,
                    demanda_pronosticada=demanda_estimada,
                    stock_actual=inventario.cantidad_actual,
                    stock_seguridad=inventario.stock_seguridad,
                    lead_time=producto.tiempo_entrega,
                    cantidad_sugerida=cantidad,
                    estado='pendiente',
                    notas_planeacion=f"Pronóstico generado automáticamente. "
                                    f"Stock actual insuficiente para cubrir demanda esperada de {demanda_estimada} unid/día."
                )
                
                db.session.add(requerimiento)
                print(f"  ✓ {producto.nombre}: {cantidad} unidades para día {simulacion.dia_actual + dias_adelante} "
                      f"({dias_adelante} días) - Demanda: {demanda_estimada}/día")
        
        db.session.commit()
        print(f"\n✅ Requerimientos creados exitosamente!")
        print(f"📋 Total: {len(empresas) * len(productos)} requerimientos")
        
        # Mostrar resumen por empresa
        print("\n" + "="*60)
        print("RESUMEN DE REQUERIMIENTOS POR EMPRESA")
        print("="*60)
        for empresa in empresas:
            reqs = RequerimientoCompra.query.filter_by(
                empresa_id=empresa.id, 
                estado='pendiente'
            ).all()
            
            if reqs:
                print(f"\n🏢 {empresa.nombre}")
                print(f"   Requerimientos pendientes: {len(reqs)}")
                
                # Urgencias
                urgentes = sum(1 for r in reqs if (r.dia_necesidad - simulacion.dia_actual) <= 3)
                medios = sum(1 for r in reqs if 3 < (r.dia_necesidad - simulacion.dia_actual) <= 7)
                normales = sum(1 for r in reqs if (r.dia_necesidad - simulacion.dia_actual) > 7)
                
                print(f"   🔥 Urgentes (≤3 días): {urgentes}")
                print(f"   ⚡ Medios (4-7 días): {medios}")
                print(f"   📅 Normales (>7 días): {normales}")
                
                # Capital requerido
                capital_req = sum(r.cantidad_sugerida * r.producto.costo_unitario for r in reqs)
                print(f"   💰 Capital requerido: ${capital_req:,.0f}")
                print(f"   💵 Capital disponible: ${empresa.capital_actual:,.0f}")

def limpiar_requerimientos():
    """Limpia todos los requerimientos existentes"""
    with app.app_context():
        count = RequerimientoCompra.query.delete()
        db.session.commit()
        print(f"🗑️  {count} requerimientos eliminados")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--limpiar':
        limpiar_requerimientos()
    else:
        crear_requerimientos_prueba()
        print("\n" + "="*60)
        print("🎯 INSTRUCCIONES DE PRUEBA")
        print("="*60)
        print("1. Inicia sesión con usuario de rol 'compras':")
        print("   Email: compras1@empresa1.com")
        print("   Contraseña: password123")
        print("")
        print("2. Navega a Dashboard de Compras")
        print("   - Verás productos priorizados por cobertura")
        print("   - Requerimientos de Planeación pendientes")
        print("   - Métricas de capital")
        print("")
        print("3. Ve a 'Requerimientos'")
        print("   - Tab Pendientes: requerimientos por procesar")
        print("   - Podrás crear órdenes o marcar como revisados")
        print("")
        print("4. Prueba crear una orden:")
        print("   - Click en 'Crear Orden' en un requerimiento")
        print("   - Ajusta cantidad si necesario")
        print("   - Confirma (validará capital disponible)")
        print("")
        print("5. Verifica en tab 'Procesados':")
        print("   - Requerimientos convertidos a órdenes")
        print("   - Vinculación con ID de orden")
        print("="*60)
