"""
Utilidades para reiniciar simulación manteniendo histórico
"""
from models import (Simulacion, Empresa, Producto, Inventario,
                    Venta, Metrica, Compra, DespachoRegional,
                    MovimientoInventario, DisrupcionEmpresa, RequerimientoCompra)
from extensions import db
from datetime import datetime


def reiniciar_simulacion(capital_inicial=50000000, nombre_simulacion=None,
                         inv_750ml=120, inv_1l=80):
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
            duracion_semanas=30,
            capital_inicial_empresas=capital_inicial,
            activa=True
        )
        db.session.add(nueva_simulacion)
        db.session.flush()  # obtener ID

        # 3. Re-vincular empresas a la nueva simulación y resetear capital
        productos = Producto.query.filter_by(activo=True).all()

        # ── Calibración automática de demanda ──────────────────────────────────
        # El stock inicial debe durar exactamente DIAS_COBERTURA días, creando
        # presión real: si Compras no hace pedidos en los primeros días, el
        # inventario se agota y el nivel de servicio cae visiblemente.
        #
        # demanda_promedio es semanal por región. En el motor competitivo:
        #   consumo diario empresa = (demanda_promedio / 7) × REGIONES
        #   stock inicial          = DIAS_COBERTURA × consumo_diario
        # → demanda_promedio = inv_inicial × 7 / (DIAS_COBERTURA × REGIONES)
        DIAS_COBERTURA    = 5      # días que debe durar el stock inicial
        REGIONES          = 5
        DIAS_REORDEN      = 3      # reordenar cuando quedan 3 días de stock
        DIAS_SEGURIDAD    = 1      # colchón de seguridad: 1 día
        FACTOR_DESVIACION = 0.20   # variación estándar = 20% de la demanda promedio

        for producto in productos:
            inv_inicial = inv_750ml if '750ml' in producto.nombre else inv_1l

            # demanda_promedio semanal por región para cobertura de DIAS_COBERTURA días
            nueva_demanda = max(1, round(
                inv_inicial * 7 / (DIAS_COBERTURA * REGIONES)
            ))
            nueva_desviacion = max(1, round(nueva_demanda * FACTOR_DESVIACION))

            # Consumo diario de la empresa (todas las regiones)
            demanda_diaria_empresa = nueva_demanda / 7.0 * REGIONES

            nuevo_punto_reorden   = max(1, round(demanda_diaria_empresa * DIAS_REORDEN))
            nuevo_stock_seguridad = max(1, round(demanda_diaria_empresa * DIAS_SEGURIDAD))
            nuevo_stock_maximo    = 1500  # techo fijo general para todos los productos

            producto.demanda_promedio   = nueva_demanda
            producto.desviacion_demanda = nueva_desviacion
            producto.stock_maximo       = nuevo_stock_maximo

            # Guardar valores calculados para usarlos en inventarios
            producto._punto_reorden_calc   = nuevo_punto_reorden
            producto._stock_seguridad_calc = nuevo_stock_seguridad

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

        for empresa in empresas:
            empresa.simulacion_id = nueva_simulacion.id
            empresa.capital_inicial = capital_inicial
            empresa.capital_actual = capital_inicial

            # 4. Resetear inventarios (actualizar existentes, crear si faltan)
            for producto in productos:
                cantidad_inicial    = inv_750ml if '750ml' in producto.nombre else inv_1l
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

        # 6. Generar histórico de 30 días y órdenes iniciales
        from utils.historico_simulacion import generar_historico_30dias, generar_ordenes_iniciales
        
        historico_ok, historico_msg = generar_historico_30dias(nueva_simulacion, empresas)
        ordenes_ok, ordenes_msg = generar_ordenes_iniciales(nueva_simulacion, empresas)

        mensaje = (
            f'Simulación reiniciada exitosamente. '
            f'Nueva simulación: {nombre_simulacion} | '
            f'Empresas: {len(empresas)} | '
            f'Capital: ${capital_inicial:,.0f} | '
            f'Inventario: {inv_750ml} und (750ml) / {inv_1l} und (1L) | '
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
