"""
Parámetros iniciales canónicos para el arranque de la simulación.

Este módulo centraliza constantes para evitar desalineaciones entre:
- reinicio de simulación,
- calibración de demanda,
- generación de demanda central,
- órdenes iniciales de abastecimiento.
"""

from __future__ import annotations

# Configuración de flota de transporte (vehículos propios)
FLOTA_VEHICULOS = {
    'V_350_1': {'capacidad': 350, 'costo': 700_000.0, 'grupo': '350'},
    'V_350_2': {'capacidad': 350, 'costo': 700_000.0, 'grupo': '350'},
    'V_350_3': {'capacidad': 350, 'costo': 700_000.0, 'grupo': '350'},
    'V_400_1': {'capacidad': 400, 'costo': 800_000.0, 'grupo': '400'},
    'V_400_2': {'capacidad': 400, 'costo': 800_000.0, 'grupo': '400'},
    'V_400_3': {'capacidad': 400, 'costo': 800_000.0, 'grupo': '400'},
    'V_400_4': {'capacidad': 400, 'costo': 800_000.0, 'grupo': '400'},
    'V_400_5': {'capacidad': 400, 'costo': 800_000.0, 'grupo': '400'},
    'V_400_6': {'capacidad': 400, 'costo': 800_000.0, 'grupo': '400'},
    'V_400_7': {'capacidad': 400, 'costo': 800_000.0, 'grupo': '400'},
    'V_400_8': {'capacidad': 400, 'costo': 800_000.0, 'grupo': '400'},
    'V_450_1': {'capacidad': 450, 'costo': 900_000.0, 'grupo': '450'},
    'V_450_2': {'capacidad': 450, 'costo': 900_000.0, 'grupo': '450'},
    'V_450_3': {'capacidad': 450, 'costo': 900_000.0, 'grupo': '450'},
    'V_450_4': {'capacidad': 450, 'costo': 900_000.0, 'grupo': '450'},
    'V_500_1': {'capacidad': 500, 'costo': 1_000_000.0, 'grupo': '500'},
    'V_500_2': {'capacidad': 500, 'costo': 1_000_000.0, 'grupo': '500'},
    'V_500_3': {'capacidad': 500, 'costo': 1_000_000.0, 'grupo': '500'},
    'V_500_4': {'capacidad': 500, 'costo': 1_000_000.0, 'grupo': '500'},
    'V_EXTERNO': {'capacidad': None, 'costo': 3_000.0, 'grupo': 'externo', 'por_unidad': True},
}

# Ciclos de reutilización por región (días hasta poder reasignar el vehículo)
CICLOS_REGION = {
    'Andina': 2,
    'Caribe': 4,
    'Pacífica': 4,
    'Orinoquía': 5,
    'Amazonía': 6,
}


# Horizonte base de juego
DURACION_SIMULACION_SEMANAS = 8
DIAS_HISTORICO_DEMANDA = 30

# Datos iniciales configurables por profesor
CAPITAL_INICIAL_EMPRESA_DEFAULT = 50_000_000.0
INVENTARIO_INICIAL_750_DEFAULT = 120
INVENTARIO_INICIAL_1L_DEFAULT = 80

# Calibración de inventario-demanda
REGIONES_MERCADO = 5
DIAS_COBERTURA_INICIAL = 5
DIAS_REORDEN = 3
DIAS_STOCK_SEGURIDAD = 1
FACTOR_DESVIACION_DEMANDA = 0.20
STOCK_MAXIMO_PRODUCTO = 1500

# Arranque de compras automáticas para no penalizar días iniciales
DIAS_ARRANQUE_PEDIDOS = (1, 2, 3)
COBERTURA_ORDENES_ARRANQUE_DIAS = 2.5
MAX_UNIDADES_ORDENES_ARRANQUE = 1600

# Perfil objetivo de llegada para los primeros 3 días (por empresa y por día).
# Suma diaria objetivo: 1599 unidades (capacidad máxima 1600).
DEMANDA_DIARIA_MEDIA_ARRANQUE = {
    'SV-1L': 213,
    'SV-750': 208,
    'ED-750': 212,
    'ED-1L': 195,
    'SR-750': 184,
    'SR-1L': 193,
    'OP-750': 204,
    'OP-1L': 190,
}

# Catálogo económico base por producto (código -> costos/precios de arranque)
CATALOGO_PRODUCTOS_BASE = {
    'SV-750': {'precio_base': 48_000.0, 'costo_unitario': 20_000.0},
    'SV-1L': {'precio_base': 55_000.0, 'costo_unitario': 25_000.0},
    'ED-750': {'precio_base': 38_000.0, 'costo_unitario': 17_000.0},
    'ED-1L': {'precio_base': 45_000.0, 'costo_unitario': 20_000.0},
    'SR-750': {'precio_base': 35_000.0, 'costo_unitario': 15_000.0},
    'SR-1L': {'precio_base': 42_000.0, 'costo_unitario': 18_000.0},
    'OP-750': {'precio_base': 40_000.0, 'costo_unitario': 18_000.0},
    'OP-1L': {'precio_base': 48_000.0, 'costo_unitario': 22_000.0},
}


def es_presentacion_750(producto) -> bool:
    """Retorna True si el producto es referencia 750 ml."""
    codigo = (getattr(producto, 'codigo', '') or '').upper()
    nombre = (getattr(producto, 'nombre', '') or '').upper()
    return '750' in codigo or '750' in nombre


def inventario_inicial_por_producto(producto, inv_750ml: int, inv_1l: int) -> int:
    """Obtiene el inventario inicial aplicable por tipo de presentación."""
    return int(inv_750ml) if es_presentacion_750(producto) else int(inv_1l)


def calcular_parametros_demanda(inv_inicial: int) -> dict:
    """Calcula demanda, desviación y parámetros de reorden desde inventario inicial."""
    nueva_demanda = max(1, round(inv_inicial * 7 / (DIAS_COBERTURA_INICIAL * REGIONES_MERCADO)))
    nueva_desviacion = max(1, round(nueva_demanda * FACTOR_DESVIACION_DEMANDA))

    demanda_diaria_empresa = nueva_demanda / 7.0 * REGIONES_MERCADO
    punto_reorden = max(1, round(demanda_diaria_empresa * DIAS_REORDEN))
    stock_seguridad = max(1, round(demanda_diaria_empresa * DIAS_STOCK_SEGURIDAD))

    return {
        'demanda_promedio': nueva_demanda,
        'desviacion_demanda': nueva_desviacion,
        'demanda_diaria_empresa': demanda_diaria_empresa,
        'punto_reorden': punto_reorden,
        'stock_seguridad': stock_seguridad,
        'stock_maximo': STOCK_MAXIMO_PRODUCTO,
    }
