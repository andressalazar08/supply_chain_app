"""
Utilidades para procesamiento automático de semanas de simulación
"""

from models import (Simulacion, Empresa, Producto, Inventario, Venta, Compra,
                    DespachoRegional, MovimientoInventario, Metrica, DisrupcionEmpresa, Decision)
from extensions import db
from datetime import datetime
from sqlalchemy import func
from utils.demanda_central import obtener_demanda_base, validar_cobertura_demanda_dia


def calcular_precios_mercado(simulacion, producto_id, region):
    """
    Calcula el precio promedio del mercado para un producto en una región
    Retorna: (precio_promedio, lista de (empresa_id, precio, stock_disponible))
    """
    empresas_activas = Empresa.query.filter_by(simulacion_id=simulacion.id).all()
    precios_mercado = []
    
    for empresa in empresas_activas:
        # Obtener precio del producto para esta empresa
        producto = Producto.query.get(producto_id)
        if not producto:
            continue
            
        inventario = Inventario.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto_id
        ).first()
        
        stock_disponible = 0
        if inventario:
            stock_disponible = inventario.cantidad_actual - inventario.cantidad_reservada
            stock_disponible = max(0, stock_disponible)
        
        # El precio actual es el mismo para todas las regiones (precio_actual del producto)
        # En el futuro podríamos tener precios por región
        precios_mercado.append({
            'empresa_id': empresa.id,
            'precio': producto.precio_actual,
            'stock': stock_disponible
        })
    
    # Calcular precio promedio de todas las empresas activas (independiente del stock)
    # Incluir empresas sin stock para que el precio de referencia sea justo
    precios_validos = [p['precio'] for p in precios_mercado]
    precio_promedio = sum(precios_validos) / len(precios_validos) if precios_validos else 0
    
    return precio_promedio, precios_mercado


def calcular_market_share(precio_empresa, precio_promedio, stock_disponible, elasticidad):
    """
    Calcula el porcentaje de market share que recibe una empresa
    basado en su precio relativo al mercado y disponibilidad de stock
    
    Retorna: porcentaje de 0 a 1
    """
    if precio_promedio <= 0:
        # Sin referencia de precio: distribución neutra, penalizada si no hay stock
        return 0.3 if stock_disponible <= 0 else 1.0
    
    # Calcular ratio de precio
    ratio_precio = precio_empresa / precio_promedio
    
    # Aplicar elasticidad del producto
    # Productos premium (baja elasticidad) son menos sensibles al precio
    # Productos económicos (alta elasticidad) son muy sensibles al precio
    factor_elasticidad = elasticidad / 2.0  # Normalizar
    
    # Calcular market share base según ratio de precio
    if ratio_precio > 1.5:  # Precio muy alto (>150% del promedio)
        market_share = 0.0
    elif ratio_precio > 1.2:  # Precio alto (120-150%)
        market_share = 0.1 + (1.5 - ratio_precio) * 0.3 * factor_elasticidad
    elif ratio_precio > 0.9:  # Precio competitivo (90-120%)
        market_share = 0.5 + (1.2 - ratio_precio) * 0.5
    elif ratio_precio > 0.7:  # Precio bajo (70-90%)
        market_share = 0.6 + (0.9 - ratio_precio) * 1.0
    else:  # Precio muy bajo (<70%)
        # Sospecha de calidad - no siempre es mejor
        market_share = 0.4
    
    # Sin stock: penalizar al 30% en lugar de bloquear completamente.
    # El mercado sigue intentando ordenar a esta empresa (demanda registrada como no atendida)
    # → esto hace que el nivel de servicio caiga visiblemente cuando hay desabastecimiento.
    if stock_disponible <= 0:
        market_share *= 0.3
    
    # Asegurar que esté entre 0 y 1
    market_share = max(0.0, min(1.0, market_share))
    
    return market_share


