"""
Script de prueba para verificar el sistema de penalización por sobrestock
"""

from app import app, db
from models import Simulacion, Empresa, Inventario, Producto
from utils.procesamiento_dias import calcular_costos_operativos

def test_penalizacion_sobrestock():
    with app.app_context():
        try:
            print("="*80)
            print("🧪 PRUEBA: PENALIZACIÓN POR SOBRESTOCK")
            print("="*80)
            
            simulacion = Simulacion.query.filter_by(activa=True).first()
            if not simulacion:
                print("❌ No hay simulación activa")
                return
            
            empresa = Empresa.query.filter_by(simulacion_id=simulacion.id).first()
            if not empresa:
                print("❌ No hay empresas en la simulación")
                return
            
            print(f"\n📊 Simulación: {simulacion.nombre}")
            print(f"🏢 Empresa: {empresa.nombre}")
            print(f"💰 Capital actual: ${empresa.capital_actual:,.0f}")
            
            # Mostrar inventarios actuales
            print("\n📦 INVENTARIOS ACTUALES:")
            inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
            
            total_inventario = 0
            total_sobrestock = 0
            
            for inv in inventarios:
                producto = inv.producto
                tiene_sobrestock = inv.cantidad_actual > producto.stock_maximo
                
                status = "⚠️ SOBRESTOCK" if tiene_sobrestock else "✅ Normal"
                
                print(f"\n   {producto.nombre}")
                print(f"      Cantidad actual: {inv.cantidad_actual:.0f}")
                print(f"      Stock máximo: {producto.stock_maximo:.0f}")
                print(f"      Estado: {status}")
                
                if tiene_sobrestock:
                    exceso = inv.cantidad_actual - producto.stock_maximo
                    print(f"      Exceso: {exceso:.0f} unidades")
                    total_sobrestock += exceso
                
                total_inventario += inv.cantidad_actual
            
            print(f"\n   TOTAL: {total_inventario:.0f} unidades")
            if total_sobrestock > 0:
                print(f"   SOBRESTOCK TOTAL: {total_sobrestock:.0f} unidades")
            
            # Calcular costos operativos
            print("\n💸 CALCULANDO COSTOS OPERATIVOS...")
            costos = calcular_costos_operativos(simulacion, empresa)
            
            print(f"\n📋 DESGLOSE DE COSTOS:")
            print(f"   • Costos fijos: ${costos['costos_fijos']:,.0f}")
            print(f"   • Mantenimiento base (0.3%): ${costos['costos_mantenimiento']:,.0f}")
            
            if costos['penalizacion_sobrestock'] > 0:
                print(f"   • ⚠️ PENALIZACIÓN SOBRESTOCK (0.5%): ${costos['penalizacion_sobrestock']:,.0f}")
            else:
                print(f"   • Penalización sobrestock: $0 (sin excesos)")
            
            print(f"   • Penalización ventas perdidas: ${costos['penalizacion_ventas_perdidas']:,.0f}")
            print(f"   {'-'*50}")
            print(f"   💰 COSTO TOTAL: ${costos['costo_total']:,.0f}")
            
            print(f"\n   Valor inventario: ${costos['valor_inventario']:,.0f}")
            
            # Análisis
            print("\n" + "="*80)
            print("📊 ANÁLISIS:")
            print("="*80)
            
            if total_sobrestock > 0:
                print(f"\n⚠️  Esta empresa tiene SOBRESTOCK en {total_sobrestock:.0f} unidades")
                print(f"   Está pagando un costo adicional de ${costos['penalizacion_sobrestock']:,.0f}/día")
                print(f"   Esto representa un {(costos['penalizacion_sobrestock']/costos['costo_total']*100):.1f}% del costo total")
                print("\n💡 RECOMENDACIÓN:")
                print("   • Reducir compras hasta normalizar niveles")
                print("   • Optimizar inventario dentro de los límites establecidos")
            else:
                print("\n✅ Esta empresa mantiene niveles óptimos de inventario")
                print("   No hay penalizaciones por sobrestock")
            
            print("\n" + "="*80)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_penalizacion_sobrestock()
