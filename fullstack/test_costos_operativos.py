"""
Script de prueba para verificar el sistema de costos operativos automáticos
"""

from app import app, db
from models import Simulacion, Empresa, Inventario, Producto, Metrica, Venta
from utils.procesamiento_dias import avanzar_simulacion

def mostrar_estado_empresas():
    """Muestra el estado actual de todas las empresas"""
    with app.app_context():
        simulacion = Simulacion.query.filter_by(activa=True).first()
        
        if not simulacion:
            print("❌ No hay simulación activa")
            return
        
        print(f"\n{'='*80}")
        print(f"📊 SIMULACIÓN: {simulacion.nombre}")
        print(f"   Día: {simulacion.dia_actual} | Estado: {simulacion.estado}")
        print(f"{'='*80}\n")
        
        empresas = Empresa.query.filter_by(simulacion_id=simulacion.id).all()
        
        for empresa in empresas:
            print(f"🏢 {empresa.nombre}")
            print(f"   💰 Capital: ${empresa.capital_actual:,.0f}")
            
            # Inventario total
            inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
            total_unidades = sum(inv.cantidad_actual for inv in inventarios)
            valor_inventario = sum(inv.cantidad_actual * (inv.costo_promedio or 0) for inv in inventarios)
            
            print(f"   📦 Inventario: {total_unidades:.0f} unidades (Valor: ${valor_inventario:,.0f})")
            
            # Métrica del último día
            metrica = Metrica.query.filter_by(
                empresa_id=empresa.id,
                dia_simulacion=simulacion.dia_actual
            ).first()
            
            if metrica:
                print(f"   📈 Día {simulacion.dia_actual}:")
                print(f"      • Ingresos: ${metrica.ingresos:,.0f}")
                print(f"      • Costos: ${metrica.costos:,.0f}")
                print(f"      • Utilidad: ${metrica.utilidad:,.0f}")
                print(f"      • Nivel Servicio: {metrica.nivel_servicio:.1f}%")
            
            # Ventas del día
            ventas = Venta.query.filter_by(
                empresa_id=empresa.id,
                dia_simulacion=simulacion.dia_actual
            ).all()
            
            if ventas:
                total_vendido = sum(v.cantidad_vendida for v in ventas)
                total_solicitado = sum(v.cantidad_solicitada for v in ventas)
                perdidas = total_solicitado - total_vendido
                
                print(f"   🛒 Ventas: {total_vendido:.0f} de {total_solicitado:.0f} solicitadas")
                if perdidas > 0:
                    print(f"      ⚠️ Ventas perdidas: {perdidas:.0f} unidades")
            
            print()

def test_costos_sin_actividad():
    """
    Prueba: Avanzar 1 día SIN tomar decisiones.
    Debe aplicar:
    - $800k costos fijos
    - 0.3% mantenimiento de inventario
    - 0 penalización (no hay ventas perdidas porque no hay demanda asignada sin stock)
    """
    with app.app_context():
        print("\n" + "="*80)
        print("🧪 PRUEBA: Costos operativos SIN actividad")
        print("="*80)
        
        # Estado antes
        print("\n📸 ANTES de avanzar día:")
        mostrar_estado_empresas()
        
        # Avanzar simulación
        print("\n⏩ Avanzando simulación...")
        success, mensaje, resumen = avanzar_simulacion()
        
        if success:
            print(f"✅ {mensaje}")
            if resumen:
                print(f"\n📋 Resumen:")
                print(f"   - Empresas procesadas: {resumen['empresas_procesadas']}")
                print(f"   - Total ventas: {resumen['total_ventas']}")
                print(f"   - Compras recibidas: {resumen['total_compras_recibidas']}")
        else:
            print(f"❌ {mensaje}")
            return
        
        # Estado después
        print("\n📸 DESPUÉS de avanzar día:")
        mostrar_estado_empresas()
        
        # Análisis de costos
        print("\n💡 ANÁLISIS DE COSTOS:")
        print("   Con inventario de ~960 unidades totales (8 productos × 120/80)")
        print("   Valor aproximado: ~960 × $45k promedio = $43,200,000")
        print("   Costos esperados por empresa:")
        print("   • Fijos: $800,000")
        print("   • Mantenimiento (0.3%): ~$129,600")
        print("   • TOTAL: ~$929,600 por día")
        print("\n   Capital debería bajar de $18,000,000 a ~$17,070,400")

if __name__ == '__main__':
    test_costos_sin_actividad()
