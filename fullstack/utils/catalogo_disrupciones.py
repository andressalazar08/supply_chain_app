"""
Catálogo estático de disrupciones de la simulación.
Cada disrupción se activa automáticamente dentro de una ventana exacta de días.
"""

CATALOGO_DISRUPCIONES = [
    {
        'key': 'retraso_proveedor',
        'nombre': 'Retraso en Proveedor Estratégico',
        'dia_inicio': 8,
        'dia_fin': 21,
        'icono': 'fas fa-ship',
        'color': 'warning',
        'contexto_html': """
            <p><strong>El área de Compras</strong> recibe una notificación urgente de un proveedor clave:</p>
            <blockquote class="fst-italic border-start border-4 border-warning ps-3 my-3 text-muted">
                "Debido a problemas operativos en puerto y retrasos en inspecciones aduaneras,
                las compras que se realicen a partir de ahora tendrán un <strong>lead time de 7 días</strong>
                y solo se recibirán pedidos en <strong>días pares</strong>."
            </blockquote>
            <p>Riesgos potenciales:</p>
            <div class="alert alert-danger py-2 mt-2 mb-1">
                <strong><i class="fas fa-exclamation-triangle me-1"></i>Impacto operativo esperado:</strong>
                <ul class="mb-0 mt-1">
                    <li>Ruptura de inventario</li>
                    <li>Incumplimiento de pedidos</li>
                    <li>Disminución del nivel de servicio</li>
                </ul>
            </div>
            <p class="text-muted small mt-2">Esta decisión debe ser tomada por el rol de <strong>Compras</strong>.</p>
        """,
        'mensaje_fin': (
            "✅ El proveedor estratégico ha regularizado su operación. "
            "El embarque retrasado ha sido entregado y la cadena de abastecimiento vuelve a operar con normalidad."
        ),
        'opciones': {
            'A': {
                'titulo': 'Activar proveedor alterno inmediato',
                'descripcion': (
                    'Lead time: 3 días. '
                    'Costo adicional: +$5.000 por unidad. '
                    'Pedido mínimo: 60 und (750 mL) / 50 und (1 L).'
                ),
                'icono': 'fas fa-handshake',
                'color': 'success',
                'efectos': {
                    'tipo': 'proveedor_alterno',
                },
            },
            'B': {
                'titulo': 'Racionar inventario disponible',
                'descripcion': (
                    'Mantener proveedor actual y priorizar clientes estratégicos.'
                ),
                'icono': 'fas fa-balance-scale',
                'color': 'info',
                'efectos': {
                    'tipo': 'racionamiento',
                },
            },
        },
    },
    {
        'key': 'aumento_demanda',
        'nombre': 'Aumento Inesperado en la Demanda',
        'dia_inicio': 29,
        'dia_fin': 35,
        'icono': 'fas fa-chart-line',
        'color': 'success',
        'contexto_html': """
            <p>El área de <strong>Ventas</strong> detecta un cambio en el mercado:</p>
            <blockquote class="fst-italic border-start border-4 border-success ps-3 my-3 text-muted">
                &ldquo;Uno de los competidores principales ha presentado problemas de abastecimiento y
                varios clientes están buscando nuevos proveedores para cubrir sus necesidades inmediatas.
                En las últimas 48 horas se han recibido solicitudes de cotización superiores a lo habitual.&rdquo;
            </blockquote>
            <p>Riesgos potenciales:</p>
            <div class="alert alert-success py-2 mt-2 mb-1">
                <strong><i class="fas fa-exclamation-triangle me-1"></i>Impacto operativo esperado:</strong>
                <ul class="mb-0 mt-1">
                    <li>Sobredemanda sin capacidad de respuesta</li>
                    <li>Sobreinventario futuro</li>
                    <li>Desbalance en la operación</li>
                </ul>
            </div>
            <p class="text-muted small mt-2">Esta decisión debe ser tomada por el rol de <strong>Ventas</strong>.</p>
        """,
        'mensaje_fin': (
            "✅ La situación del competidor se ha regularizado. "
            "La demanda extraordinaria ha concluido y el mercado vuelve a sus niveles habituales."
        ),
        'opciones': {
            'A': {
                'titulo': 'Aceptar todos los nuevos pedidos y aumentar compras inmediatamente',
                'descripcion': (
                    'Confirmar pedidos actuales y nuevos clientes. '
                    'Emitir órdenes de compra adicionales para cubrir el incremento. '
                    'Riesgo de sobreinventario.'
                ),
                'icono': 'fas fa-bolt',
                'color': 'success',
                'efectos': {
                    'tipo': 'aumento_demanda',
                    'demanda_multiplicador': 1.30,
                    'compras_auto_factor': 0.40,
                },
            },
            'B': {
                'titulo': 'Aceptar parcialmente el aumento de la demanda',
                'descripcion': (
                    'Priorizar clientes estratégicos o de mayor margen. '
                    'Limitar el volumen aceptado a nuevos clientes. '
                    'Ajustar compras moderadamente.'
                ),
                'icono': 'fas fa-sliders-h',
                'color': 'info',
                'efectos': {
                    'tipo': 'aumento_demanda',
                    'demanda_multiplicador': 1.15,
                },
            },
            'C': {
                'titulo': 'Mantener el plan actual sin aceptar incrementos adicionales',
                'descripcion': (
                    'No aceptar pedidos extraordinarios. '
                    'Mantener plan de compras original. '
                    'Proteger estabilidad operativa.'
                ),
                'icono': 'fas fa-minus-circle',
                'color': 'danger',
                'efectos': {
                    'tipo': 'sin_efecto',
                },
            },
        },
    },
    {
        'key': 'falla_flota',
        'nombre': 'Reducción de Capacidad Logística por Fallas en Flota',
        'dia_inicio': 43,
        'dia_fin': 56,
        'icono': 'fas fa-truck',
        'color': 'danger',
        'contexto_html': """
            <p>El área de <strong>Logística</strong> informa una falla crítica:</p>
            <div class="alert alert-danger py-2 mt-2 mb-3">
                <strong><i class="fas fa-exclamation-triangle me-1"></i>Situación actual:</strong>
                <ul class="mb-0 mt-1">
                    <li>Los vehículos con <strong>capacidad 500</strong> quedan fuera de operación por incumplimiento de mantenimiento.</li>
                    <li>Tiempo estimado de reparación: <strong>2 semanas</strong>.</li>
                    <li>El transporte externo implica un costo por unidad <strong>2 veces mayor</strong>.</li>
                </ul>
            </div>
            <p>Riesgos potenciales:</p>
            <ul>
                <li>Retrasos en las entregas a regiones</li>
                <li>Acumulación de inventario en bodega</li>
                <li>Afectación en el nivel de servicio</li>
            </ul>
            <p class="text-muted small mt-2">Esta decisión debe ser tomada por el rol de <strong>Logística</strong>.</p>
        """,
        'mensaje_fin': (
            "✅ La flota propia ha sido reparada y vuelve a operación completa. "
            "Los costos de transporte retornan a sus valores normales."
        ),
        'opciones': {
            'A': {
                'titulo': 'Contratar transporte tercerizado',
                'descripcion': (
                    'Activar operador externo inmediatamente. '
                    'Asumir incremento del doble en costo logístico por envío.'
                ),
                'icono': 'fas fa-shipping-fast',
                'color': 'success',
                'efectos': {
                    'tipo': 'costo_logistico',
                    'costo_multiplicador': 1.0,
                    'delay_semanas': 0,
                },
            },
            'B': {
                'titulo': 'Generar solo las ventas que cubran la capacidad de los vehículos internos',
                'descripcion': (
                    'Mantener operación solo con flota disponible. '
                    'Evitar contratación externa.'
                ),
                'icono': 'fas fa-balance-scale',
                'color': 'warning',
                'efectos': {
                    'tipo': 'costo_logistico',
                    'costo_multiplicador': 1.0,
                    'delay_semanas': 0,
                },
            },
        },
    },
]


def get_disrupcion(key):
    """Retorna la definición de una disrupción por su key."""
    return next((d for d in CATALOGO_DISRUPCIONES if d['key'] == key), None)