def distribuir_demanda_competitiva(simulacion, producto, region, demanda_total, semana_actual):
    """
    Distribuye la demanda total del mercado entre todas las empresas
    según su competitividad de precios y disponibilidad de stock
    
    Retorna: (lista de asignaciones, precio_promedio)
    """
    # Obtener precios de mercado
    precio_promedio, empresas_info = calcular_precios_mercado(simulacion, producto.id, region)
    
    if precio_promedio <= 0 or not empresas_info:
        return [], 0  # Sin mercado activo - retornar tupla vacía
    
    # Calcular market share para cada empresa
    market_shares = []
    total_market_share = 0
    
    for info in empresas_info:
        share = calcular_market_share(
            info['precio'], 
            precio_promedio, 
            info['stock'],
            producto.elasticidad_precio
        )
        market_shares.append({
            'empresa_id': info['empresa_id'],
            'precio': info['precio'],
            'stock': info['stock'],
            'market_share': share
        })
        total_market_share += share
    
    # Normalizar market shares
    if total_market_share > 0:
        for ms in market_shares:
            ms['market_share'] = ms['market_share'] / total_market_share
    
    # Distribuir demanda según market share
    asignaciones = []
    demanda_restante = demanda_total
    
    # Ordenar por market share descendente
    market_shares.sort(key=lambda x: x['market_share'], reverse=True)
    
    for ms in market_shares:
        if demanda_restante <= 0:
            break
            
        # Calcular demanda asignada a esta empresa según market share
        demanda_empresa = round(demanda_total * ms['market_share'])
        
        # No se limita por stock aquí: el stock disponible limita las ventas reales
        # en procesar_ventas_semana. Esto permite registrar demanda no atendida,
        # lo que hace que el nivel de servicio baje correctamente cuando hay desabastecimiento.
        cantidad_asignada = min(demanda_empresa, demanda_restante)
        
        if cantidad_asignada > 0:
            asignaciones.append({
                'empresa_id': ms['empresa_id'],
                'cantidad': cantidad_asignada,
                'precio': ms['precio'],
                'market_share': ms['market_share'],
                'stock_disponible': ms['stock']
            })
            demanda_restante -= cantidad_asignada
    
    # Si queda demanda sin asignar (todas sin stock o precios muy altos)
    # Se registrará como ventas perdidas para cada empresa según su intención de compra
    
    return asignaciones, precio_promedio


# ---------------------------------------------------------------------------
# SISTEMA DE DISRUPCIONES
# ---------------------------------------------------------------------------

def obtener_producto_mas_demandado(empresa):
    """
    Retorna el producto con mayor volumen de ventas histórico para la empresa.
    Si no hay ventas aún, usa el de mayor demanda_promedio en el catálogo.
    """
    resultado = db.session.query(
        Venta.producto_id,
        func.sum(Venta.cantidad_vendida).label('total')
    ).filter_by(empresa_id=empresa.id).group_by(Venta.producto_id).order_by(
        func.sum(Venta.cantidad_vendida).desc()
    ).first()

    if resultado:
        return Producto.query.get(resultado.producto_id)
    return Producto.query.filter_by(activo=True).order_by(Producto.demanda_promedio.desc()).first()


def verificar_y_activar_disrupciones(simulacion):
    """
    Revisa el catálogo y crea registros DisrupcionEmpresa para las empresas
    que aún no tienen la disrupción cuyo semana_trigger ya fue alcanzada o pasada.
    Usar >= permite crear disrupciones para empresas que se unieron tarde a la simulación.
    """
    from utils.catalogo_disrupciones import CATALOGO_DISRUPCIONES

    # Comparar semana_trigger (concepto de semana) con la semana derivada del día actual
    semana_derivada = (simulacion.dia_actual - 1) // 7 + 1
    dia = simulacion.dia_actual
    empresas = Empresa.query.filter_by(activa=True, simulacion_id=simulacion.id).all()
    nuevas = []

    for definicion in CATALOGO_DISRUPCIONES:
        if definicion['semana_trigger'] > semana_derivada:
            continue
        for empresa in empresas:
            ya_existe = DisrupcionEmpresa.query.filter_by(
                simulacion_id=simulacion.id,
                empresa_id=empresa.id,
                disrupcion_key=definicion['key']
            ).first()
            if ya_existe:
                continue

            producto = obtener_producto_mas_demandado(empresa)
            nueva = DisrupcionEmpresa(
                simulacion_id=simulacion.id,
                empresa_id=empresa.id,
                disrupcion_key=definicion['key'],
                producto_afectado_id=producto.id if producto else None,
                semana_inicio=dia,
                semana_fin=dia + int(definicion['duracion_semanas'] * 7) - 1,
                activa=True,
            )
            db.session.add(nueva)
            nuevas.append(nueva)

    return nuevas


