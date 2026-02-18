"""
Script de prueba para verificar el sistema de nivel de servicio acumulativo
con demanda mínima garantizada
"""

from app import app, db
from models import Simulacion, Empresa, Venta, Metrica
from utils.procesamiento_dias import avanzar_simulacion

def mostrar_metricas_empresas():
    with app.app_context():
        try:
            print("="*80)
            print("📊 ANÁLISIS DE NIVEL DE SERVICIO ACUMULATIVO")
            print("="*80)
            
            simulacion = Simulacion.query.filter_by(activa=True).first()
            if not simulacion:
                print("❌ No hay simulación activa")
                return
            
            print(f"\n🎯 Simulación: {simulacion.nombre}")
            print(f"   Día actual: {simulacion.dia_actual}")
            
            empresas = Empresa.query.filter_by(simulacion_id=simulacion.id).all()
            
            for empresa in empresas:
                print(f"\n{'='*80}")
                print(f"🏢 {empresa.nombre}")
                print(f"{'='*80}")
                
                # Obtener todas las ventas históricas
                ventas_historicas = Venta.query.filter_by(
                    empresa_id=empresa.id
                ).order_by(Venta.dia_simulacion).all()
                
                if not ventas_historicas:
                    print("   ℹ️  No hay ventas registradas")
                    continue
                
                # Calcular acumulados
                total_solicitado = sum(v.cantidad_solicitada for v in ventas_historicas)
                total_vendido = sum(v.cantidad_vendida for v in ventas_historicas)
                total_perdido = sum(v.cantidad_perdida for v in ventas_historicas)
                
                nivel_servicio_acumulativo = (total_vendido / total_solicitado * 100) if total_solicitado > 0 else 100
                
                print(f"\n   📦 HISTORIAL COMPLETO (Días 1-{simulacion.dia_actual}):")
                print(f"      • Demanda total: {total_solicitado:,.0f} unidades")
                print(f"      • Vendido total: {total_vendido:,.0f} unidades")
                print(f"      • Perdido total: {total_perdido:,.0f} unidades")
                print(f"      • 📊 NIVEL SERVICIO ACUMULATIVO: {nivel_servicio_acumulativo:.1f}%")
                
                # Desglose por día (últimos 5 días)
                print(f"\n   📅 ÚLTIMOS 5 DÍAS:")
                print(f"      {'Día':<8} {'Solicitado':<12} {'Vendido':<12} {'Nivel Servicio':<15}")
                print(f"      {'-'*50}")
                
                dias_unicos = sorted(set(v.dia_simulacion for v in ventas_historicas))
                for dia in dias_unicos[-5:]:
                    ventas_dia = [v for v in ventas_historicas if v.dia_simulacion == dia]
                    sol_dia = sum(v.cantidad_solicitada for v in ventas_dia)
                    vend_dia = sum(v.cantidad_vendida for v in ventas_dia)
                    ns_dia = (vend_dia / sol_dia * 100) if sol_dia > 0 else 100
                    
                    print(f"      {dia:<8} {sol_dia:<12.0f} {vend_dia:<12.0f} {ns_dia:<15.1f}%")
                
                # Métrica del día actual
                metrica_actual = Metrica.query.filter_by(
                    empresa_id=empresa.id,
                    dia_simulacion=simulacion.dia_actual
                ).first()
                
                if metrica_actual:
                    print(f"\n   💰 MÉTRICA DÍA {simulacion.dia_actual}:")
                    print(f"      • Capital: ${empresa.capital_actual:,.0f}")
                    print(f"      • Ingresos: ${metrica_actual.ingresos:,.0f}")
                    print(f"      • Costos: ${metrica_actual.costos:,.0f}")
                    print(f"      • Utilidad: ${metrica_actual.utilidad:,.0f}")
                    print(f"      • Nivel Servicio (en métrica): {metrica_actual.nivel_servicio:.1f}%")
            
            print("\n" + "="*80)
            print("✅ INTERPRETACIÓN:")
            print("="*80)
            print("\n   El nivel de servicio ahora es ACUMULATIVO:")
            print("   • Si una empresa tiene 0 stock durante varios días → nivel baja")
            print("   • La demanda mínima garantizada es 60% de demanda promedio")
            print("   • Cada empresa DEBE poder atender esa demanda base")
            print("   • El nivel de servicio refleja el % de cumplimiento histórico")
            print("\n   📈 Empresas con buen stock → nivel servicio alto (>90%)")
            print("   📉 Empresas sin stock → nivel servicio bajo (<50%)")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    mostrar_metricas_empresas()
