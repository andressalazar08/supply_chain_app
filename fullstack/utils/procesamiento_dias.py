"""
Utilidades para procesamiento automático de semanas de simulación
"""

from models import (Simulacion, Empresa, Producto, Inventario, Venta, Compra,
                    DespachoRegional, MovimientoInventario, Metrica, DisrupcionEmpresa)
from extensions import db
from datetime import datetime
import random
from sqlalchemy import func


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
    
    # Calcular precio promedio (solo de empresas con stock > 0)
    precios_validos = [p['precio'] for p in precios_mercado if p['stock'] > 0]
    precio_promedio = sum(precios_validos) / len(precios_validos) if precios_validos else 0
    
    return precio_promedio, precios_mercado


def calcular_market_share(precio_empresa, precio_promedio, stock_disponible, elasticidad):
    """
    Calcula el porcentaje de market share que recibe una empresa
    basado en su precio relativo al mercado y disponibilidad de stock
    
    Retorna: porcentaje de 0 a 1
    """
    if stock_disponible <= 0:
        return 0.0  # Sin stock = sin ventas
    
    if precio_promedio <= 0:
        return 1.0 / max(1, stock_disponible)  # Distribuir equitativamente si no hay referencia
    
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
        market_share = 0.4 + random.uniform(-0.1, 0.1)
    
    # Agregar factor de aleatoriedad (comportamiento de consumidor)
    market_share += random.uniform(-0.05, 0.05)
    
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
            
        # Calcular demanda asignada a esta empresa
        demanda_empresa = round(demanda_total * ms['market_share'])
        
        # Limitar por stock disponible
        cantidad_asignada = min(demanda_empresa, ms['stock'], demanda_restante)
        
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

    semana = simulacion.semana_actual
    empresas = Empresa.query.filter_by(activa=True, simulacion_id=simulacion.id).all()
    nuevas = []

    for definicion in CATALOGO_DISRUPCIONES:
        if definicion['semana_trigger'] > semana:
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
                semana_inicio=semana,
                semana_fin=semana + definicion['duracion_semanas'] - 1,
                activa=True,
            )
            db.session.add(nueva)
            nuevas.append(nueva)

    return nuevas


def verificar_y_expirar_disrupciones(simulacion):
    """
    Marca como inactivas las disrupciones cuya semana_fin quedó en el pasado.
    Revierte efectos permanentes (ej: precio Opción D) antes de desactivarlas.
    Retorna las disrupciones recién expiradas para que la UI muestre la notificación.
    """
    from models import Producto
    expiradas = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.semana_fin < simulacion.semana_actual
    ).all()

    for d in expiradas:
        # Revertir precio si hubo Opción D en disrupcion aumento_demanda
        if (d.disrupcion_key == 'aumento_demanda'
                and d.opcion_elegida == 'D'
                and d.producto_afectado_id
                and d.datos_extra
                and 'precio_original' in d.datos_extra):
            producto = Producto.query.get(d.producto_afectado_id)
            if producto:
                producto.precio_actual = d.datos_extra['precio_original']
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


# ---------------------------------------------------------------------------

