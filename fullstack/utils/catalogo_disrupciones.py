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
            <p>Esta mañana el área de Compras recibe un correo urgente de uno de los proveedores estratégicos:</p>
            <blockquote class="fst-italic border-start border-4 border-warning ps-3 my-3 text-muted">
                "Debido a problemas operativos en puerto y retrasos en inspecciones
                aduaneras, el embarque programado para esta semana se retrasará
                <strong>10 días</strong>."
            </blockquote>
            <p>Este proveedor representa el <strong>60% del suministro</strong> del producto más
            demandado de su portafolio.</p>
            <div class="alert alert-danger py-2 mt-2 mb-1">
                <strong><i class="fas fa-exclamation-triangle me-1"></i>Si no se toman decisiones
                oportunas, en aproximadamente dos semanas podría generarse:</strong>
                <ul class="mb-0 mt-1">
                    <li>Ruptura de inventario</li>
                    <li>Incumplimiento de pedidos</li>
                    <li>Caída en el nivel de servicio</li>
                </ul>
            </div>
            <p class="text-muted small mt-2">El equipo completo (Ventas, Planeación, Logística y
            Compras) debe decidir cómo actuar con la información disponible.</p>
        """,
        'mensaje_fin': (
            "✅ El proveedor estratégico ha regularizado su operación. "
            "El embarque retrasado ha sido entregado y la cadena de abastecimiento vuelve a operar con normalidad."
        ),
        'opciones': {
            'A': {
                'titulo': 'Activar proveedor alterno inmediato',
                'descripcion': (
                    'Buscar un proveedor secundario que puede abastecer en 1 semana, '
                    'pero con 20% mayor costo por unidad y pedido mínimo de 200 unidades.'
                ),
                'icono': 'fas fa-handshake',
                'color': 'success',
                'efectos': {
                    'tipo': 'proveedor_alterno',
                    'costo_multiplicador': 1.20,
                    'tiempo_entrega_override': 1,
                    'pedido_minimo': 200,
                },
            },
            'B': {
                'titulo': 'Racionar inventario disponible',
                'descripcion': (
                    'Mantener el proveedor actual y priorizar clientes estratégicos. '
                    'Las ventas del producto afectado se limitan al 60% del inventario '
                    'disponible por semana para garantizar cobertura futura.'
                ),
                'icono': 'fas fa-balance-scale',
                'color': 'info',
                'efectos': {
                    'tipo': 'racionamiento',
                    'limite_ventas_factor': 0.60,
                },
            },
            'C': {
                'titulo': 'Mantener plan actual (esperar al proveedor)',
                'descripcion': (
                    'No realizar ajustes. '
                    'Las órdenes de compra pendientes del producto afectado '
                    'se entregarán con 2 semanas adicionales de retraso.'
                ),
                'icono': 'fas fa-clock',
                'color': 'danger',
                'efectos': {
                    'tipo': 'esperar',
                    'delay_compras_pendientes': 2,
                },
            },
        },
    }
    # Aquí se agregarán futuras disrupciones
]


def get_disrupcion(key):
    """Retorna la definición de una disrupción por su key."""
    return next((d for d in CATALOGO_DISRUPCIONES if d['key'] == key), None)