def verificar_y_expirar_disrupciones(simulacion):
    """
    Marca como inactivas las disrupciones cuya semana_fin quedó en el pasado.
    Retorna las disrupciones recién expiradas para que la UI muestre la notificación.
    """
    expiradas = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.semana_fin < simulacion.dia_actual
    ).all()

    for d in expiradas:
        d.activa = False

    return expiradas


def obtener_efectos_por_empresa(simulacion_id, empresa_id):
    """
    Retorna un dict {producto_id: efectos} con los efectos de disrupción
    activos para la empresa (solo disrupciones con opción elegida).
    """
    from utils.catalogo_disrupciones import CATALOGO_DISRUPCIONES
    cat_dict = {d['key']: d for d in CATALOGO_DISRUPCIONES}

    disrupciones = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.simulacion_id == simulacion_id,
        DisrupcionEmpresa.empresa_id == empresa_id,
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.opcion_elegida != None
    ).all()

    efectos = {}
    for dis in disrupciones:
        cat = cat_dict.get(dis.disrupcion_key)
        if not cat or not dis.producto_afectado_id:
            continue
        opcion = cat['opciones'].get(dis.opcion_elegida)
        if opcion:
            efectos[dis.producto_afectado_id] = {
                'tipo': opcion['efectos']['tipo'],
                'efectos': opcion['efectos'],
                'disrupcion_id': dis.id,
            }
    return efectos


def obtener_efecto_logistico_empresa(simulacion_id, empresa_id):
    """
    Retorna el efecto de falla_flota activo para la empresa, o None.
    A diferencia de las otras disrupciones, este aplica a TODOS los despachos
    (no es específico a un producto).
    """
    from utils.catalogo_disrupciones import get_disrupcion
    dis = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.simulacion_id == simulacion_id,
        DisrupcionEmpresa.empresa_id == empresa_id,
        DisrupcionEmpresa.disrupcion_key == 'falla_flota',
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.opcion_elegida != None
    ).first()
    if not dis:
        return None
    cat = get_disrupcion('falla_flota')
    if not cat:
        return None
    opcion = cat['opciones'].get(dis.opcion_elegida)
    return opcion['efectos'] if opcion else None


def asegurar_metricas_base_dia_uno(simulacion, commit=False):
    """Garantiza métricas base desde el día 1 (nivel de servicio inicial en 100%)."""
    if not simulacion:
        return 0

    empresas = Empresa.query.filter_by(simulacion_id=simulacion.id, activa=True).all()
    creadas = 0

    for empresa in empresas:
        existe = Metrica.query.filter_by(
            empresa_id=empresa.id,
            semana_simulacion=1,
        ).first()
        if existe:
            continue

        db.session.add(Metrica(
            empresa_id=empresa.id,
            semana_simulacion=1,
            ingresos=0,
            costos=0,
            utilidad=0,
            nivel_servicio=100,
            rotacion_inventario=0,
            market_share=0,
        ))
        creadas += 1

    if creadas:
        if commit:
            db.session.commit()
        else:
            db.session.flush()

    return creadas


# ---------------------------------------------------------------------------