def procesar_ventas_semana(simulacion, empresa):
    """
    Procesa las ventas de la semana para una empresa usando motor de competencia
    La demanda se distribuye entre empresas según precios y disponibilidad
    """
    semana_actual = simulacion.semana_actual
    productos = Producto.query.filter_by(activo=True).all()
    regiones = ['Andina', 'Caribe', 'Pacífica', 'Orinoquía', 'Amazonía']
    ventas_generadas = []

    # Obtener efectos de disrupciones activas una sola vez por empresa
    efectos_disrupcion = obtener_efectos_por_empresa(simulacion.id, empresa.id)

    for producto in productos:
        # Obtener inventario de esta empresa
        inventario = Inventario.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto.id
        ).first()
        
        if not inventario:
            continue
        
        for region in regiones:
            # DEMANDA MÍNIMA GARANTIZADA: Cada empresa DEBE atender esta demanda base
            # Esto garantiza que el nivel de servicio refleje capacidad real
            demanda_base_empresa = producto.demanda_promedio * 0.6  # 60% de la demanda promedio
            
            # Generar demanda TOTAL del mercado (para distribución competitiva)
            demanda_mercado_base = random.gauss(producto.demanda_promedio, producto.desviacion_demanda)
            demanda_mercado_base = max(0, demanda_mercado_base)
            
            cantidad_total_mercado = round(demanda_mercado_base)
            
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
                    precio_unitario=producto.precio_actual,
                    ingreso_total=0,
                    costo_unitario=inventario.costo_promedio or producto.costo_unitario,
                    margen=0
                )
                db.session.add(venta)
                ventas_generadas.append(venta)
                continue
            
            # DISTRIBUIR LA DEMANDA ENTRE TODAS LAS EMPRESAS COMPETIDORAS
            asignaciones, precio_promedio = distribuir_demanda_competitiva(
                simulacion, producto, region, cantidad_total_mercado, semana_actual
            )
            
            # Buscar la asignación para ESTA empresa
            asignacion_empresa = None
            for asig in asignaciones:
                if asig['empresa_id'] == empresa.id:
                    asignacion_empresa = asig
                    break
            
            # Determinar cuánta demanda recibió esta empresa
            # SIEMPRE asignar la demanda mínima garantizada + demanda competitiva
            cantidad_solicitada_minima = round(demanda_base_empresa)  # Demanda que DEBE atender
            
            if asignacion_empresa:
                # Demanda competitiva adicional basada en precio y disponibilidad
                cantidad_adicional_competitiva = asignacion_empresa['cantidad']
                cantidad_solicitada = cantidad_solicitada_minima + cantidad_adicional_competitiva
                market_share_obtenido = asignacion_empresa['market_share']
            else:
                # Esta empresa no recibió demanda competitiva, pero SÍ tiene demanda mínima
                cantidad_solicitada = cantidad_solicitada_minima
                market_share_obtenido = 0
            
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

            # Disrupcion 2 Opciones A y B: multiplicador de demanda
            if efecto_d and efecto_d['tipo'] == 'aumento_demanda':
                mult = efecto_d['efectos'].get('demanda_multiplicador', 1.0)
                cantidad_solicitada = round(cantidad_solicitada * mult)

            # Disrupcion 2 Opcion D: menor demanda por precio alto
            if efecto_d and efecto_d['tipo'] == 'aumento_precio_demanda':
                mult_d = efecto_d['efectos'].get('demanda_multiplicador', 0.90)
                cantidad_solicitada = round(cantidad_solicitada * mult_d)

            cantidad_vendida = min(cantidad_solicitada, stock_disponible)

            # Calcular ventas perdidas
            ventas_perdidas_sin_stock = max(0, cantidad_solicitada - cantidad_vendida)
            ratio_precio = producto.precio_actual / precio_promedio if precio_promedio > 0 else 1.0
            ventas_perdidas_precio = 0
            if stock_disponible > 0 and cantidad_solicitada == 0 and ratio_precio > 1.2:
                ventas_perdidas_precio = round(cantidad_total_mercado * 0.15)
            cantidad_perdida_total = ventas_perdidas_sin_stock + ventas_perdidas_precio

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
                precio_unitario=precio_unitario,
                ingreso_total=ingreso_total,
                costo_unitario=costo_unitario,
                margen=margen
            )
            
            db.session.add(venta)
            
            # Actualizar inventario si hubo venta
            if cantidad_vendida > 0:
                saldo_anterior = inventario.cantidad_actual
                inventario.cantidad_actual -= cantidad_vendida
                
                # Calcular porcentaje de competitividad para el mensaje
                competitividad_msg = ""
                if precio_promedio > 0:
                    if ratio_precio > 1.5:
                        competitividad_msg = f" - Precio 50%+ sobre mercado (${precio_promedio:,.0f})"
                    elif ratio_precio > 1.2:
                        competitividad_msg = f" - Precio alto vs mercado (${precio_promedio:,.0f})"
                    elif ratio_precio < 0.8:
                        competitividad_msg = f" - Precio muy competitivo vs mercado (${precio_promedio:,.0f})"
                
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
                    observaciones=f'Venta semana {semana_actual} - {region} - Market share: {market_share_obtenido*100:.1f}%{competitividad_msg}'
                )
                
                db.session.add(movimiento)
            
            ventas_generadas.append(venta)
    
    return ventas_generadas


def procesar_llegadas_compras(simulacion, empresa):
    """
    Procesa las llegadas de órdenes de compra programadas para esta semana
    """
    semana_actual = simulacion.semana_actual
    
    # Obtener órdenes que llegan esta semana
    ordenes_llegan = Compra.query.filter_by(
        empresa_id=empresa.id,
        semana_entrega=semana_actual,
        estado='en_transito'
    ).all()
    
    ordenes_recibidas = []
    
    for orden in ordenes_llegan:
        # Obtener inventario
        inventario = Inventario.query.filter_by(
            empresa_id=empresa.id,
            producto_id=orden.producto_id
        ).first()
        
        if inventario:
            # Calcular nuevo costo promedio ponderado
            stock_actual = inventario.cantidad_actual
            costo_actual = inventario.costo_promedio or 0
            
            nueva_cantidad = stock_actual + orden.cantidad
            if nueva_cantidad > 0:
                nuevo_costo_promedio = (
                    (stock_actual * costo_actual + orden.cantidad * orden.costo_unitario) / nueva_cantidad
                )
            else:
                nuevo_costo_promedio = orden.costo_unitario
            
            # Actualizar inventario
            saldo_anterior = inventario.cantidad_actual
            inventario.cantidad_actual = nueva_cantidad
            inventario.costo_promedio = nuevo_costo_promedio
            
            # Registrar movimiento
            movimiento = MovimientoInventario(
                empresa_id=empresa.id,
                producto_id=orden.producto_id,
                usuario_id=None,  # Automático
                semana_simulacion=semana_actual,
                tipo_movimiento='entrada_compra',
                cantidad=orden.cantidad,
                saldo_anterior=saldo_anterior,
                saldo_nuevo=inventario.cantidad_actual,
                compra_id=orden.id,
                observaciones=f'Recepción automática semana {semana_actual}'
            )
            
            db.session.add(movimiento)
            
            # Actualizar estado de la orden
            orden.estado = 'recibido'
            
            ordenes_recibidas.append(orden)
    
    return ordenes_recibidas


