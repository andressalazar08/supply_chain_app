"""
Funciones para cálculos de inventario y gestión de compras
"""

from typing import Dict, List
from models import Inventario, Venta, Compra


def calcular_consumo_diario(ventas: List, dias: int = 7) -> float:
    """
    Calcula el consumo diario promedio basado en ventas históricas
    
    Args:
        ventas: Lista de objetos Venta
        dias: Número de días a considerar
    
    Returns:
        Consumo promedio por día
    """
    if not ventas:
        return 0.0
    
    total_vendido = sum([v.cantidad_vendida for v in ventas])
    dias_unicos = len(set([v.dia_simulacion for v in ventas]))
    
    if dias_unicos == 0:
        return 0.0
    
    return total_vendido / dias_unicos


def calcular_dias_cobertura(stock_actual: float, consumo_diario: float) -> float:
    """
    Calcula los días de cobertura de inventario
    
    Args:
        stock_actual: Cantidad actual en inventario
        consumo_diario: Consumo promedio por día
    
    Returns:
        Días de cobertura (cuántos días durará el inventario)
    """
    if consumo_diario <= 0:
        return float('inf')  # Stock infinito si no hay consumo
    
    return stock_actual / consumo_diario


def calcular_punto_reorden_economico(
    demanda_anual: float,
    costo_pedido: float,
    costo_almacenamiento: float,
    lead_time: int
) -> Dict[str, float]:
    """
    Calcula el punto de reorden y cantidad económica de pedido (EOQ)
    
    Args:
        demanda_anual: Demanda anual del producto
        costo_pedido: Costo de realizar un pedido
        costo_almacenamiento: Costo de almacenar una unidad por año
        lead_time: Tiempo de entrega en días
    
    Returns:
        Diccionario con EOQ y punto de reorden
    """
    import math
    
    # EOQ = sqrt((2 × D × S) / H)
    # D = Demanda anual
    # S = Costo de pedido
    # H = Costo de almacenamiento
    
    if costo_almacenamiento <= 0:
        costo_almacenamiento = 1  # Evitar división por cero
    
    eoq = math.sqrt((2 * demanda_anual * costo_pedido) / costo_almacenamiento)
    
    # Punto de reorden = Demanda durante lead time
    demanda_diaria = demanda_anual / 365
    punto_reorden = demanda_diaria * lead_time
    
    return {
        'eoq': round(eoq, 2),
        'punto_reorden': round(punto_reorden, 2),
        'demanda_diaria': round(demanda_diaria, 2)
    }


def analizar_inventario(inventario: Inventario, ventas_recientes: List) -> Dict:
    """
    Análisis completo de un inventario
    
    Args:
        inventario: Objeto Inventario
        ventas_recientes: Lista de ventas del producto
    
    Returns:
        Diccionario con métricas de análisis
    """
    consumo_diario = calcular_consumo_diario(ventas_recientes)
    dias_cobertura = calcular_dias_cobertura(inventario.cantidad_actual, consumo_diario)
    
    # Determinar estado del inventario
    if dias_cobertura < 3:
        estado = 'critico'
        alerta = 'Inventario crítico - Ordenar urgentemente'
    elif dias_cobertura < 7:
        estado = 'bajo'
        alerta = 'Inventario bajo - Considerar ordenar'
    elif dias_cobertura < 14:
        estado = 'normal'
        alerta = 'Nivel adecuado'
    else:
        estado = 'alto'
        alerta = 'Inventario alto - Evaluar sobrestock'
    
    # Calcular si está por debajo del punto de reorden
    requiere_pedido = inventario.cantidad_actual < inventario.punto_reorden
    
    return {
        'consumo_diario': round(consumo_diario, 2),
        'dias_cobertura': round(dias_cobertura, 1) if dias_cobertura != float('inf') else 999,
        'estado': estado,
        'alerta': alerta,
        'requiere_pedido': requiere_pedido,
        'cantidad_faltante': max(0, inventario.punto_reorden - inventario.cantidad_actual),
        'stock_disponible': inventario.cantidad_actual - inventario.cantidad_reservada
    }


