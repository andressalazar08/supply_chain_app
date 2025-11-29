"""
Utilidades para procesamiento automático de días de simulación
"""

from models import (Simulacion, Empresa, Producto, Inventario, Venta, Compra, 
                    DespachoRegional, MovimientoInventario, Metrica, DisrupcionActiva)
from extensions import db
from datetime import datetime
import random
from utils.disrupciones import (
    calcular_impacto_demanda, calcular_impacto_lead_time,
    obtener_disrupciones_activas_empresa
)


def procesar_ventas_dia(simulacion, empresa):
    """
    Procesa las ventas del día para una empresa
    Genera demanda aleatoria y procesa ventas según disponibilidad
    """
    dia_actual = simulacion.dia_actual
    productos = Producto.query.filter_by(activo=True).all()
    regiones = ['Andina', 'Caribe', 'Pacífica', 'Orinoquía', 'Amazonía']
    
    # Obtener disrupciones activas
    disrupciones_activas = obtener_disrupciones_activas_empresa(simulacion, empresa.id, dia_actual)
    
    ventas_generadas = []
    
    for producto in productos:
        # Obtener inventario
        inventario = Inventario.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto.id
        ).first()
        
        if not inventario:
            continue
        
        for region in regiones:
            # Generar demanda base con variabilidad
            demanda_base = random.gauss(producto.demanda_promedio, producto.desviacion_demanda)
            demanda_base = max(0, demanda_base)  # No negativa
            
            # Aplicar impacto de disrupciones
            demanda_ajustada = calcular_impacto_demanda(
                producto.id, region, demanda_base, dia_actual, disrupciones_activas
            )
            
            cantidad_solicitada = round(demanda_ajustada)
            
            if cantidad_solicitada <= 0:
                continue
            
            # Procesar venta según stock disponible
            stock_disponible = inventario.cantidad_actual
            cantidad_vendida = min(cantidad_solicitada, stock_disponible)
            
            # Calcular valores
            precio_unitario = producto.precio_actual
            ingreso_total = cantidad_vendida * precio_unitario
            costo_unitario = inventario.costo_promedio or producto.costo_unitario
            margen = ingreso_total - (cantidad_vendida * costo_unitario)
            
            # Crear registro de venta
            venta = Venta(
                empresa_id=empresa.id,
                producto_id=producto.id,
                dia_simulacion=dia_actual,
                region=region,
                cantidad_solicitada=cantidad_solicitada,
                cantidad_vendida=cantidad_vendida,
                cantidad_perdida=cantidad_solicitada - cantidad_vendida,
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
                
                # Registrar movimiento de inventario
                movimiento = MovimientoInventario(
                    empresa_id=empresa.id,
                    producto_id=producto.id,
                    usuario_id=None,  # Automático del sistema
                    dia_simulacion=dia_actual,
                    tipo_movimiento='salida_venta',
                    cantidad=cantidad_vendida,
                    saldo_anterior=saldo_anterior,
                    saldo_nuevo=inventario.cantidad_actual,
                    venta_id=None,  # Se actualizará después del commit
                    observaciones=f'Venta automática día {dia_actual} - Región {region}'
                )
                
                db.session.add(movimiento)
            
            ventas_generadas.append(venta)
    
    return ventas_generadas


def procesar_llegadas_compras(simulacion, empresa):
    """
    Procesa las llegadas de órdenes de compra programadas para hoy
    """
    dia_actual = simulacion.dia_actual
    
    # Obtener órdenes que llegan hoy
    ordenes_llegan = Compra.query.filter_by(
        empresa_id=empresa.id,
        dia_entrega=dia_actual,
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
                dia_simulacion=dia_actual,
                tipo_movimiento='entrada_compra',
                cantidad=orden.cantidad,
                saldo_anterior=saldo_anterior,
                saldo_nuevo=inventario.cantidad_actual,
                compra_id=orden.id,
                observaciones=f'Recepción automática día {dia_actual}'
            )
            
            db.session.add(movimiento)
            
            # Actualizar estado de la orden
            orden.estado = 'recibido'
            
            ordenes_recibidas.append(orden)
    
    return ordenes_recibidas


def procesar_despachos_regionales(simulacion, empresa):
    """
    Procesa despachos que llegan a su destino hoy
    """
    dia_actual = simulacion.dia_actual
    
    # Obtener despachos que llegan hoy
    despachos_llegan = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        dia_entrega_estimado=dia_actual,
        estado='en_transito'
    ).all()
    
    for despacho in despachos_llegan:
        despacho.estado = 'entregado'
        despacho.dia_entrega_real = dia_actual
        
        # Liberar cantidad reservada
        inventario = Inventario.query.filter_by(
            empresa_id=empresa.id,
            producto_id=despacho.producto_id
        ).first()
        
        if inventario:
            inventario.cantidad_reservada = max(0, inventario.cantidad_reservada - despacho.cantidad)
    
    return despachos_llegan


