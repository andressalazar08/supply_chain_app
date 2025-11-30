"""
Utilidades para gestión de disrupciones y escenarios del profesor
"""

# Catálogo de disrupciones predefinidas
DISRUPCIONES_CATALOGO = {
    'retraso_proveedor': {
        'nombre': 'Retraso en Proveedores',
        'icono': 'fa-truck-loading',
        'severidades': {
            'baja': {
                'nombre': 'Retraso Menor - Tráfico',
                'descripcion': 'Congestión vehicular causa retrasos menores en entregas',
                'dias_adicionales': 2,
                'duracion_dias': 3
            },
            'media': {
                'nombre': 'Retraso Moderado - Vía en Mantenimiento',
                'descripcion': 'Obras en la vía principal requieren desvíos',
                'dias_adicionales': 5,
                'duracion_dias': 7
            },
            'alta': {
                'nombre': 'Retraso Severo - Derrumbe',
                'descripcion': 'Derrumbe en vía Bogotá-Medellín bloquea transporte',
                'dias_adicionales': 10,
                'duracion_dias': 10
            },
            'critica': {
                'nombre': 'Bloqueo Total - Paro Nacional',
                'descripcion': 'Paro de transportadores paraliza entregas',
                'dias_adicionales': 15,
                'duracion_dias': 14
            }
        }
    },
    
    'aumento_demanda': {
        'nombre': 'Aumento en Demanda',
        'icono': 'fa-chart-line',
        'severidades': {
            'baja': {
                'nombre': 'Incremento Estacional',
                'descripcion': 'Temporada vacacional aumenta ventas moderadamente',
                'multiplicador': 1.3,
                'duracion_dias': 5
            },
            'media': {
                'nombre': 'Campaña Publicitaria Exitosa',
                'descripcion': 'Marketing digital genera aumento sostenido',
                'multiplicador': 1.8,
                'duracion_dias': 10
            },
            'alta': {
                'nombre': 'Día de la Madre / Padre',
                'descripcion': 'Fecha especial duplica demanda en ciertas regiones',
                'multiplicador': 2.5,
                'duracion_dias': 7
            },
            'critica': {
                'nombre': 'Navidad - Temporada Alta',
                'descripcion': 'Demanda navideña triplica ventas normales',
                'multiplicador': 3.5,
                'duracion_dias': 15
            }
        }
    },
    
    'reduccion_capacidad': {
        'nombre': 'Reducción de Capacidad Logística',
        'icono': 'fa-warehouse',
        'severidades': {
            'baja': {
                'nombre': 'Falta de Personal',
                'descripcion': 'Ausentismo reduce capacidad operativa',
                'reduccion_porcentaje': 15,
                'duracion_dias': 5
            },
            'media': {
                'nombre': 'Daño en Equipo',
                'descripcion': 'Falla en montacargas reduce velocidad',
                'reduccion_porcentaje': 30,
                'duracion_dias': 7
            },
            'alta': {
                'nombre': 'Incendio en Bodega',
                'descripcion': 'Sección del almacén fuera de servicio',
                'reduccion_porcentaje': 50,
                'duracion_dias': 12
            },
            'critica': {
                'nombre': 'Cierre Temporal Centro de Distribución',
                'descripcion': 'Problemas sanitarios cierran instalación',
                'reduccion_porcentaje': 75,
                'duracion_dias': 10
            }
        }
    },
    
    'aumento_costos': {
        'nombre': 'Aumento en Costos de Compra',
        'icono': 'fa-dollar-sign',
        'severidades': {
            'baja': {
                'nombre': 'Inflación Controlada',
                'descripcion': 'Aumento gradual de precios de insumos',
                'incremento_porcentaje': 10,
                'duracion_dias': 10
            },
            'media': {
                'nombre': 'Aumento en Transporte',
                'descripcion': 'Incremento en precio del combustible',
                'incremento_porcentaje': 20,
                'duracion_dias': 15
            },
            'alta': {
                'nombre': 'Devaluación del Peso',
                'descripcion': 'Dólar sube afectando importaciones',
                'incremento_porcentaje': 35,
                'duracion_dias': 20
            },
            'critica': {
                'nombre': 'Crisis de Insumos',
                'descripcion': 'Escasez global duplica costos',
                'incremento_porcentaje': 60,
                'duracion_dias': 25
            }
        }
    },
    
    'region_bloqueada': {
        'nombre': 'Región sin Cobertura',
        'icono': 'fa-map-marked-alt',
        'severidades': {
            'baja': {
                'nombre': 'Lluvia Torrencial',
                'descripcion': 'Inundaciones temporales dificultan acceso',
                'dias_bloqueo': 2,
                'duracion_dias': 3
            },
            'media': {
                'nombre': 'Deslizamiento de Tierra',
                'descripcion': 'Vía principal cerrada por seguridad',
                'dias_bloqueo': 5,
                'duracion_dias': 8
            },
            'alta': {
                'nombre': 'Bloqueos Viales',
                'descripcion': 'Protestas bloquean acceso a la región',
                'dias_bloqueo': 7,
                'duracion_dias': 10
            },
            'critica': {
                'nombre': 'Desastre Natural',
                'descripcion': 'Emergencia regional impide distribución',
                'dias_bloqueo': 12,
                'duracion_dias': 15
            }
        }
    }
}