def procesar_ventas_semana(simulacion, empresa):
    """
    Procesa ventas del día para una empresa usando la base central de demanda.
    La demanda base por producto/región es idéntica para todas las empresas.
    """
    semana_actual = simulacion.dia_actual
    productos = Producto.query.filter_by(activo=True).all()
    regiones = ['Andina', 'Caribe', 'Pacífica', 'Orinoquía', 'Amazonía']
    ventas_generadas = []

    # Obtener efectos de disrupciones activas una sola vez por empresa
    efectos_disrupcion = obtener_efectos_por_empresa(simulacion.id, empresa.id)

    # Aprobaciones de Ventas para el día (si no hay, se asume 0 aprobado).
    decision_aprobaciones = Decision.query.filter_by(
        empresa_id=empresa.id,
        tipo_decision='ventas_aprobacion_diaria',
        semana_simulacion=semana_actual
    ).order_by(Decision.created_at.desc()).first()

    aprobaciones_map = {}
    if decision_aprobaciones and decision_aprobaciones.datos_decision:
        for item in decision_aprobaciones.datos_decision.get('aprobaciones', []):
            pid = int(item.get('producto_id', 0))
            region = item.get('region')
            cantidad = int(item.get('cantidad_aprobada', 0))
            if pid and region:
                aprobaciones_map[(pid, region)] = max(0, cantidad)

    for producto in productos:
        # Obtener inventario de esta empresa
        inventario = Inventario.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto.id
        ).first()
        
        if not inventario:
            continue
        
        for region in regiones:
            # Demanda base central (misma para todas las empresas en el día)
            cantidad_total_mercado = int(obtener_demanda_base(
                simulacion.id,
                semana_actual,
                producto.id,
                region
            ))
            
            if cantidad_total_mercado <= 0:
                # Registrar venta con 0 demanda
                venta = Venta(
                    empresa_id=empresa.id,
                    producto_id=producto.id,
                    semana_simulacion=semana_actual,
                    region=region,
                    cantidad_solicitada=0,
                    cantidad_vendida=0,
                    cantidad_perdida=0,
                    demanda_mercado_total=0,
                    precio_unitario=producto.precio_actual,
                    ingreso_total=0,
                    costo_unitario=inventario.costo_promedio or producto.costo_unitario,
                    margen=0
                )
                db.session.add(venta)
                ventas_generadas.append(venta)
                continue
            
            # Pedido solicitado por región (desde base central).
            cantidad_solicitada = cantidad_total_mercado

            # Pedido aprobado por Ventas (no puede superar lo solicitado).
            cantidad_aprobada = int(aprobaciones_map.get((producto.id, region), 0))
            cantidad_aprobada = max(0, min(cantidad_aprobada, cantidad_solicitada))
            
            # Procesar venta según stock disponible
            stock_disponible = inventario.cantidad_actual - inventario.cantidad_reservada
            stock_disponible = max(0, stock_disponible)

            # DISRUPCIÓN - efectos sobre demanda, racionamiento y precio
            efecto_d = efectos_disrupcion.get(producto.id)

            # Opción B disrupcion 1: Racionamiento del stock disponible
            if efecto_d and efecto_d['tipo'] == 'racionamiento':
                factor = efecto_d['efectos'].get('limite_ventas_factor', 0.60)
                tope_racionamiento = round(inventario.cantidad_actual * factor)
                stock_disponible = min(stock_disponible, tope_racionamiento)

            # Ventas reales = aprobado por Ventas limitado por stock.
            cantidad_vendida = min(cantidad_aprobada, stock_disponible)

            # Calcular ventas perdidas
            ventas_perdidas_sin_stock = max(0, cantidad_solicitada - cantidad_vendida)
            cantidad_perdida_total = ventas_perdidas_sin_stock

            # Precio unitario — ya actualizado en DB si el equipo eligió Opción D
            precio_unitario = producto.precio_actual
            ingreso_total = cantidad_vendida * precio_unitario
            costo_unitario = inventario.costo_promedio or producto.costo_unitario
            margen = ingreso_total - (cantidad_vendida * costo_unitario)

            # Crear registro de venta con información de competitividad
            venta = Venta(
                empresa_id=empresa.id,
                producto_id=producto.id,
                semana_simulacion=semana_actual,
                region=region,
                cantidad_solicitada=cantidad_solicitada,
                cantidad_vendida=cantidad_vendida,
                cantidad_perdida=cantidad_perdida_total,
                demanda_mercado_total=cantidad_total_mercado,
                precio_unitario=precio_unitario,
                ingreso_total=ingreso_total,
                costo_unitario=costo_unitario,
                margen=margen
            )
            
            db.session.add(venta)
            
            # Actualizar inventario si hubo venta
            if cantidad_vendida > 0:
                saldo_anterior = inventario.cantidad_actual
                inventario.cantidad_actual = max(0, int(round((inventario.cantidad_actual or 0) - cantidad_vendida)))
                
                # Calcular porcentaje de competitividad para el mensaje
                competitividad_msg = ""
                
                # Registrar movimiento de inventario
                movimiento = MovimientoInventario(
                    empresa_id=empresa.id,
                    producto_id=producto.id,
                    usuario_id=None,
                    semana_simulacion=semana_actual,
                    tipo_movimiento='salida_venta',
                    cantidad=cantidad_vendida,
                    saldo_anterior=saldo_anterior,
                    saldo_nuevo=inventario.cantidad_actual,
                    venta_id=None,
                    observaciones=(
                        f'Venta día {semana_actual} - {region} - '
                        f'Solicitado: {cantidad_solicitada}, Aprobado: {cantidad_aprobada}{competitividad_msg}'
                    )
                )
                
                db.session.add(movimiento)
            
            ventas_generadas.append(venta)
    
    return ventas_generadas


