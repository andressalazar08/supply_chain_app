"""
Prueba avanzando un día para verificar que la demanda mínima se genera
"""

from app import app, db
from models import Simulacion, Empresa, Inventario, Producto
from utils.procesamiento_dias import avanzar_simulacion

def test_avance_con_demanda_minima():
    with app.app_context():
        try:
            print("="*80)
            print("🧪 PRUEBA: AVANCE CON DEMANDA MÍNIMA GARANTIZADA")
            print("="*80)
            
            simulacion = Simulacion.query.filter_by(activa=True).first()
            empresa = Empresa.query.filter_by(simulacion_id=simulacion.id).first()
            
            print(f"\n📊 ANTES - Día {simulacion.dia_actual}")
            print(f"   Empresa: {empresa.nombre}")
            print(f"   Capital: ${empresa.capital_actual:,.0f}")
            
            # Verificar inventarios
            inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
            total_stock = sum(inv.cantidad_actual for inv in inventarios)
            print(f"   Stock total: {total_stock:.0f} unidades")
            
            if total_stock > 0:
                print("\n   ✅ Hay stock - debería recibir y procesar ventas")
            else:
                print("\n   ⚠️  SIN STOCK - recibirá demanda pero no podrá vender")
                print("      (esto hará que el nivel de servicio BAJE)")
            
            # Avanzar simulación
            print(f"\n⏩ Avanzando simulación...")
            success, mensaje, resumen = avanzar_simulacion()
            
            if not success:
                print(f"❌ Error: {mensaje}")
                return
            
            print(f"✅ {mensaje}")
            
            # Verificar resultado
            db.session.refresh(simulacion)
            db.session.refresh(empresa)
            
            print(f"\n📊 DESPUÉS - Día {simulacion.dia_actual}")
            print(f"   Capital: ${empresa.capital_actual:,.0f}")
            
            # Verificar ventas del día
            from models import Venta
            ventas_dia = Venta.query.filter_by(
                empresa_id=empresa.id,
                dia_simulacion=simulacion.dia_actual
            ).all()
            
            total_solicitado = sum(v.cantidad_solicitada for v in ventas_dia)
            total_vendido = sum(v.cantidad_vendida for v in ventas_dia)
            
            print(f"\n   🛒 VENTAS DEL DÍA:")
            print(f"      Demanda recibida: {total_solicitado:.0f} unidades")
            print(f"      Vendido: {total_vendido:.0f} unidades")
            
            if total_solicitado > 0:
                ns_dia = (total_vendido / total_solicitado) * 100
                print(f"      Nivel servicio del día: {ns_dia:.1f}%")
                
                if total_vendido < total_solicitado:
                    print(f"      ⚠️  No pudo atender: {total_solicitado - total_vendido:.0f} unidades")
            
            # Calcular nivel servicio acumulativo
            todas_ventas = Venta.query.filter_by(empresa_id=empresa.id).all()
            total_hist_sol = sum(v.cantidad_solicitada for v in todas_ventas)
            total_hist_vend = sum(v.cantidad_vendida for v in todas_ventas)
            
            ns_acumulativo = (total_hist_vend / total_hist_sol * 100) if total_hist_sol > 0 else 100
            
            print(f"\n   📊 NIVEL SERVICIO ACUMULATIVO: {ns_acumulativo:.1f}%")
            print(f"      Total histórico solicitado: {total_hist_sol:.0f}")
            print(f"      Total histórico vendido: {total_hist_vend:.0f}")
            
            print("\n" + "="*80)
            print("✅ VERIFICACIÓN:")
            print("="*80)
            
            if total_solicitado > 0:
                print(f"\n   ✅ El sistema generó demanda mínima: {total_solicitado:.0f} unidades")
                
                if total_vendido == 0 and total_stock == 0:
                    print(f"   ✅ Sin stock → no vendió → nivel de servicio bajará")
                elif total_vendido < total_solicitado:
                    print(f"   ⚠️  Stock insuficiente → nivel de servicio bajó")
                elif total_vendido == total_solicitado:
                    print(f"   ✅ Atendió toda la demanda → nivel de servicio se mantiene")
            else:
                print(f"\n   ❌ NO se generó demanda mínima - verificar código")
            
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_avance_con_demanda_minima()