# Regiones disponibles
REGIONES_COLOMBIA = ['Andina', 'Caribe', 'Pacífica', 'Orinoquía', 'Amazonía']


def obtener_disrupciones_disponibles():
    """Retorna lista de disrupciones con sus configuraciones"""
    return DISRUPCIONES_CATALOGO


def crear_disrupcion_parametros(tipo_disrupcion, severidad, productos=None, regiones=None, razon=None):
    """
    Crea los parámetros para una disrupción específica
    
    Args:
        tipo_disrupcion: Tipo de disrupción del catálogo
        severidad: baja, media, alta, critica
        productos: Lista de IDs de productos afectados (None = todos)
        regiones: Lista de regiones afectadas (None = todas)
        razon: Razón personalizada (None = usar del catálogo)
    
    Returns:
        dict con parámetros configurados
    """
    if tipo_disrupcion not in DISRUPCIONES_CATALOGO:
        raise ValueError(f"Tipo de disrupción no válido: {tipo_disrupcion}")
    
    config = DISRUPCIONES_CATALOGO[tipo_disrupcion]['severidades'].get(severidad)
    if not config:
        raise ValueError(f"Severidad no válida: {severidad}")
    
    parametros = {}
    descripcion = razon if razon else config['descripcion']
    duracion = config.get('duracion_dias', 7)
    
    if tipo_disrupcion == 'retraso_proveedor':
        parametros = {
            'dias_adicionales': config['dias_adicionales'],
            'productos_afectados': productos if productos else [],  # [] = todos
            'razon': descripcion
        }
        
    elif tipo_disrupcion == 'aumento_demanda':
        parametros = {
            'multiplicador': config['multiplicador'],
            'regiones': regiones if regiones else REGIONES_COLOMBIA,
            'productos': productos if productos else [],
            'razon': descripcion
        }
        
    elif tipo_disrupcion == 'reduccion_capacidad':
        parametros = {
            'reduccion_porcentaje': config['reduccion_porcentaje'],
            'regiones': regiones if regiones else REGIONES_COLOMBIA,
            'razon': descripcion
        }
        
    elif tipo_disrupcion == 'aumento_costos':
        parametros = {
            'incremento_porcentaje': config['incremento_porcentaje'],
            'productos': productos if productos else [],
            'razon': descripcion
        }
        
    elif tipo_disrupcion == 'region_bloqueada':
        parametros = {
            'regiones': regiones if regiones else [],
            'dias_bloqueo': config['dias_bloqueo'],
            'razon': descripcion
        }
    
    return {
        'nombre': config['nombre'],
        'descripcion': descripcion,
        'parametros': parametros,
        'duracion_dias': duracion,
        'icono': DISRUPCIONES_CATALOGO[tipo_disrupcion]['icono']
    }


def calcular_impacto_lead_time(producto_id, dia_actual, disrupciones_activas):
    """
    Calcula el lead time ajustado considerando disrupciones activas
    
    Args:
        producto_id: ID del producto
        dia_actual: Día actual de la simulación
        disrupciones_activas: Lista de disrupciones activas
    
    Returns:
        Días adicionales a sumar al lead time base
    """
    dias_adicionales = 0
    
    for disrupcion in disrupciones_activas:
        if disrupcion.tipo_disrupcion == 'retraso_proveedor':
            if disrupcion.esta_activa(dia_actual):
                productos_afectados = disrupcion.parametros.get('productos_afectados', [])
                # Si lista vacía = todos los productos afectados
                if not productos_afectados or producto_id in productos_afectados:
                    dias_adicionales += disrupcion.parametros.get('dias_adicionales', 0)
    
    return dias_adicionales


def calcular_impacto_demanda(producto_id, region, demanda_base, dia_actual, disrupciones_activas):
    """
    Calcula la demanda ajustada considerando disrupciones activas
    
    Args:
        producto_id: ID del producto
        region: Región donde se vende
        demanda_base: Demanda calculada normalmente
        dia_actual: Día actual de la simulación
        disrupciones_activas: Lista de disrupciones activas
    
    Returns:
        Demanda ajustada
    """
    multiplicador_total = 1.0
    
    for disrupcion in disrupciones_activas:
        if disrupcion.tipo_disrupcion == 'aumento_demanda':
            if disrupcion.esta_activa(dia_actual):
                productos_afectados = disrupcion.parametros.get('productos', [])
                regiones_afectadas = disrupcion.parametros.get('regiones', [])
                
                producto_aplica = not productos_afectados or producto_id in productos_afectados
                region_aplica = region in regiones_afectadas
                
                if producto_aplica and region_aplica:
                    multiplicador_total *= disrupcion.parametros.get('multiplicador', 1.0)
    
    return demanda_base * multiplicador_total


