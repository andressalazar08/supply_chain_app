"""
Catálogo estático de disrupciones de la simulación.
Cada disrupción se activa automáticamente en su semana_trigger y dura duracion_semanas.
"""

CATALOGO_DISRUPCIONES = [
    {
        'key': 'retraso_proveedor',
        'nombre': 'Retraso en Proveedor Estratégico',
        'semana_trigger': 2,
        'duracion_semanas': 2,
        'icono': 'fas fa-ship',
        'color': 'warning',
        'contexto_html': """
            <p><strong>El área de Compras</strong> recibe una notificación urgente de un proveedor clave:</p>
            <blockquote class="fst-italic border-start border-4 border-warning ps-3 my-3 text-muted">
                "Debido a problemas operativos en puerto y retrasos aduaneros,
                los nuevos pedidos tendrán un <strong>lead time de 7 días</strong>
                y solo se recibirán órdenes en <strong>días pares</strong>."
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
                'titulo': 'Activar proveedor alterno',
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
        'semana_trigger': 5,
        'duracion_semanas': 2,
        'icono': 'fas fa-chart-line',
        'color': 'success',
        'contexto_html': """
            <p>El área de <strong>Ventas</strong> detecta un cambio en el mercado:</p>
            <blockquote class="fst-italic border-start border-4 border-success ps-3 my-3 text-muted">
                &ldquo;Un competidor presenta problemas de abastecimiento, generando un aumento
                en solicitudes de cotización y pedidos en las últimas 48 horas.&rdquo;
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
                'titulo': 'Atender toda la demanda',
                'descripcion': (
                    'Aceptar pedidos actuales y nuevos. '
                    'Aumentar compras inmediatamente. '
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
                'titulo': 'Atender demanda de forma selectiva',
                'descripcion': (
                    'Priorizar clientes estratégicos o de mayor margen. '
                    'Limitar nuevos pedidos. '
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
                'titulo': 'Mantener plan actual',
                'descripcion': (
                    'No aceptar incrementos adicionales. '
                    'Mantener compras planeadas. '
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
        'semana_trigger': 8,
        'duracion_semanas': 2,
        'icono': 'fas fa-truck',
        'color': 'danger',
        'contexto_html': """
            <p>El área de <strong>Logística</strong> informa una falla crítica:</p>
            <div class="alert alert-danger py-2 mt-2 mb-3">
                <strong><i class="fas fa-exclamation-triangle me-1"></i>Situación actual:</strong>
                <ul class="mb-0 mt-1">
                    <li>El vehículo <strong>V2 (capacidad 440)</strong> queda fuera de operación por incumplimiento de mantenimiento.</li>
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
                'titulo': 'Contratar transporte externo',
                'descripcion': (
                    'Activación inmediata del transporte externo. '
                    'Incremento significativo en costos logísticos.'
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
                'titulo': 'Ajustar operación a capacidad interna',
                'descripcion': (
                    'Operar solo con flota disponible. '
                    'Limitar ventas según capacidad. '
                    'Evitar costos adicionales.'
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
    # Aquí se agregarán futuras disrupciones
]


def get_disrupcion(key):
    """Retorna la definición de una disrupción por su key."""
    return next((d for d in CATALOGO_DISRUPCIONES if d['key'] == key), None)