def procesar_llegadas_compras(simulacion, empresa):
    """
    Las compras no se recepcionan automáticamente.
    La recepción es responsabilidad del rol de Logística desde su tablero.
    """
    return []


def procesar_despachos_regionales(simulacion, empresa):
    """
    Procesa despachos que llegan a su destino esta semana
    """
    semana_actual = simulacion.dia_actual
    
    # Obtener despachos que llegan este día
    despachos_llegan = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        semana_entrega_estimado=semana_actual,
        estado='en_transito'
    ).all()
    
    for despacho in despachos_llegan:
        despacho.estado = 'entregado'
        despacho.semana_entrega_real = semana_actual
        # El inventario ya fue reducido en cantidad_actual al crear el despacho;
        # no hay cantidad_reservada que liberar para despachos.
    
    return despachos_llegan


def calcular_costos_operativos(simulacion, empresa):
    """
    Calcula y aplica costos operativos automáticos diarios:
    - Costos fijos: $800,000/día
    - Mantenimiento de inventario: 0.3% del valor del inventario/día
    - Penalización por ventas perdidas: 30% del precio de las unidades no vendidas
    
    Retorna un diccionario con el desglose de costos
    """
    semana_actual = simulacion.dia_actual
    
    # 1. COSTOS FIJOS OPERACIONALES ($800,000/semana → $114,286/día)
    costos_fijos = round(800000 / 7)
    
    # 2. COSTOS DE MANTENIMIENTO DE INVENTARIO (0.3%/semana → 0.0429%/día)
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    valor_inventario = sum(
        inv.cantidad_actual * (inv.costo_promedio or 0) for inv in inventarios
    )
    costos_mantenimiento = valor_inventario * (0.003 / 7)  # tasa diaria
    
    # 2.1 PENALIZACIÓN POR SOBRESTOCK ($1000 por unidad excedente)
    penalizacion_sobrestock = 0
    for inv in inventarios:
        if inv.producto.stock_maximo and inv.cantidad_actual > inv.producto.stock_maximo:
            exceso = inv.cantidad_actual - inv.producto.stock_maximo
            penalizacion_sobrestock += exceso * 1000
    
    costos_mantenimiento += penalizacion_sobrestock
    
    # 3. PENALIZACIÓN POR VENTAS PERDIDAS (30% del precio)
    ventas_dia = Venta.query.filter_by(
        empresa_id=empresa.id,
        semana_simulacion=semana_actual
    ).all()
    
    penalizacion_ventas_perdidas = 0
    for venta in ventas_dia:
        cantidad_perdida = venta.cantidad_solicitada - venta.cantidad_vendida
        if cantidad_perdida > 0:
            # Obtener precio actual del producto
            producto = Producto.query.get(venta.producto_id)
            precio_venta = producto.precio_actual if producto else 0
            penalizacion_ventas_perdidas += cantidad_perdida * precio_venta * 0.30  # 30% del precio
    
    # APLICAR COSTOS AL CAPITAL
    costo_total = costos_fijos + costos_mantenimiento + penalizacion_ventas_perdidas
    empresa.capital_actual -= costo_total

    # Retornar desglose para métricas
    return {
        'costo_total': costo_total,
        'costos_fijos': costos_fijos,
        'costos_mantenimiento': costos_mantenimiento - penalizacion_sobrestock,
        'penalizacion_sobrestock': penalizacion_sobrestock,
        'penalizacion_ventas_perdidas': penalizacion_ventas_perdidas,
        'valor_inventario': valor_inventario
    }


