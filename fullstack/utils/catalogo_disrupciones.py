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
                    'Buscar un proveedor secundario que puede abastecer en 7 días, '
                    'pero con 20% mayor costo por unidad y pedido mínimo de 200 unidades.'
                ),
                'icono': 'fas fa-handshake',
                'color': 'success',
                'efectos': {
                    'tipo': 'proveedor_alterno',
                    'costo_multiplicador': 1.20,
                    'tiempo_entrega_override': 7,
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
                    'se entregarán con 14 días adicionales de retraso.'
                ),
                'icono': 'fas fa-clock',
                'color': 'danger',
                'efectos': {
                    'tipo': 'esperar',
                    'delay_compras_pendientes': 14,
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
            <p>El área de <strong>Ventas</strong> recibe información urgente del mercado:</p>
            <blockquote class="fst-italic border-start border-4 border-success ps-3 my-3 text-muted">
                &ldquo;Uno de los competidores principales ha presentado
                <strong>problemas de abastecimiento</strong>. Varios clientes están buscando
                nuevos proveedores para cubrir sus necesidades inmediatas.&rdquo;
            </blockquote>
            <p>En las últimas 48 horas se han recibido
            <strong>solicitudes de cotización superiores a lo habitual</strong> y
            clientes actuales quieren aumentar el volumen de sus pedidos.</p>
            <div class="alert alert-success py-2 mt-2 mb-1">
                <strong><i class="fas fa-lightbulb me-1"></i>Oportunidad:</strong>
                <ul class="mb-0 mt-1">
                    <li>Incremento potencial de ventas del <strong>+30%</strong> en el producto principal</li>
                    <li>Captación de nuevos clientes del competidor</li>
                    <li>Riesgo: sobreinventario si la demanda vuelve a la normalidad</li>
                </ul>
            </div>
            <p class="text-muted small mt-2">Todo el equipo debe decidir cómo reaccionar ante
            esta oportunidad de mercado con la información disponible.</p>
        """,
        'mensaje_fin': (
            "✅ La situación del competidor se ha regularizado. "
            "La demanda extraordinaria ha concluido y el mercado vuelve a sus niveles habituales."
        ),
        'opciones': {
            'A': {
                'titulo': 'Aceptar todos los pedidos y aumentar compras inmediatamente',
                'descripcion': (
                    'Confirmar pedidos actuales y nuevos clientes. '
                    'Se emite automáticamente una orden de compra adicional (+40% de la demanda promedio). '
                    'Mayor riesgo de sobreinventario si la demanda normaliza.'
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
                'titulo': 'Aceptar parcialmente el aumento de demanda',
                'descripcion': (
                    'Priorizar clientes estratégicos y de mayor margen. '
                    'Limitar el volumen aceptado a nuevos clientes. '
                    'Compras ajustadas moderadamente sin riesgo de sobrestock.'
                ),
                'icono': 'fas fa-sliders-h',
                'color': 'info',
                'efectos': {
                    'tipo': 'aumento_demanda',
                    'demanda_multiplicador': 1.15,
                },
            },
            'C': {
                'titulo': 'Mantener el plan actual sin aceptar incrementos',
                'descripcion': (
                    'No aceptar pedidos extraordinarios. '
                    'Mantener plan de compras original. '
                    'Se perderán las ventas adicionales del mercado, pero se protege la estabilidad operativa.'
                ),
                'icono': 'fas fa-minus-circle',
                'color': 'danger',
                'efectos': {
                    'tipo': 'sin_efecto',
                },
            },
            'D': {
                'titulo': 'Aumentar precios ante el incremento de demanda',
                'descripcion': (
                    'Ajustar el precio de venta del producto afectado +15% para aprovechar la coyuntura. '
                    'La demanda cae un 10% por elasticidad, pero el margen por unidad mejora significativamente.'
                ),
                'icono': 'fas fa-tags',
                'color': 'warning',
                'efectos': {
                    'tipo': 'aumento_precio_demanda',
                    'precio_multiplicador': 1.15,
                    'demanda_multiplicador': 0.90,
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
            <p>El área de <strong>Logística</strong> informa que, tras una revisión técnica inesperada,
            se detectó que varios vehículos de la flota propia <strong>no cumplían con los
            mantenimientos preventivos</strong> programados.</p>
            <div class="alert alert-danger py-2 mt-2 mb-3">
                <strong><i class="fas fa-exclamation-triangle me-1"></i>Situación actual:</strong>
                <ul class="mb-0 mt-1">
                    <li>El <strong>40% de los vehículos</strong> quedan fuera de operación inmediata</li>
                    <li>Tiempo estimado de reparación: <strong>14 días</strong></li>
                    <li>Contratar transporte tercerizado implica un <strong>costo 30% mayor</strong> por envío</li>
                </ul>
            </div>
            <p>Si no se toman decisiones oportunas, podrían presentarse:</p>
            <ul>
                <li>Retrasos en las entregas a regiones</li>
                <li>Acumulación de inventario en bodega</li>
                <li>Afectación en el nivel de servicio</li>
            </ul>
            <p class="text-muted small mt-2">Todo el equipo debe decidir cómo responder ante esta situación.</p>
        """,
        'mensaje_fin': (
            "✅ La flota propia ha sido reparada y vuelve a operación completa. "
            "Los costos de transporte retornan a sus valores normales."
        ),
        'opciones': {
            'A': {
                'titulo': 'Contratar transporte tercerizado (100% del déficit)',
                'descripcion': (
                    'Activar operador externo inmediatamente para cubrir el 100% de la capacidad. '
                    'Mantener todas las promesas de entrega. '
                    'Incremento del 30% en costo logístico por envío durante 14 días.'
                ),
                'icono': 'fas fa-shipping-fast',
                'color': 'success',
                'efectos': {
                    'tipo': 'costo_logistico',
                    'costo_multiplicador': 1.30,
                    'delay_semanas': 0,
                },
            },
            'B': {
                'titulo': 'Combinar flota propia con transporte externo parcial',
                'descripcion': (
                    'Usar flota disponible para clientes prioritarios y tercerizar el resto. '
                    'Incremento del 15% en costos logísticos. '
                    'Capacidad de despacho reducida moderadamente.'
                ),
                'icono': 'fas fa-random',
                'color': 'warning',
                'efectos': {
                    'tipo': 'costo_logistico',
                    'costo_multiplicador': 1.15,
                    'delay_semanas': 0,
                },
            },
            'C': {
                'titulo': 'Operar solo con flota disponible (sin contratar externo)',
                'descripcion': (
                    'Mantener operación únicamente con el 60% de flota disponible. '
                    'Sin costos adicionales, pero todos los despachos se retrasan 7 días '
                    'mientras se repara la flota.'
                ),
                'icono': 'fas fa-pause-circle',
                'color': 'danger',
                'efectos': {
                    'tipo': 'costo_logistico',
                    'costo_multiplicador': 1.0,
                    'delay_semanas': 7,
                },
            },
        },
    },
    {
        'key': 'aumento_costos_compra',
        'nombre': 'Aumento Repentino en Costos de Compra',
        'semana_trigger': 11,
        'duracion_semanas': 2,
        'icono': 'fas fa-dollar-sign',
        'color': 'danger',
        'contexto_html': """
            <p>El área de <strong>Compras</strong> recibe una comunicación urgente del proveedor principal:</p>
            <blockquote class="fst-italic border-start border-4 border-danger ps-3 my-3 text-muted">
                &ldquo;Debido al alza en costos de materias primas e insumos de producción,
                nos vemos obligados a incrementar el precio de venta de nuestros productos
                en un <strong>18%</strong> con vigencia inmediata. Esta medida aplica a todos
                los nuevos pedidos a partir de la fecha.&rdquo;
            </blockquote>
            <p>Este proveedor suministra el <strong>producto más demandado</strong> del portafolio.</p>
            <div class="alert alert-danger py-2 mt-2 mb-1">
                <strong><i class="fas fa-exclamation-triangle me-1"></i>Impacto potencial:</strong>
                <ul class="mb-0 mt-1">
                    <li>Reducción directa del <strong>margen bruto</strong> si se absorbe el costo</li>
                    <li>Riesgo de perder clientes si se traslada el aumento al precio de venta</li>
                    <li>Posibilidad de buscar proveedor alterno con condiciones diferentes</li>
                </ul>
            </div>
            <p class="text-muted small mt-2">Todo el equipo debe decidir cómo gestionar este incremento
            de costos manteniendo la rentabilidad y el nivel de servicio.</p>
        """,
        'mensaje_fin': (
            "✅ El proveedor ha informado que los costos de materias primas se han estabilizado. "
            "Los precios de compra retornan a sus valores anteriores."
        ),
        'opciones': {
            'A': {
                'titulo': 'Absorber el aumento (mantener precio de venta)',
                'descripcion': (
                    'Asumir internamente el incremento del 18% en el costo de compra. '
                    'El precio de venta al cliente se mantiene sin cambios. '
                    'El margen por unidad se reduce durante la duración de la disrupción.'
                ),
                'icono': 'fas fa-hand-holding-usd',
                'color': 'warning',
                'efectos': {
                    'tipo': 'costo_compra',
                    'costo_multiplicador': 1.18,
                },
            },
            'B': {
                'titulo': 'Trasladar el aumento al precio de venta',
                'descripcion': (
                    'Ajustar el precio de venta del producto afectado en un +18% '
                    'para mantener el margen. La demanda puede caer por elasticidad. '
                    'El precio regresará a su valor original al finalizar la disrupción.'
                ),
                'icono': 'fas fa-tags',
                'color': 'info',
                'efectos': {
                    'tipo': 'costo_compra_precio_venta',
                    'precio_multiplicador': 1.18,
                },
            },
            'C': {
                'titulo': 'Activar proveedor alterno (menor costo, mayor plazo)',
                'descripcion': (
                    'Contratar un proveedor secundario con un costo 17.4% menor al original. '
                    'Condiciones: pedido mínimo de 150 unidades y tiempo de entrega '
                    '+7 días adicionales. El margen se protege a cambio de mayor inventario requerido.'
                ),
                'icono': 'fas fa-exchange-alt',
                'color': 'success',
                'efectos': {
                    'tipo': 'costo_compra',
                    'costo_multiplicador': 0.826,
                    'delay_entrega': 7,
                    'pedido_minimo': 150,
                },
            },
        },
    },
    # Aquí se agregarán futuras disrupciones
]


def get_disrupcion(key):
    """Retorna la definición de una disrupción por su key."""
    return next((d for d in CATALOGO_DISRUPCIONES if d['key'] == key), None)
