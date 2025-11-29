"""
Script de prueba para el sistema de procesamiento de días
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Simulacion, Empresa, Venta, Compra, Metrica
from utils.procesamiento_dias import avanzar_simulacion, obtener_resumen_simulacion

def imprimir_separador():
    print("\n" + "="*60 + "\n")

def test_avanzar_dia():
    """Prueba el avance de un día simulado"""
    
    with app.app_context():
        print("🧪 PRUEBA DE PROCESAMIENTO DE DÍAS")
        imprimir_separador()
        
        # Obtener simulación
        simulacion = Simulacion.query.first()
        print(f"📅 Estado actual:")
        print(f"   Día: {simulacion.dia_actual}")
        print(f"   Estado: {simulacion.estado}")
        
        if simulacion.estado != 'en_curso':
            print("\n⚠️  Cambiando estado a 'en_curso'...")
            simulacion.estado = 'en_curso'
            db.session.commit()
        
        imprimir_separador()
        
        # Obtener datos antes del avance
        empresas = Empresa.query.filter_by(activa=True).all()
        print("💼 Estado de empresas ANTES del avance:")
        for empresa in empresas:
            ventas_anteriores = Venta.query.filter_by(
                empresa_id=empresa.id,
                dia_simulacion=simulacion.dia_actual - 1
            ).count()
            
            print(f"\n   {empresa.nombre}:")
            print(f"      Capital: ${empresa.capital_actual:,.2f}")
            print(f"      Ventas día anterior: {ventas_anteriores}")
        
        imprimir_separador()
        
        # Avanzar simulación
        print("🚀 AVANZANDO AL SIGUIENTE DÍA...")
        success, mensaje, resumen = avanzar_simulacion()
        
        if success:
            print(f"\n✅ {mensaje}")
            
            if resumen:
                print(f"\n📊 RESUMEN DEL PROCESAMIENTO:")
                print(f"   • Día procesado: {resumen['dia']}")
                print(f"   • Empresas procesadas: {resumen['empresas_procesadas']}")
                print(f"   • Total ventas generadas: {resumen['total_ventas']}")
                print(f"   • Compras recibidas: {resumen['total_compras_recibidas']}")
                print(f"   • Despachos entregados: {resumen['total_despachos_entregados']}")
                
                if resumen['alertas']:
                    print(f"\n⚠️  ALERTAS:")
                    for empresa_alertas in resumen['alertas']:
                        print(f"\n   {empresa_alertas['empresa']}:")
                        for alerta in empresa_alertas['alertas'][:3]:  # Mostrar solo las primeras 3
                            icono = "🔴" if alerta['tipo'] == 'critico' else "⚠️" if alerta['tipo'] == 'advertencia' else "ℹ️"
                            print(f"      {icono} {alerta['mensaje']}")
        else:
            print(f"\n❌ ERROR: {mensaje}")
            return
        
        imprimir_separador()
        
        # Verificar cambios en base de datos
        simulacion = Simulacion.query.first()
        print("📅 Estado actual DESPUÉS del avance:")
        print(f"   Día: {simulacion.dia_actual}")
        
        print("\n💼 Estado de empresas DESPUÉS del avance:")
        for empresa in empresas:
            ventas_dia = Venta.query.filter_by(
                empresa_id=empresa.id,
                dia_simulacion=simulacion.dia_actual - 1
            ).all()
            
            metrica = Metrica.query.filter_by(
                empresa_id=empresa.id,
                dia_simulacion=simulacion.dia_actual - 1
            ).first()
            
            total_vendido = sum(v.cantidad_vendida for v in ventas_dia)
            total_solicitado = sum(v.cantidad_solicitada for v in ventas_dia)
            
            print(f"\n   {empresa.nombre}:")
            print(f"      Capital: ${empresa.capital_actual:,.2f}")
            print(f"      Ventas procesadas: {len(ventas_dia)}")
            print(f"      Unidades vendidas: {total_vendido}/{total_solicitado}")
            
            if metrica:
                print(f"      Ingresos: ${metrica.ingresos:,.2f}")
                print(f"      Utilidad: ${metrica.utilidad:,.2f}")
                print(f"      Nivel de servicio: {metrica.nivel_servicio:.1f}%")
        
        imprimir_separador()
        
        # Obtener resumen general
        print("📈 RESUMEN GENERAL DE LA SIMULACIÓN:")
        resumen_general = obtener_resumen_simulacion(simulacion)
        
        for empresa_data in resumen_general['empresas']:
            print(f"\n   {empresa_data['nombre']}:")
            print(f"      Capital actual: ${empresa_data['capital_actual']:,.2f}")
            print(f"      Ingresos totales: ${empresa_data['ingresos_totales']:,.2f}")
            print(f"      Utilidad total: ${empresa_data['utilidad_total']:,.2f}")
            print(f"      Nivel servicio promedio: {empresa_data['nivel_servicio_promedio']:.1f}%")
        
        imprimir_separador()
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
        imprimir_separador()


def test_multiples_dias(n_dias=3):
    """Prueba el avance de múltiples días consecutivos"""
    
    with app.app_context():
        print(f"🧪 PRUEBA DE {n_dias} DÍAS CONSECUTIVOS")
        imprimir_separador()
        
        for i in range(n_dias):
            print(f"\n🔄 Procesando día {i+1}/{n_dias}...")
            success, mensaje, resumen = avanzar_simulacion()
            
            if success:
                print(f"   ✅ {mensaje}")
                if resumen:
                    print(f"   📊 {resumen['total_ventas']} ventas, {resumen['total_compras_recibidas']} compras")
            else:
                print(f"   ❌ {mensaje}")
                break
        
        imprimir_separador()
        
        # Mostrar estado final
        simulacion = Simulacion.query.first()
        print(f"📅 Día final: {simulacion.dia_actual}")
        
        empresas = Empresa.query.filter_by(activa=True).all()
        print("\n💼 Capitales finales:")
        for empresa in empresas:
            print(f"   {empresa.nombre}: ${empresa.capital_actual:,.2f}")
        
        imprimir_separador()


if __name__ == '__main__':
    print("\n" + "🎮 SISTEMA DE PROCESAMIENTO DE DÍAS - PRUEBAS".center(60) + "\n")
    
    # Menú de opciones
    print("Selecciona una opción:")
    print("1. Avanzar 1 día (con detalle completo)")
    print("2. Avanzar 3 días consecutivos")
    print("3. Avanzar 7 días consecutivos (semana)")
    
    opcion = input("\nOpción: ").strip()
    
    if opcion == '1':
        test_avanzar_dia()
    elif opcion == '2':
        test_multiples_dias(3)
    elif opcion == '3':
        test_multiples_dias(7)
    else:
        print("❌ Opción no válida")