def calcular_metricas_semana(simulacion, empresa, costos_operativos=None):
    """
    Calcula las métricas de desempeño de la semana incluyendo costos operativos
    """
    semana_actual = simulacion.dia_actual
    
    # Obtener ventas del día
    ventas_dia = Venta.query.filter_by(
        empresa_id=empresa.id,
        semana_simulacion=semana_actual
    ).all()
    
    # Calcular totales
    ingresos = sum(v.ingreso_total for v in ventas_dia)
    costos_ventas = sum(v.cantidad_vendida * v.costo_unitario for v in ventas_dia)
    
    # Obtener compras del día (órdenes creadas hoy)
    compras_dia = Compra.query.filter_by(
        empresa_id=empresa.id,
        semana_orden=semana_actual
    ).all()
    
    costos_compras = sum(c.costo_total for c in compras_dia)

    # Costos de transporte de despachos realizados esta semana
    despachos_dia = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        semana_despacho=semana_actual
    ).all()
    costos_transporte = sum(d.costo_transporte or 0 for d in despachos_dia)

    # Calcular nivel de servicio ACUMULATIVO (todo el historial de la simulación)
    ventas_historicas = Venta.query.filter_by(
        empresa_id=empresa.id
    ).filter(
        Venta.semana_simulacion <= semana_actual
    ).all()
    
    total_solicitado_historico = sum(v.cantidad_solicitada for v in ventas_historicas)
    total_vendido_historico = sum(v.cantidad_vendida for v in ventas_historicas)
    
    # Nivel de servicio acumulativo: ventas totales / demanda total
    nivel_servicio = (total_vendido_historico / total_solicitado_historico * 100) if total_solicitado_historico > 0 else 100
    
    # Calcular valor del inventario
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    valor_inventario = sum(
        inv.cantidad_actual * (inv.costo_promedio or 0) for inv in inventarios
    )
    
    # Calcular rotación de inventario (anualizada)
    rotacion_inventario = (costos_ventas / valor_inventario * 365) if valor_inventario > 0 else 0
    
    # Sumar costos operativos automáticos si existen
    costos_operativos_total = 0
    if costos_operativos:
        costos_operativos_total = costos_operativos.get('costo_total', 0)

    # Actualizar capital de la empresa:
    #  + ingresos por ventas
    #  - costos transporte (despachos de esta semana)
    # NOTA: costos_compras ya fueron descontados al crear la orden (routes/estudiante.py)
    #       costos_operativos ya fueron descontados en calcular_costos_operativos()
    empresa.capital_actual += (ingresos - costos_transporte)

    # Métricas P&L: los costos de compra son movimiento de balance (capital → inventario),
    # NO gastos del periodo. Solo se registran costos del periodo:
    #  costos_ventas (COGS) + operativos + transporte
    costos_periodo = costos_ventas + costos_operativos_total + costos_transporte
    utilidad_periodo = ingresos - costos_periodo

    # Crear registro de métrica
    metrica = Metrica(
        empresa_id=empresa.id,
        semana_simulacion=semana_actual,
        ingresos=ingresos,
        costos=costos_periodo,
        utilidad=utilidad_periodo,
        nivel_servicio=nivel_servicio,
        rotacion_inventario=rotacion_inventario,
        market_share=0
    )
    
    db.session.add(metrica)
    
    return metrica


