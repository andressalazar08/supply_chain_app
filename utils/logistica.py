"""
Utilidades para el módulo de Logística
Funciones para gestión de recepciones, despachos y distribución regional
"""

from typing import Dict, List, Any
from datetime import datetime


def calcular_tiempo_entrega_region(region: str) -> int:
    """
    Calcula el tiempo de entrega en días según la región de Colombia
    
    Args:
        region: Nombre de la región (Andina, Caribe, Pacífica, Orinoquía, Amazonía)
    
    Returns:
        Días de tránsito
    """
    tiempos_entrega = {
        'Andina': 1,      # Región central - más rápido
        'Caribe': 2,      # Costa norte
        'Pacífica': 2,    # Costa oeste
        'Orinoquía': 3,   # Llanos orientales
        'Amazonía': 4     # Región más alejada
    }
    
    return tiempos_entrega.get(region, 2)


def procesar_recepcion_compra(compra, inventario) -> Dict[str, Any]:
    """
    Procesa la recepción de una orden de compra
    
    Args:
        compra: Objeto Compra a recibir
        inventario: Objeto Inventario a actualizar
    
    Returns:
        Diccionario con resultado de la operación
    """
    cantidad_anterior = inventario.cantidad_actual
    inventario.cantidad_actual += compra.cantidad
    
    # Actualizar costo promedio ponderado
    valor_anterior = cantidad_anterior * inventario.costo_promedio
    valor_nueva_compra = compra.cantidad * compra.costo_unitario
    cantidad_total = cantidad_anterior + compra.cantidad
    
    if cantidad_total > 0:
        inventario.costo_promedio = (valor_anterior + valor_nueva_compra) / cantidad_total
    
    return {
        'cantidad_recibida': compra.cantidad,
        'cantidad_anterior': cantidad_anterior,
        'cantidad_nueva': inventario.cantidad_actual,
        'costo_unitario': compra.costo_unitario,
        'costo_promedio': inventario.costo_promedio,
        'valor_recepcion': valor_nueva_compra
    }


def calcular_stock_disponible_despacho(inventario, ordenes_pendientes=None) -> float:
    """
    Calcula el stock disponible para despacho
    
    Args:
        inventario: Objeto Inventario
        ordenes_pendientes: Lista de órdenes de despacho pendientes
    
    Returns:
        Cantidad disponible para despachar
    """
    stock_disponible = inventario.cantidad_actual - inventario.cantidad_reservada
    
    # Restar cantidades en órdenes de despacho pendientes
    if ordenes_pendientes:
        for orden in ordenes_pendientes:
            stock_disponible -= orden.cantidad
    
    return max(0, stock_disponible)


def validar_despacho_region(inventario, cantidad_solicitada: float, 
                            stock_seguridad: float = None) -> Dict[str, Any]:
    """
    Valida si se puede despachar una cantidad a una región
    
    Args:
        inventario: Objeto Inventario
        cantidad_solicitada: Cantidad que se quiere despachar
        stock_seguridad: Stock de seguridad mínimo (opcional)
    
    Returns:
        Diccionario con validación y recomendación
    """
    stock_seguridad = stock_seguridad or inventario.stock_seguridad
    stock_disponible = inventario.cantidad_actual - inventario.cantidad_reservada
    
    puede_despachar = cantidad_solicitada <= stock_disponible
    
    # Verificar si el despacho dejaría menos del stock de seguridad
    stock_resultante = stock_disponible - cantidad_solicitada
    alerta_stock_bajo = stock_resultante < stock_seguridad
    
    recomendacion = None
    if not puede_despachar:
        recomendacion = f"Stock insuficiente. Disponible: {stock_disponible:.0f}"
    elif alerta_stock_bajo:
        recomendacion = f"Advertencia: Stock resultante ({stock_resultante:.0f}) por debajo del stock de seguridad ({stock_seguridad:.0f})"
    
    return {
        'puede_despachar': puede_despachar,
        'stock_disponible': stock_disponible,
        'stock_resultante': stock_resultante,
        'alerta_stock_bajo': alerta_stock_bajo,
        'recomendacion': recomendacion
    }


