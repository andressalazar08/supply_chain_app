"""
Utilidades para reiniciar simulación manteniendo histórico
"""
from models import (Simulacion, Empresa, Producto, Inventario,
                    Venta, Metrica, Compra, DespachoRegional,
                    MovimientoInventario, DisrupcionEmpresa, RequerimientoCompra,
                    DisponibilidadVehiculo, Decision)
from extensions import db
from datetime import datetime
from utils.demanda_central import generar_base_demanda_simulacion
from utils.parametros_iniciales import (
    CAPITAL_INICIAL_EMPRESA_DEFAULT,
    INVENTARIO_INICIAL_750_DEFAULT,
    INVENTARIO_INICIAL_1L_DEFAULT,
    DURACION_SIMULACION_SEMANAS,
    DIAS_HISTORICO_DEMANDA,
    CATALOGO_PRODUCTOS_BASE,
    inventario_inicial_por_producto,
    calcular_parametros_demanda,
)


def reiniciar_simulacion(capital_inicial=CAPITAL_INICIAL_EMPRESA_DEFAULT, nombre_simulacion=None,
                         inv_750ml=INVENTARIO_INICIAL_750_DEFAULT, inv_1l=INVENTARIO_INICIAL_1L_DEFAULT):
    """
    Crea una nueva simulación reutilizando las mismas empresas ya existentes.
    No se crean empresas nuevas: las del profesor se re-vinculan a la nueva
    simulación y sus datos operativos (capital, inventario, precios) se resetean.

    Args:
        capital_inicial: Capital inicial igual para todas las empresas
        nombre_simulacion: Nombre descriptivo (autogenerado si es None)
        inv_750ml: Unidades iniciales de inventario para productos 750ml
        inv_1l: Unidades iniciales de inventario para productos 1L

    Returns:
        tuple: (nueva_simulacion, mensaje_resultado)
    """
    try:
        # 1. Desactivar simulación actual y obtener sus empresas
        simulacion_anterior = Simulacion.query.filter_by(activa=True).first()
        if simulacion_anterior:
            simulacion_anterior.activa = False
            simulacion_anterior.estado = 'finalizado'
            simulacion_anterior.fecha_fin = datetime.utcnow()
            empresas = Empresa.query.filter_by(
                simulacion_id=simulacion_anterior.id, activa=True
            ).all()
        else:
            empresas = Empresa.query.filter_by(activa=True).all()

        if not empresas:
            return None, "No hay empresas registradas para reiniciar"

        # 2. Crear nueva simulación
        if not nombre_simulacion:
            numero_sim = Simulacion.query.count() + 1
            nombre_simulacion = f'Simulación {numero_sim}'

        nueva_simulacion = Simulacion(
            nombre=nombre_simulacion,
            semana_actual=1,
            dia_actual=1,
            estado='pausado',
            fecha_inicio=datetime.utcnow(),
            duracion_semanas=DURACION_SIMULACION_SEMANAS,
            capital_inicial_empresas=capital_inicial,
            activa=True
        )
        db.session.add(nueva_simulacion)
        db.session.flush()  # obtener ID

        # 3. Re-vincular empresas a la nueva simulación y resetear capital
        productos = Producto.query.filter_by(activo=True).all()

        # ── Calibración automática de demanda ──────────────────────────────────
        for producto in productos:
            base_producto = CATALOGO_PRODUCTOS_BASE.get((producto.codigo or '').upper())
            if base_producto:
                producto.precio_base = float(base_producto['precio_base'])
                producto.precio_actual = float(base_producto['precio_base'])
                producto.precio_sugerido = float(base_producto['precio_base'])
                producto.costo_unitario = float(base_producto['costo_unitario'])

            inv_inicial = inventario_inicial_por_producto(producto, inv_750ml, inv_1l)
            params = calcular_parametros_demanda(inv_inicial)

            producto.demanda_promedio = params['demanda_promedio']
            producto.desviacion_demanda = params['desviacion_demanda']
            producto.stock_maximo = params['stock_maximo']

            # Guardar valores calculados para usarlos en inventarios
            producto._punto_reorden_calc = params['punto_reorden']
            producto._stock_seguridad_calc = params['stock_seguridad']

        # ── Fin calibración ────────────────────────────────────────────────────

        # 3b. Limpiar datos históricos de las empresas para que cada simulación
        #     empiece completamente en cero (ventas, métricas, compras, etc.)
        for empresa in empresas:
            ids = (empresa.id,)
            Venta.query.filter(Venta.empresa_id.in_(ids)).delete(synchronize_session=False)
            Metrica.query.filter(Metrica.empresa_id.in_(ids)).delete(synchronize_session=False)
            Compra.query.filter(Compra.empresa_id.in_(ids)).delete(synchronize_session=False)
            DespachoRegional.query.filter(DespachoRegional.empresa_id.in_(ids)).delete(synchronize_session=False)
            MovimientoInventario.query.filter(MovimientoInventario.empresa_id.in_(ids)).delete(synchronize_session=False)
            DisrupcionEmpresa.query.filter(DisrupcionEmpresa.empresa_id.in_(ids)).delete(synchronize_session=False)
            RequerimientoCompra.query.filter(RequerimientoCompra.empresa_id.in_(ids)).delete(synchronize_session=False)
            DisponibilidadVehiculo.query.filter(DisponibilidadVehiculo.empresa_id.in_(ids)).delete(synchronize_session=False)
            Decision.query.filter(Decision.empresa_id.in_(ids)).delete(synchronize_session=False)

        for empresa in empresas:
            empresa.simulacion_id = nueva_simulacion.id
            empresa.capital_inicial = capital_inicial
            empresa.capital_actual = capital_inicial

            # 4. Resetear inventarios (actualizar existentes, crear si faltan)
            for producto in productos:
                cantidad_inicial = inventario_inicial_por_producto(producto, inv_750ml, inv_1l)
                punto_reorden_calc  = getattr(producto, '_punto_reorden_calc',   50)
                stock_seguridad_calc = getattr(producto, '_stock_seguridad_calc', 20)

                inventario = Inventario.query.filter_by(
                    empresa_id=empresa.id,
                    producto_id=producto.id
                ).first()

                if inventario:
                    inventario.cantidad_actual   = cantidad_inicial
                    inventario.cantidad_reservada = 0
                    inventario.costo_promedio    = producto.costo_unitario
                    inventario.punto_reorden     = punto_reorden_calc
                    inventario.stock_seguridad   = stock_seguridad_calc
                else:
                    db.session.add(Inventario(
                        empresa_id=empresa.id,
                        producto_id=producto.id,
                        cantidad_actual=cantidad_inicial,
                        cantidad_reservada=0,
                        punto_reorden=punto_reorden_calc,
                        stock_seguridad=stock_seguridad_calc,
                        costo_promedio=producto.costo_unitario
                    ))

        # 5. Resetear precios de productos a su valor base
        for producto in productos:
            producto.precio_actual = producto.precio_base

        db.session.commit()

        # 6. Generar base central de demanda (histórico + horizonte simulación)
        demanda_ok, demanda_msg = generar_base_demanda_simulacion(
            nueva_simulacion,
            dias_historico=DIAS_HISTORICO_DEMANDA,
            replace=True,
        )
        if not demanda_ok:
            raise RuntimeError(demanda_msg)

        # 7. Generar histórico de 30 días y órdenes iniciales
        from utils.historico_simulacion import generar_historico_30dias, generar_ordenes_iniciales
        from utils.procesamiento_dias import asegurar_metricas_base_dia_uno
        
        historico_ok, historico_msg = generar_historico_30dias(nueva_simulacion, empresas)
        ordenes_ok, ordenes_msg = generar_ordenes_iniciales(nueva_simulacion, empresas)
        asegurar_metricas_base_dia_uno(nueva_simulacion)

        mensaje = (
            f'Simulación reiniciada exitosamente. '
            f'Nueva simulación: {nombre_simulacion} | '
            f'Empresas: {len(empresas)} | '
            f'Capital: ${capital_inicial:,.0f} | '
            f'Inventario: {inv_750ml} und (750ml) / {inv_1l} und (1L) | '
            f'{demanda_msg} | '
            f'{historico_msg} | '
            f'{ordenes_msg}'
        )

        return nueva_simulacion, mensaje

    except Exception as e:
        db.session.rollback()
        return None, f"Error al reiniciar simulación: {str(e)}"


def obtener_simulacion_activa():
    """Obtiene la simulación actualmente activa"""
    return Simulacion.query.filter_by(activa=True).first()


def obtener_historico_simulaciones():
    """Obtiene todas las simulaciones ordenadas por fecha"""
    return Simulacion.query.order_by(Simulacion.created_at.desc()).all()