def verificar_alertas_inventario(empresa):
    """
    Verifica niveles de inventario y genera alertas
    """
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    alertas = []
    
    for inv in inventarios:
        # Alerta de stock bajo
        if inv.cantidad_actual <= inv.stock_seguridad:
            alertas.append({
                'tipo': 'critico',
                'producto': inv.producto.nombre,
                'mensaje': f'Stock crítico: {inv.cantidad_actual:.0f} unidades (Seguridad: {inv.stock_seguridad:.0f})'
            })
        elif inv.cantidad_actual <= inv.punto_reorden:
            alertas.append({
                'tipo': 'advertencia',
                'producto': inv.producto.nombre,
                'mensaje': f'Stock bajo punto de reorden: {inv.cantidad_actual:.0f} unidades (Reorden: {inv.punto_reorden:.0f})'
            })
        
        # Alerta de sobrestock (más del 300% del punto de reorden)
        if inv.punto_reorden > 0 and inv.cantidad_actual > (inv.punto_reorden * 3):
            alertas.append({
                'tipo': 'info',
                'producto': inv.producto.nombre,
                'mensaje': f'Sobrestock: {inv.cantidad_actual:.0f} unidades (excede 3x punto de reorden)'
            })
    
    return alertas


def _actualizar_market_share(simulacion, dia, empresas):
    """Calcula y persiste la cuota de mercado (%) por ingresos para cada empresa en el día."""
    ids_empresas = [e.id for e in empresas]
    total_ingresos = db.session.query(func.sum(Venta.ingreso_total)).filter(
        Venta.semana_simulacion == dia,
        Venta.empresa_id.in_(ids_empresas)
    ).scalar() or 0
    for empresa in empresas:
        ingresos_e = db.session.query(func.sum(Venta.ingreso_total)).filter(
            Venta.empresa_id == empresa.id,
            Venta.semana_simulacion == dia
        ).scalar() or 0
        share = round(ingresos_e / total_ingresos * 100, 2) if total_ingresos > 0 else 0
        metrica = Metrica.query.filter_by(empresa_id=empresa.id, semana_simulacion=dia).first()
        if metrica:
            metrica.market_share = share


def procesar_semana_completa(simulacion):
    """
    Procesa una semana completa de la simulación para todas las empresas
    
    Returns:
        dict con resumen del procesamiento
    """
    semana_actual = simulacion.dia_actual
    empresas = Empresa.query.filter_by(
        simulacion_id=simulacion.id, activa=True
    ).all()

    resumen = {
        'semana': semana_actual,   # contiene dia_actual
        'empresas_procesadas': 0,
        'total_ventas': 0,
        'total_compras_recibidas': 0,
        'total_despachos_entregados': 0,
        'alertas': []
    }
    
    for empresa in empresas:
        # 1. Procesar ventas de la semana
        ventas = procesar_ventas_semana(simulacion, empresa)
        resumen['total_ventas'] += len(ventas)
        
        # 2. Procesar llegadas de compras
        compras_recibidas = procesar_llegadas_compras(simulacion, empresa)
        resumen['total_compras_recibidas'] += len(compras_recibidas)
        
        # 3. Procesar despachos regionales
        despachos_entregados = procesar_despachos_regionales(simulacion, empresa)
        resumen['total_despachos_entregados'] += len(despachos_entregados)
        
        # 4. APLICAR COSTOS OPERATIVOS AUTOMÁTICOS
        costos_operativos = calcular_costos_operativos(simulacion, empresa)
        
        # 5. Calcular métricas de la semana (incluyendo costos operativos)
        metrica = calcular_metricas_semana(simulacion, empresa, costos_operativos)
        
        # 6. Verificar alertas de inventario
        alertas_empresa = verificar_alertas_inventario(empresa)
        if alertas_empresa:
            resumen['alertas'].append({
                'empresa': empresa.nombre,
                'alertas': alertas_empresa
            })
        
        resumen['empresas_procesadas'] += 1
    
    # Actualizar market share al finalizar el procesamiento de todas las empresas
    _actualizar_market_share(simulacion, semana_actual, empresas)

    # Commit de todos los cambios
    db.session.commit()
    
    return resumen