def procesar_despachos_regionales(simulacion, empresa):
    """
    Procesa despachos que llegan a su destino esta semana
    """
    semana_actual = simulacion.semana_actual
    
    # Obtener despachos que llegan esta semana
    despachos_llegan = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        semana_entrega_estimado=semana_actual,
        estado='en_transito'
    ).all()
    
    for despacho in despachos_llegan:
        despacho.estado = 'entregado'
        despacho.semana_entrega_real = semana_actual
        
        # Liberar cantidad reservada
        inventario = Inventario.query.filter_by(
            empresa_id=empresa.id,
            producto_id=despacho.producto_id
        ).first()
        
        if inventario:
            inventario.cantidad_reservada = max(0, inventario.cantidad_reservada - despacho.cantidad)
    
    return despachos_llegan


def calcular_costos_operativos(simulacion, empresa):
    """
    Calcula y aplica costos operativos automáticos diarios:
    - Costos fijos: $800,000/día
    - Mantenimiento de inventario: 0.3% del valor del inventario/día
    - Penalización por ventas perdidas: 30% del precio de las unidades no vendidas
    
    Retorna un diccionario con el desglose de costos
    """
    semana_actual = simulacion.semana_actual
    
    # 1. COSTOS FIJOS OPERACIONALES ($800,000/día)
    costos_fijos = 800000
    
    # 2. COSTOS DE MANTENIMIENTO DE INVENTARIO (0.3% del valor)
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    valor_inventario = sum(
        inv.cantidad_actual * (inv.costo_promedio or 0) for inv in inventarios
    )
    costos_mantenimiento = valor_inventario * 0.003  # 0.3%
    
    # 2.1 PENALIZACIÓN POR SOBRESTOCK (0.5% adicional sobre el exceso)
    penalizacion_sobrestock = 0
    for inv in inventarios:
        if inv.producto.stock_maximo and inv.cantidad_actual > inv.producto.stock_maximo:
            exceso = inv.cantidad_actual - inv.producto.stock_maximo
            valor_exceso = exceso * (inv.costo_promedio or 0)
            penalizacion_sobrestock += valor_exceso * 0.005  # 0.5% adicional
    
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
    semana_actual = simulacion.semana_actual
    
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
    
    # Calcular rotación de inventario (simplificado)
    rotacion_inventario = (costos_ventas / valor_inventario) if valor_inventario > 0 else 0
    
    # Sumar costos operativos automáticos si existen
    costos_operativos_total = 0
    if costos_operativos:
        costos_operativos_total = costos_operativos.get('costo_total', 0)
    
    # Actualizar capital de la empresa (ingresos - compras)
    # Los costos operativos ya fueron descontados en calcular_costos_operativos()
    empresa.capital_actual += (ingresos - costos_compras)
    
    # Crear registro de métrica con todos los costos
    metrica = Metrica(
        empresa_id=empresa.id,
        semana_simulacion=semana_actual,
        ingresos=ingresos,
        costos=costos_ventas + costos_compras + costos_operativos_total,
        utilidad=ingresos - costos_ventas - costos_operativos_total,
        nivel_servicio=nivel_servicio,
        rotacion_inventario=rotacion_inventario
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


def procesar_semana_completa(simulacion):
    """
    Procesa una semana completa de la simulación para todas las empresas
    
    Returns:
        dict con resumen del procesamiento
    """
    semana_actual = simulacion.semana_actual
    empresas = Empresa.query.filter_by(activa=True).all()
    
    resumen = {
        'semana': semana_actual,
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

        # Incrementar semana
        semana_anterior = simulacion.semana_actual
        simulacion.semana_actual += 1

        # Expirar disrupciones cuya duración ya terminó
        expiradas = verificar_y_expirar_disrupciones(simulacion)

        # Procesar semana completa (los efectos activos se consultan dentro)
        resumen = procesar_semana_completa(simulacion)

        # Activar nuevas disrupciones que tienen semana_trigger == semana actual
        nuevas = verificar_y_activar_disrupciones(simulacion)

        resumen['disrupciones_activadas'] = len(nuevas)
        resumen['disrupciones_expiradas'] = len(expiradas)

        db.session.commit()

        mensaje = f"✅ Semana {semana_anterior} → Semana {simulacion.semana_actual} procesada exitosamente"
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
        'semana_actual': simulacion.semana_actual,
        'estado': simulacion.estado,
        'empresas': []
    }

    for empresa in empresas:
        # Métricas de la semana anterior
        metrica_reciente = Metrica.query.filter_by(
            empresa_id=empresa.id,
            semana_simulacion=simulacion.semana_actual - 1
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