def calcular_costo_total_compra(cantidad: float, precio_unitario: float, 
                                 descuento_pct: float = 0) -> Dict[str, float]:
    """
    Calcula el costo total de una compra con descuentos
    
    Args:
        cantidad: Cantidad a comprar
        precio_unitario: Precio por unidad
        descuento_pct: Porcentaje de descuento (0-100)
    
    Returns:
        Diccionario con desglose de costos
    """
    subtotal = cantidad * precio_unitario
    descuento = subtotal * (descuento_pct / 100)
    total = subtotal - descuento
    
    return {
        'cantidad': cantidad,
        'precio_unitario': precio_unitario,
        'subtotal': round(subtotal, 2),
        'descuento_pct': descuento_pct,
        'descuento_monto': round(descuento, 2),
        'total': round(total, 2)
    }


def validar_capacidad_compra(capital_disponible: float, costo_compra: float,
                             pedidos_pendientes: List[Compra]) -> Dict:
    """
    Valida si hay capital suficiente para realizar una compra
    
    Args:
        capital_disponible: Capital actual de la empresa
        costo_compra: Costo de la compra a realizar
        pedidos_pendientes: Lista de compras en tránsito
    
    Returns:
        Diccionario con validación y sugerencias
    """
    # Calcular capital comprometido en pedidos pendientes
    capital_comprometido = sum([c.costo_total for c in pedidos_pendientes if c.estado == 'en_transito'])
    
    # Capital efectivamente disponible
    capital_libre = capital_disponible - capital_comprometido
    
    # Validar
    puede_comprar = capital_libre >= costo_compra
    
    # Calcular porcentaje de utilización
    pct_uso = (costo_compra / capital_disponible * 100) if capital_disponible > 0 else 0
    
    resultado = {
        'puede_comprar': puede_comprar,
        'capital_disponible': capital_disponible,
        'capital_comprometido': capital_comprometido,
        'capital_libre': round(capital_libre, 2),
        'costo_compra': costo_compra,
        'deficit': max(0, costo_compra - capital_libre),
        'pct_uso_capital': round(pct_uso, 1)
    }
    
    # Sugerencias
    if not puede_comprar:
        resultado['sugerencia'] = f'Reducir cantidad o esperar entrega de pedidos pendientes (${capital_comprometido:,.2f})'
    elif pct_uso > 80:
        resultado['sugerencia'] = 'Alto uso de capital - Evaluar prioridades'
    elif pct_uso > 50:
        resultado['sugerencia'] = 'Uso moderado de capital'
    else:
        resultado['sugerencia'] = 'Capital disponible suficiente'
    
    return resultado


def priorizar_productos_compra(productos_data: List[Dict]) -> List[Dict]:
    """
    Prioriza productos para compra basado en días de cobertura
    
    Args:
        productos_data: Lista de diccionarios con datos de productos
                        Debe incluir: {producto_id, dias_cobertura, stock_actual}
    
    Returns:
        Lista ordenada por prioridad (menor cobertura = mayor prioridad)
    """
    # Ordenar por días de cobertura (ascendente)
    productos_ordenados = sorted(productos_data, key=lambda x: x.get('dias_cobertura', 999))
    
    # Asignar nivel de prioridad
    for i, prod in enumerate(productos_ordenados):
        if prod['dias_cobertura'] < 3:
            prod['prioridad'] = 'Alta'
            prod['prioridad_num'] = 1
        elif prod['dias_cobertura'] < 7:
            prod['prioridad'] = 'Media'
            prod['prioridad_num'] = 2
        else:
            prod['prioridad'] = 'Baja'
            prod['prioridad_num'] = 3
    
    return productos_ordenados