def avanzar_simulacion():
    """
    Avanza la simulación a la siguiente semana y procesa todos los eventos

    Returns:
        tuple: (success: bool, mensaje: str, resumen: dict)
    """
    try:
        simulacion = Simulacion.query.filter_by(activa=True).first()

        if not simulacion:
            return False, "No existe una simulación activa", None

        if simulacion.estado != 'en_curso':
            return False, "La simulación debe estar en curso para avanzar", None

        # Procesar el día actual primero (incluye día 1 en el primer avance)
        dia_procesado = simulacion.dia_actual
        semana_procesada = (dia_procesado - 1) // 7 + 1

        cobertura_ok, cobertura_msg = validar_cobertura_demanda_dia(simulacion.id, dia_procesado)
        if not cobertura_ok:
            db.session.rollback()
            return False, cobertura_msg, None

        # Expirar disrupciones cuya duración ya terminó
        expiradas = verificar_y_expirar_disrupciones(simulacion)

        # Procesar día completo (los efectos activos se consultan dentro)
        resumen = procesar_semana_completa(simulacion)

        # Activar nuevas disrupciones que tienen semana_trigger == semana actual
        nuevas = verificar_y_activar_disrupciones(simulacion)

        resumen['disrupciones_activadas'] = len(nuevas)
        resumen['disrupciones_expiradas'] = len(expiradas)

        # Avanzar al siguiente día una vez finaliza el procesamiento actual.
        simulacion.dia_actual = dia_procesado + 1
        simulacion.semana_actual = (simulacion.dia_actual - 1) // 7 + 1

        db.session.commit()

        mensaje = (f"✅ Día {dia_procesado} (Semana {semana_procesada}) procesado exitosamente. "
                   f"Siguiente día: {simulacion.dia_actual} (Semana {simulacion.semana_actual})")
        if nuevas:
            mensaje += f" | ⚠️ {len(nuevas)} nueva(s) disrupción(es) activada(s)"

        return True, mensaje, resumen

    except Exception as e:
        db.session.rollback()
        return False, f"Error al avanzar simulación: {str(e)}", None


def obtener_resumen_simulacion(simulacion):
    """
    Obtiene un resumen del estado actual de la simulación
    """
    empresas = Empresa.query.filter_by(activa=True, simulacion_id=simulacion.id).all()

    resumen = {
        'dia_actual': simulacion.dia_actual,
        'semana_actual': simulacion.semana_actual,
        'estado': simulacion.estado,
        'empresas': []
    }

    for empresa in empresas:
        # Métricas del día anterior
        metrica_reciente = Metrica.query.filter_by(
            empresa_id=empresa.id,
            semana_simulacion=simulacion.dia_actual - 1
        ).first()
        
        # Métricas acumuladas
        metricas_totales = db.session.query(
            db.func.sum(Metrica.ingresos).label('ingresos_totales'),
            db.func.sum(Metrica.utilidad).label('utilidad_total'),
            db.func.avg(Metrica.nivel_servicio).label('nivel_servicio_promedio')
        ).filter_by(empresa_id=empresa.id).first()
        
        # Stock total
        inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
        valor_inventario = sum(
            inv.cantidad_actual * (inv.costo_promedio or 0) for inv in inventarios
        )
        
        resumen['empresas'].append({
            'id': empresa.id,
            'nombre': empresa.nombre,
            'capital_actual': empresa.capital_actual,
            'capital_inicial': empresa.capital_inicial,
            'valor_inventario': valor_inventario,
            'ingresos_totales': metricas_totales.ingresos_totales or 0,
            'utilidad_total': metricas_totales.utilidad_total or 0,
            'nivel_servicio_promedio': metricas_totales.nivel_servicio_promedio or 0,
            'utilidad_dia': metrica_reciente.utilidad if metrica_reciente else 0
        })
    
    return resumen