def distribuir_stock_por_demanda(stock_disponible: float, demandas_regionales: Dict[str, float]) -> Dict[str, float]:
    """
    Distribuye stock disponible proporcionalmente a la demanda de cada región
    
    Args:
        stock_disponible: Stock total disponible para distribuir
        demandas_regionales: Dict con región -> demanda
    
    Returns:
        Dict con región -> cantidad asignada
    """
    demanda_total = sum(demandas_regionales.values())
    
    if demanda_total == 0:
        # Distribuir equitativamente
        num_regiones = len(demandas_regionales)
        cantidad_por_region = stock_disponible / num_regiones if num_regiones > 0 else 0
        return {region: cantidad_por_region for region in demandas_regionales.keys()}
    
    # Distribuir proporcionalmente
    distribucion = {}
    for region, demanda in demandas_regionales.items():
        proporcion = demanda / demanda_total
        distribucion[region] = stock_disponible * proporcion
    
    return distribucion


def analizar_cobertura_regional(inventario_regional: Dict[str, float], 
                                 ventas_regionales: Dict[str, List]) -> Dict[str, Any]:
    """
    Analiza la cobertura de inventario por región
    
    Args:
        inventario_regional: Dict con región -> stock actual
        ventas_regionales: Dict con región -> lista de ventas recientes
    
    Returns:
        Análisis de cobertura por región
    """
    analisis = {}
    
    for region, stock in inventario_regional.items():
        ventas = ventas_regionales.get(region, [])
        
        if not ventas:
            analisis[region] = {
                'stock': stock,
                'demanda_diaria': 0,
                'dias_cobertura': float('inf'),
                'estado': 'sin_datos'
            }
            continue
        
        # Calcular demanda diaria promedio
        total_vendido = sum(v.cantidad_vendida for v in ventas)
        dias_historico = len(set(v.dia_simulacion for v in ventas))
        demanda_diaria = total_vendido / dias_historico if dias_historico > 0 else 0
        
        # Calcular días de cobertura
        dias_cobertura = stock / demanda_diaria if demanda_diaria > 0 else float('inf')
        
        # Determinar estado
        if dias_cobertura <= 3:
            estado = 'critico'
        elif dias_cobertura <= 7:
            estado = 'bajo'
        elif dias_cobertura <= 14:
            estado = 'normal'
        else:
            estado = 'alto'
        
        analisis[region] = {
            'stock': stock,
            'demanda_diaria': demanda_diaria,
            'dias_cobertura': dias_cobertura,
            'estado': estado,
            'total_vendido': total_vendido,
            'dias_historico': dias_historico
        }
    
    return analisis


def priorizar_despachos_pendientes(despachos_pendientes: List) -> List:
    """
    Prioriza despachos pendientes por urgencia
    
    Args:
        despachos_pendientes: Lista de objetos de despacho
    
    Returns:
        Lista ordenada por prioridad
    """
    def calcular_prioridad(despacho):
        # Prioridad basada en:
        # 1. Tiempo de espera (mayor tiempo = mayor prioridad)
        # 2. Región (regiones lejanas tienen prioridad)
        # 3. Cantidad (órdenes grandes tienen prioridad)
        
        peso_tiempo = 10  # Más peso al tiempo
        peso_region = calcular_tiempo_entrega_region(despacho.region) * 5
        peso_cantidad = despacho.cantidad / 100
        
        return peso_tiempo + peso_region + peso_cantidad
    
    return sorted(despachos_pendientes, key=calcular_prioridad, reverse=True)


def generar_alertas_logistica(inventario, ventas_recientes: List, 
                               ordenes_compra_transito: List) -> List[Dict[str, str]]:
    """
    Genera alertas logísticas basadas en estado del inventario
    
    Args:
        inventario: Objeto Inventario
        ventas_recientes: Lista de ventas recientes
        ordenes_compra_transito: Lista de compras en tránsito
    
    Returns:
        Lista de alertas con tipo y mensaje
    """
    alertas = []
    
    # Alerta de stock bajo
    if inventario.cantidad_actual <= inventario.stock_seguridad:
        alertas.append({
            'tipo': 'danger',
            'icono': 'exclamation-triangle',
            'mensaje': f'Stock crítico: {inventario.cantidad_actual:.0f} unidades (Stock seguridad: {inventario.stock_seguridad:.0f})'
        })
    elif inventario.cantidad_actual <= inventario.punto_reorden:
        alertas.append({
            'tipo': 'warning',
            'icono': 'exclamation-circle',
            'mensaje': f'Stock bajo punto de reorden: {inventario.cantidad_actual:.0f} unidades'
        })
    
    # Alerta de stock reservado alto
    porcentaje_reservado = (inventario.cantidad_reservada / inventario.cantidad_actual * 100) if inventario.cantidad_actual > 0 else 0
    if porcentaje_reservado > 50:
        alertas.append({
            'tipo': 'info',
            'icono': 'lock',
            'mensaje': f'{porcentaje_reservado:.0f}% del stock está reservado ({inventario.cantidad_reservada:.0f} unidades)'
        })
    
    # Alerta de compras en tránsito
    if ordenes_compra_transito:
        total_en_transito = sum(o.cantidad for o in ordenes_compra_transito)
        alertas.append({
            'tipo': 'success',
            'icono': 'truck',
            'mensaje': f'{len(ordenes_compra_transito)} orden(es) en tránsito: {total_en_transito:.0f} unidades próximamente'
        })
    
    return alertas