def calcular_metricas_dia(simulacion, empresa):
    """
    Calcula las métricas de desempeño del día
    """
    dia_actual = simulacion.dia_actual
    
    # Obtener ventas del día
    ventas_dia = Venta.query.filter_by(
        empresa_id=empresa.id,
        dia_simulacion=dia_actual
    ).all()
    
    # Calcular totales
    ingresos = sum(v.ingreso_total for v in ventas_dia)
    costos_ventas = sum(v.cantidad_vendida * v.costo_unitario for v in ventas_dia)
    
    # Obtener compras del día (órdenes creadas hoy)
    compras_dia = Compra.query.filter_by(
        empresa_id=empresa.id,
        dia_orden=dia_actual
    ).all()
    
    costos_compras = sum(c.costo_total for c in compras_dia)
    
    # Calcular nivel de servicio
    total_solicitado = sum(v.cantidad_solicitada for v in ventas_dia)
    total_vendido = sum(v.cantidad_vendida for v in ventas_dia)
    nivel_servicio = (total_vendido / total_solicitado * 100) if total_solicitado > 0 else 100
    
    # Calcular valor del inventario
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    valor_inventario = sum(
        inv.cantidad_actual * (inv.costo_promedio or 0) for inv in inventarios
    )
    
    # Calcular rotación de inventario (simplificado)
    rotacion_inventario = (costos_ventas / valor_inventario) if valor_inventario > 0 else 0
    
    # Actualizar capital de la empresa
    empresa.capital_actual += (ingresos - costos_compras)
    
    # Crear registro de métrica
    metrica = Metrica(
        empresa_id=empresa.id,
        dia_simulacion=dia_actual,
        ingresos=ingresos,
        costos=costos_ventas + costos_compras,
        utilidad=ingresos - costos_ventas,
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


def procesar_dia_completo(simulacion):
    """
    Procesa un día completo de la simulación para todas las empresas
    
    Returns:
        dict con resumen del procesamiento
    """
    dia_actual = simulacion.dia_actual
    empresas = Empresa.query.filter_by(activa=True).all()
    
    resumen = {
        'dia': dia_actual,
        'empresas_procesadas': 0,
        'total_ventas': 0,
        'total_compras_recibidas': 0,
        'total_despachos_entregados': 0,
        'alertas': []
    }
    
    for empresa in empresas:
        # 1. Procesar ventas del día
        ventas = procesar_ventas_dia(simulacion, empresa)
        resumen['total_ventas'] += len(ventas)
        
        # 2. Procesar llegadas de compras
        compras_recibidas = procesar_llegadas_compras(simulacion, empresa)
        resumen['total_compras_recibidas'] += len(compras_recibidas)
        
        # 3. Procesar despachos regionales
        despachos_entregados = procesar_despachos_regionales(simulacion, empresa)
        resumen['total_despachos_entregados'] += len(despachos_entregados)
        
        # 4. Calcular métricas del día
        metrica = calcular_metricas_dia(simulacion, empresa)
        
        # 5. Verificar alertas de inventario
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
    Avanza la simulación al siguiente día y procesa todos los eventos
    
    Returns:
        tuple: (success: bool, mensaje: str, resumen: dict)
    """
    try:
        simulacion = Simulacion.query.first()
        
        if not simulacion:
            return False, "No existe una simulación activa", None
        
        if simulacion.estado != 'en_curso':
            return False, "La simulación debe estar en curso para avanzar", None
        
        # Incrementar día
        dia_anterior = simulacion.dia_actual
        simulacion.dia_actual += 1
        
        # Procesar día completo
        resumen = procesar_dia_completo(simulacion)
        
        mensaje = f"✅ Día {dia_anterior} → Día {simulacion.dia_actual} procesado exitosamente"
        
        return True, mensaje, resumen
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error al avanzar simulación: {str(e)}", None


def obtener_resumen_simulacion(simulacion):
    """
    Obtiene un resumen del estado actual de la simulación
    """
    empresas = Empresa.query.filter_by(activa=True).all()
    
    resumen = {
        'dia_actual': simulacion.dia_actual,
        'estado': simulacion.estado,
        'empresas': []
    }
    
    for empresa in empresas:
        # Métricas del último día
        metrica_reciente = Metrica.query.filter_by(
            empresa_id=empresa.id,
            dia_simulacion=simulacion.dia_actual - 1
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