def calcular_impacto_capacidad(region, capacidad_base, dia_actual, disrupciones_activas):
    """
    Calcula la capacidad logística ajustada considerando disrupciones
    
    Args:
        region: Región de despacho
        capacidad_base: Capacidad normal
        dia_actual: Día actual
        disrupciones_activas: Lista de disrupciones activas
    
    Returns:
        Capacidad ajustada
    """
    reduccion_total = 0
    
    for disrupcion in disrupciones_activas:
        if disrupcion.tipo_disrupcion == 'reduccion_capacidad':
            if disrupcion.esta_activa(dia_actual):
                regiones_afectadas = disrupcion.parametros.get('regiones', [])
                
                if region in regiones_afectadas:
                    reduccion_total += disrupcion.parametros.get('reduccion_porcentaje', 0)
    
    # Límite máximo de reducción: 90%
    reduccion_total = min(reduccion_total, 90)
    
    return capacidad_base * (1 - reduccion_total / 100)


def calcular_impacto_costo(producto_id, costo_base, dia_actual, disrupciones_activas):
    """
    Calcula el costo ajustado considerando disrupciones
    
    Args:
        producto_id: ID del producto
        costo_base: Costo normal del producto
        dia_actual: Día actual
        disrupciones_activas: Lista de disrupciones activas
    
    Returns:
        Costo ajustado
    """
    incremento_total = 0
    
    for disrupcion in disrupciones_activas:
        if disrupcion.tipo_disrupcion == 'aumento_costos':
            if disrupcion.esta_activa(dia_actual):
                productos_afectados = disrupcion.parametros.get('productos', [])
                
                if not productos_afectados or producto_id in productos_afectados:
                    incremento_total += disrupcion.parametros.get('incremento_porcentaje', 0)
    
    return costo_base * (1 + incremento_total / 100)


def verificar_region_disponible(region, dia_actual, disrupciones_activas):
    """
    Verifica si una región está disponible para despachos
    
    Args:
        region: Región a verificar
        dia_actual: Día actual
        disrupciones_activas: Lista de disrupciones activas
    
    Returns:
        tuple: (disponible: bool, dias_adicionales: int, razon: str)
    """
    for disrupcion in disrupciones_activas:
        if disrupcion.tipo_disrupcion == 'region_bloqueada':
            if disrupcion.esta_activa(dia_actual):
                regiones_bloqueadas = disrupcion.parametros.get('regiones', [])
                
                if region in regiones_bloqueadas:
                    dias_bloqueo = disrupcion.parametros.get('dias_bloqueo', 0)
                    razon = disrupcion.parametros.get('razon', 'Región temporalmente inaccesible')
                    return (False, dias_bloqueo, razon)
    
    return (True, 0, '')


def obtener_disrupciones_activas_empresa(simulacion, empresa_id, dia_actual):
    """
    Obtiene todas las disrupciones activas que afectan a una empresa
    
    Args:
        simulacion: Objeto Simulacion
        empresa_id: ID de la empresa
        dia_actual: Día actual de la simulación
    
    Returns:
        Lista de disrupciones activas filtradas
    """
    from models import DisrupcionActiva
    
    disrupciones = DisrupcionActiva.query.filter_by(
        simulacion_id=simulacion.id,
        activo=True
    ).filter(
        DisrupcionActiva.dia_inicio <= dia_actual,
        DisrupcionActiva.dia_fin >= dia_actual
    ).all()
    
    # Filtrar por empresa si aplica
    disrupciones_empresa = []
    for d in disrupciones:
        empresas_afectadas = d.empresas_afectadas
        if empresas_afectadas is None or empresa_id in empresas_afectadas:
            disrupciones_empresa.append(d)
    
    return disrupciones_empresa


def generar_alerta_disrupcion(disrupcion):
    """
    Genera el HTML/texto de alerta para mostrar a los estudiantes
    
    Args:
        disrupcion: Objeto DisrupcionActiva
    
    Returns:
        dict con información formateada de la alerta
    """
    severidad_class = {
        'baja': 'info',
        'media': 'warning',
        'alta': 'danger',
        'critica': 'danger'
    }
    
    severidad_icon = {
        'baja': 'fa-info-circle',
        'media': 'fa-exclamation-triangle',
        'alta': 'fa-exclamation-circle',
        'critica': 'fa-radiation'
    }
    
    return {
        'id': disrupcion.id,
        'titulo': disrupcion.nombre,
        'descripcion': disrupcion.descripcion,
        'tipo': disrupcion.tipo_disrupcion,
        'severidad': disrupcion.severidad,
        'class': severidad_class.get(disrupcion.severidad, 'info'),
        'icono': disrupcion.icono or severidad_icon.get(disrupcion.severidad, 'fa-bell'),
        'dias_restantes': disrupcion.dia_fin - disrupcion.dia_inicio + 1,
        'parametros': disrupcion.parametros
    }