def calcular_eficiencia_despacho(despachos_realizados: List, 
                                  tiempo_promedio_esperado: int = 2) -> Dict[str, Any]:
    """
    Calcula métricas de eficiencia de despachos
    
    Args:
        despachos_realizados: Lista de despachos completados
        tiempo_promedio_esperado: Tiempo esperado en días
    
    Returns:
        Métricas de eficiencia
    """
    if not despachos_realizados:
        return {
            'total_despachos': 0,
            'tiempo_promedio': 0,
            'entregas_a_tiempo': 0,
            'entregas_tarde': 0,
            'porcentaje_a_tiempo': 0
        }
    
    tiempos = []
    entregas_a_tiempo = 0
    
    for despacho in despachos_realizados:
        if hasattr(despacho, 'dia_entrega') and hasattr(despacho, 'dia_despacho'):
            tiempo = despacho.dia_entrega - despacho.dia_despacho
            tiempos.append(tiempo)
            
            tiempo_esperado_region = calcular_tiempo_entrega_region(despacho.region)
            if tiempo <= tiempo_esperado_region:
                entregas_a_tiempo += 1
    
    tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
    porcentaje_a_tiempo = (entregas_a_tiempo / len(despachos_realizados) * 100) if despachos_realizados else 0
    
    return {
        'total_despachos': len(despachos_realizados),
        'tiempo_promedio': tiempo_promedio,
        'entregas_a_tiempo': entregas_a_tiempo,
        'entregas_tarde': len(despachos_realizados) - entregas_a_tiempo,
        'porcentaje_a_tiempo': porcentaje_a_tiempo
    }


def sugerir_redistribucion(inventarios_regionales: Dict[str, float], 
                           demandas_regionales: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Sugiere redistribuciones de inventario entre regiones
    
    Args:
        inventarios_regionales: Dict con región -> stock
        demandas_regionales: Dict con región -> demanda diaria
    
    Returns:
        Lista de sugerencias de redistribución
    """
    sugerencias = []
    
    # Calcular días de cobertura por región
    coberturas = {}
    for region, stock in inventarios_regionales.items():
        demanda = demandas_regionales.get(region, 0)
        cobertura = stock / demanda if demanda > 0 else float('inf')
        coberturas[region] = {
            'stock': stock,
            'demanda': demanda,
            'cobertura': cobertura
        }
    
    # Identificar regiones con exceso y déficit
    regiones_exceso = {r: c for r, c in coberturas.items() if c['cobertura'] > 14 and c['stock'] > 0}
    regiones_deficit = {r: c for r, c in coberturas.items() if c['cobertura'] < 7}
    
    # Generar sugerencias
    for region_deficit, datos_deficit in regiones_deficit.items():
        for region_exceso, datos_exceso in regiones_exceso.items():
            if region_deficit != region_exceso:
                # Calcular cantidad a transferir
                stock_exceso = datos_exceso['stock'] - (datos_exceso['demanda'] * 10)  # Mantener 10 días
                cantidad_faltante = (7 * datos_deficit['demanda']) - datos_deficit['stock']  # Para llegar a 7 días
                
                cantidad_transferir = min(stock_exceso, cantidad_faltante)
                
                if cantidad_transferir > 0:
                    sugerencias.append({
                        'origen': region_exceso,
                        'destino': region_deficit,
                        'cantidad': cantidad_transferir,
                        'cobertura_origen': datos_exceso['cobertura'],
                        'cobertura_destino': datos_deficit['cobertura'],
                        'tiempo_transito': calcular_tiempo_entrega_region(region_deficit)
                    })
    
    return sugerencias
