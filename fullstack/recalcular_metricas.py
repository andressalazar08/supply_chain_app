#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script: Recalcular métricas con la fórmula correcta del Fill Rate
Fill Rate = Promedio de (Cantidad Aprobada por región / Demanda del Mercado por región) × 100
"""

from app import app, db
from models import Simulacion, Empresa, Metrica, Decision, DemandaMercadoDiaria

# Regiones y variantes
REGIONES_CANONICAS = [
    'Andina',
    'Caribe',
    'Pacífica',
    'Orinoquía',
    'Amazonía',
]

REGION_VARIANTES = {
    'Andina': ['Andina'],
    'Caribe': ['Caribe'],
    'Pacífica': ['Pacífica', 'Pacifica', 'Pac\u00edfica'],
    'Orinoquía': ['Orinoquía', 'Orinoquia', 'Orinoqu\u00eda'],
    'Amazonía': ['Amazonía', 'Amazonia', 'Amazon\u00eda'],
}

def variantes_region(region):
    """Retorna alias válidos de una región para tolerar datos legados mal codificados."""
    return REGION_VARIANTES.get(region, [region])

def calcular_fill_rate_promedio(empresa_id, simulacion, dia_fin):
    """Calcula el Fill Rate promedio de las 5 regiones hasta dia_fin"""
    dia_inicio = 1
    
    # Obtener todas las decisiones de aprobación para esta empresa hasta dia_fin
    decisiones = Decision.query.filter(
        Decision.empresa_id == empresa_id,
        Decision.tipo_decision == 'ventas_aprobacion_diaria',
        Decision.semana_simulacion >= dia_inicio,
        Decision.semana_simulacion <= dia_fin,
    ).order_by(Decision.semana_simulacion.asc(), Decision.created_at.asc()).all()

    # Construir mapa de aprobaciones por (región, día)
    aprobaciones_por_region_dia = {}
    for dec in decisiones:
        if not dec.datos_decision:
            continue
        dia = int(dec.semana_simulacion)
        for item in dec.datos_decision.get('aprobaciones', []):
            region = (item.get('region') or '').strip()
            cantidad = int(item.get('cantidad_aprobada', 0) or 0)
            if region not in REGIONES_CANONICAS:
                continue
            aprobaciones_por_region_dia.setdefault((region, dia), 0)
            aprobaciones_por_region_dia[(region, dia)] += max(0, cantidad)

    fill_rates = []
    for region in REGIONES_CANONICAS:
        # Obtener demanda del mercado por día para esta región
        demanda_rango = db.session.query(
            DemandaMercadoDiaria.dia_simulacion,
            db.func.coalesce(db.func.sum(DemandaMercadoDiaria.demanda_base), 0).label('demanda_total')
        ).filter(
            DemandaMercadoDiaria.simulacion_id == simulacion.id,
            DemandaMercadoDiaria.dia_simulacion >= dia_inicio,
            DemandaMercadoDiaria.dia_simulacion <= dia_fin,
            DemandaMercadoDiaria.region.in_(variantes_region(region)),
        ).group_by(DemandaMercadoDiaria.dia_simulacion).all()

        demanda_por_dia = {
            int(row.dia_simulacion): int(round(float(row.demanda_total or 0)))
            for row in demanda_rango
        }

        # Calcular totales acumulados por región
        demanda_total = sum(demanda_por_dia.values())
        aprobada_total = sum(
            int(aprobaciones_por_region_dia.get((region, dia), 0))
            for dia in range(dia_inicio, dia_fin + 1)
        )
        
        # Fill rate por región
        fill_rate = (aprobada_total / demanda_total * 100) if demanda_total > 0 else 100.0
        fill_rates.append(fill_rate)

    # Retornar el promedio
    return round(sum(fill_rates) / len(fill_rates), 1) if fill_rates else 100.0

def recalcular_metricas():
    """Recalcula las métricas con la fórmula correcta del Fill Rate"""
    with app.app_context():
        simulacion = Simulacion.query.filter_by(activa=True).first()
        if not simulacion:
            print("❌ No hay simulación activa")
            return
        
        empresas = Empresa.query.filter_by(simulacion_id=simulacion.id).all()
        
        print(f"\n🔄 RECALCULANDO FILL RATE - Simulación Día {simulacion.dia_actual}")
        print("=" * 80)
        
        for empresa in empresas:
            print(f"\n🏢 Empresa: {empresa.nombre}")
            
            # Obtener todas las métricas existentes
            metricas = Metrica.query.filter_by(
                empresa_id=empresa.id
            ).order_by(Metrica.semana_simulacion).all()
            
            for metrica in metricas:
                # Calcular Fill Rate promedio hasta ese día
                fill_rate_nuevo = calcular_fill_rate_promedio(empresa.id, simulacion, metrica.semana_simulacion)
                
                fill_rate_antiguo = metrica.nivel_servicio
                
                # Actualizar si es diferente
                if abs(fill_rate_nuevo - fill_rate_antiguo) > 0.1:
                    print(f"   Día {metrica.semana_simulacion}:")
                    print(f"      {fill_rate_antiguo:.1f}% → {fill_rate_nuevo:.1f}%")
                    metrica.nivel_servicio = fill_rate_nuevo
                    db.session.add(metrica)
            
            db.session.commit()
            print(f"   ✅ Actualizado")
        
        print("\n" + "=" * 80)
        print("✅ Recálculo completado")

if __name__ == '__main__':
    recalcular_metricas()
