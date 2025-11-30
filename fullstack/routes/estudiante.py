"""
Rutas para el rol Estudiante
Dashboard diferenciado según rol: Ventas, Planeación, Compras, Logística
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import (Usuario, Empresa, Simulacion, Inventario, Venta, Compra, Decision, 
                    Producto, Pronostico, RequerimientoCompra, MovimientoInventario, DespachoRegional, DisrupcionActiva)
from extensions import db
from datetime import datetime
from utils.pronosticos import (
    promedio_movil, suavizacion_exponencial_simple, suavizacion_exponencial_doble_holt,
    comparar_metodos, obtener_mejor_metodo, calcular_cantidad_pedir
)
from utils.inventario import (
    calcular_consumo_diario, calcular_dias_cobertura, analizar_inventario,
    calcular_costo_total_compra, validar_capacidad_compra, priorizar_productos_compra
)
from utils.logistica import (
    calcular_tiempo_entrega_region, procesar_recepcion_compra, validar_despacho_region,
    distribuir_stock_por_demanda, analizar_cobertura_regional, generar_alertas_logistica,
    sugerir_redistribucion, calcular_stock_disponible_despacho
)
from utils.disrupciones import obtener_disrupciones_activas_empresa

bp = Blueprint('estudiante', __name__, url_prefix='/estudiante')

def estudiante_required(f):
    """Decorador para verificar que el usuario sea estudiante"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol == 'admin':
            flash('Acceso denegado. Solo para estudiantes.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/dashboard')
@login_required
@estudiante_required
def dashboard():
    """
    Dashboard principal del estudiante
    Ahora redirige al dashboard general unificado
    """
    return redirect(url_for('estudiante.dashboard_general'))


@bp.route('/general')
@login_required
@estudiante_required
def dashboard_general():
    """
    Dashboard general unificado para todos los roles
    Permite acceso a los 4 módulos: Ventas, Planeación, Compras, Logística
    """
    empresa = current_user.empresa
    simulacion = Simulacion.query.first()
    
    if not simulacion:
        flash('No existe una simulación activa', 'error')
        return redirect(url_for('auth.login'))
    
    # Obtener datos generales
    productos = Producto.query.filter_by(activo=True).all()
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    
    # Ventas del día actual
    ventas_dia = Venta.query.filter_by(
        empresa_id=empresa.id,
        dia_simulacion=simulacion.dia_actual
    ).all()
    
    # Métrica del día
    from models import Metrica
    metrica_hoy = Metrica.query.filter_by(
        empresa_id=empresa.id,
        dia_simulacion=simulacion.dia_actual
    ).first()
    
    # Pronósticos activos
    pronosticos_activos = Pronostico.query.filter_by(
        empresa_id=empresa.id
    ).count()
    
    # Órdenes en tránsito
    ordenes_transito = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).count()
    
    # Requerimientos pendientes
    requerimientos_pendientes = RequerimientoCompra.query.filter_by(
        empresa_id=empresa.id,
        estado='pendiente'
    ).count()
    
    # Alertas de inventario
    alertas_inventario = sum(1 for inv in inventarios if inv.cantidad_actual <= inv.stock_seguridad)
    
    # Movimientos recientes
    movimientos_recientes = MovimientoInventario.query.filter_by(
        empresa_id=empresa.id
    ).order_by(MovimientoInventario.created_at.desc()).limit(10).all()
    
    # Órdenes próximas a llegar (próximos 3 días)
    ordenes_proximas = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).filter(
        Compra.dia_entrega <= simulacion.dia_actual + 3
    ).order_by(Compra.dia_entrega).limit(5).all()
    
    # Disrupciones activas
    disrupciones_activas = obtener_disrupciones_activas_empresa(
        simulacion, empresa.id, simulacion.dia_actual
    )
    # Filtrar solo las visibles para estudiantes
    disrupciones_activas = [d for d in disrupciones_activas if d.visible_estudiantes]
    
    return render_template('estudiante/dashboard_general.html',
                         empresa=empresa,
                         simulacion=simulacion,
                         productos=productos,
                         inventarios=inventarios,
                         ventas_dia=ventas_dia,
                         metrica_hoy=metrica_hoy,
                         pronosticos_activos=pronosticos_activos,
                         ordenes_transito=ordenes_transito,
                         requerimientos_pendientes=requerimientos_pendientes,
                         alertas_inventario=alertas_inventario,
                         movimientos_recientes=movimientos_recientes,
                         ordenes_proximas=ordenes_proximas,
                         disrupciones_activas=disrupciones_activas)


# ============== DASHBOARD VENTAS ==============
@bp.route('/ventas')
@login_required
@estudiante_required
def dashboard_ventas():
    """Dashboard específico para el rol de Ventas - Accesible para todos"""
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    
    # Obtener productos con precios actuales
    productos = Producto.query.filter_by(activo=True).all()
    
    # Ventas por región - últimos 7 días
    regiones = ['Caribe', 'Pacifica', 'Orinoquia', 'Amazonia', 'Andina']
    ventas_por_region = {}
    for region in regiones:
        ventas = Venta.query.filter_by(
            empresa_id=empresa.id,
            region=region
        ).filter(
            Venta.dia_simulacion >= max(1, simulacion.dia_actual - 7)
        ).all()
        ventas_por_region[region] = {
            'total_ingresos': sum([v.ingreso_total for v in ventas]),
            'total_unidades': sum([v.cantidad_vendida for v in ventas]),
            'ventas_perdidas': sum([v.cantidad_perdida for v in ventas])
        }
    
    # Ventas del día actual
    ventas_hoy = Venta.query.filter_by(
        empresa_id=empresa.id,
        dia_simulacion=simulacion.dia_actual
    ).all()
    
    total_ingresos_hoy = sum([v.ingreso_total for v in ventas_hoy])
    total_unidades_hoy = sum([v.cantidad_vendida for v in ventas_hoy])
    ventas_perdidas_hoy = sum([v.cantidad_perdida for v in ventas_hoy])
    
    # Calcular nivel de servicio
    total_solicitado = sum([v.cantidad_solicitada for v in ventas_hoy])
    nivel_servicio = (total_unidades_hoy / total_solicitado * 100) if total_solicitado > 0 else 100
    
    # Ventas por producto - últimos 7 días
    ventas_por_producto = {}
    for producto in productos:
        ventas = Venta.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto.id
        ).filter(
            Venta.dia_simulacion >= max(1, simulacion.dia_actual - 7)
        ).all()
        ventas_por_producto[producto.nombre] = {
            'total_unidades': sum([v.cantidad_vendida for v in ventas]),
            'total_ingresos': sum([v.ingreso_total for v in ventas]),
            'precio_promedio': sum([v.precio_unitario for v in ventas]) / len(ventas) if ventas else producto.precio_actual
        }
    
    # Historial de precios y demanda para análisis
    historial_ventas = Venta.query.filter_by(
        empresa_id=empresa.id
    ).order_by(Venta.dia_simulacion.desc()).limit(30).all()
    
    return render_template('estudiante/ventas/dashboard.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         productos=productos,
                         regiones=regiones,
                         ventas_por_region=ventas_por_region,
                         ventas_por_producto=ventas_por_producto,
                         total_ingresos_hoy=total_ingresos_hoy,
                         total_unidades_hoy=total_unidades_hoy,
                         ventas_perdidas_hoy=ventas_perdidas_hoy,
                         nivel_servicio=nivel_servicio,
                         historial_ventas=historial_ventas)


@bp.route('/ventas/ajustar-precio', methods=['POST'])
@login_required
@estudiante_required
def ajustar_precio():
    """Ajustar precio de un producto - Accesible para todos los roles"""
    # Comentado: Todos los estudiantes pueden acceder a todos los módulos para colaborar
    # if current_user.rol != 'ventas':
    #     flash('No autorizado', 'error')
    #     return redirect(url_for('estudiante.dashboard'))
    
    try:
        producto_id = int(request.form.get('producto_id'))
        nuevo_precio = float(request.form.get('nuevo_precio'))
        
        producto = Producto.query.get(producto_id)
        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('estudiante.dashboard_ventas'))
        
        # Validar que el precio no sea menor al costo
        if nuevo_precio < producto.costo_unitario:
            flash(f'El precio no puede ser menor al costo unitario (${producto.costo_unitario:,.2f})', 'error')
            return redirect(url_for('estudiante.dashboard_ventas'))
        
        # Registrar el precio anterior
        precio_anterior = producto.precio_actual
        
        # Actualizar precio
        producto.precio_actual = nuevo_precio
        
        # Registrar la decisión
        simulacion = Simulacion.query.first()
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            dia_simulacion=simulacion.dia_actual,
            tipo_decision='ajuste_precio',
            datos_decision={
                'producto_id': producto_id,
                'producto_nombre': producto.nombre,
                'precio_anterior': precio_anterior,
                'precio_nuevo': nuevo_precio,
                'variacion_porcentual': ((nuevo_precio - precio_anterior) / precio_anterior * 100) if precio_anterior > 0 else 0
            }
        )
        
        db.session.add(decision)
        db.session.commit()
        
        cambio_pct = ((nuevo_precio - precio_anterior) / precio_anterior * 100) if precio_anterior > 0 else 0
        flash(f'Precio de {producto.nombre} actualizado a ${nuevo_precio:,.2f} ({cambio_pct:+.1f}%)', 'success')
        
    except ValueError:
        flash('Datos inválidos', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al ajustar precio: {str(e)}', 'error')
    
    return redirect(url_for('estudiante.dashboard_ventas'))


@bp.route('/ventas/analisis-regional')
@login_required
@estudiante_required
def analisis_regional():
    """Vista detallada de análisis por región"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    
    # Datos por región en los últimos 14 días
    regiones = ['Caribe', 'Pacifica', 'Orinoquia', 'Amazonia', 'Andina']
    dias_analisis = 14
    
    datos_regionales = {}
    for region in regiones:
        ventas = Venta.query.filter_by(
            empresa_id=empresa.id,
            region=region
        ).filter(
            Venta.dia_simulacion >= max(1, simulacion.dia_actual - dias_analisis)
        ).all()
        
        datos_regionales[region] = {
            'ventas': ventas,
            'total_ingresos': sum([v.ingreso_total for v in ventas]),
            'total_unidades': sum([v.cantidad_vendida for v in ventas]),
            'ventas_perdidas': sum([v.cantidad_perdida for v in ventas]),
            'dias_con_ventas': len(set([v.dia_simulacion for v in ventas])),
            'ingreso_promedio_dia': sum([v.ingreso_total for v in ventas]) / dias_analisis if ventas else 0
        }
    
    return render_template('estudiante/ventas/analisis_regional.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         regiones=regiones,
                         datos_regionales=datos_regionales,
                         dias_analisis=dias_analisis)


# API Endpoints para gráficos dinámicos
@bp.route('/api/ventas/historico-region')
@login_required
@estudiante_required
def api_ventas_historico_region():
    """API: Datos históricos de ventas por región"""
    if current_user.rol != 'ventas':
        return jsonify({'error': 'No autorizado'}), 403
    
    simulacion = Simulacion.query.first()
    empresa_id = current_user.empresa_id
    dias = int(request.args.get('dias', 14))
    
    regiones = ['Caribe', 'Pacifica', 'Orinoquia', 'Amazonia', 'Andina']
    resultado = {
        'labels': list(range(max(1, simulacion.dia_actual - dias + 1), simulacion.dia_actual + 1)),
        'datasets': []
    }
    
    colores = {
        'Caribe': '#3498db',
        'Pacifica': '#2ecc71',
        'Orinoquia': '#f39c12',
        'Amazonia': '#27ae60',
        'Andina': '#9b59b6'
    }
    
    for region in regiones:
        datos_dia = []
        for dia in resultado['labels']:
            ventas = Venta.query.filter_by(
                empresa_id=empresa_id,
                region=region,
                dia_simulacion=dia
            ).all()
            total = sum([v.ingreso_total for v in ventas])
            datos_dia.append(round(total, 2))
        
        resultado['datasets'].append({
            'label': region,
            'data': datos_dia,
            'borderColor': colores[region],
            'backgroundColor': colores[region] + '33',
            'tension': 0.4
        })
    
    return jsonify(resultado)


@bp.route('/api/ventas/precio-demanda/<int:producto_id>')
@login_required
@estudiante_required
def api_precio_demanda(producto_id):
    """API: Relación precio vs demanda para un producto"""
    if current_user.rol != 'ventas':
        return jsonify({'error': 'No autorizado'}), 403
    
    empresa_id = current_user.empresa_id
    dias = int(request.args.get('dias', 14))
    simulacion = Simulacion.query.first()
    
    ventas = Venta.query.filter_by(
        empresa_id=empresa_id,
        producto_id=producto_id
    ).filter(
        Venta.dia_simulacion >= max(1, simulacion.dia_actual - dias)
    ).order_by(Venta.dia_simulacion).all()
    
    # Agrupar por día
    datos_por_dia = {}
    for venta in ventas:
        dia = venta.dia_simulacion
        if dia not in datos_por_dia:
            datos_por_dia[dia] = {
                'precio': venta.precio_unitario,
                'demanda': 0
            }
        datos_por_dia[dia]['demanda'] += venta.cantidad_solicitada
    
    resultado = {
        'labels': list(datos_por_dia.keys()),
        'precios': [datos_por_dia[dia]['precio'] for dia in datos_por_dia],
        'demanda': [datos_por_dia[dia]['demanda'] for dia in datos_por_dia]
    }
    
    return jsonify(resultado)


@bp.route('/api/ventas/por-producto')
@login_required
@estudiante_required
def api_ventas_por_producto():
    """API: Ventas totales por producto"""
    if current_user.rol != 'ventas':
        return jsonify({'error': 'No autorizado'}), 403
    
    empresa_id = current_user.empresa_id
    dias = int(request.args.get('dias', 7))
    simulacion = Simulacion.query.first()
    
    productos = Producto.query.filter_by(activo=True).all()
    
    labels = []
    valores = []
    
    for producto in productos:
        ventas = Venta.query.filter_by(
            empresa_id=empresa_id,
            producto_id=producto.id
        ).filter(
            Venta.dia_simulacion >= max(1, simulacion.dia_actual - dias)
        ).all()
        
        total_ingresos = sum([v.ingreso_total for v in ventas])
        if total_ingresos > 0:
            labels.append(producto.nombre)
            valores.append(round(total_ingresos, 2))
    
    resultado = {
        'labels': labels,
        'data': valores,
        'backgroundColor': [
            '#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6',
            '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#16a085'
        ]
    }
    
    return jsonify(resultado)


# ============== DASHBOARD PLANEACIÓN ==============
@bp.route('/planeacion')
@login_required
@estudiante_required
def dashboard_planeacion():
    """Dashboard específico para el rol de Planeación"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    
    # Obtener productos
    productos = Producto.query.filter_by(activo=True).all()
    
    # Obtener inventarios actuales
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    inventarios_dict = {inv.producto_id: inv for inv in inventarios}
    
    # Calcular estadísticas por producto
    stats_productos = []
    for producto in productos:
        # Ventas históricas del producto
        ventas = Venta.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto.id
        ).order_by(Venta.dia_simulacion).all()
        
        # Datos para análisis
        total_vendido = sum([v.cantidad_vendida for v in ventas])
        total_perdido = sum([v.cantidad_perdida for v in ventas])
        demanda_promedio = total_vendido / len(ventas) if ventas else 0
        
        inventario = inventarios_dict.get(producto.id)
        stock_actual = inventario.cantidad_actual if inventario else 0
        
        stats_productos.append({
            'producto': producto,
            'total_vendido': total_vendido,
            'total_perdido': total_perdido,
            'demanda_promedio': demanda_promedio,
            'stock_actual': stock_actual,
            'dias_ventas': len(set([v.dia_simulacion for v in ventas]))
        })
    
    # Pronósticos recientes
    pronosticos_recientes = Pronostico.query.filter_by(
        empresa_id=empresa.id,
        usuario_id=current_user.id
    ).order_by(Pronostico.created_at.desc()).limit(10).all()
    
    # Requerimientos pendientes
    requerimientos_pendientes = RequerimientoCompra.query.filter_by(
        empresa_id=empresa.id,
        usuario_planeacion_id=current_user.id,
        estado='pendiente'
    ).count()
    
    return render_template('estudiante/planeacion/dashboard.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         productos=productos,
                         stats_productos=stats_productos,
                         pronosticos_recientes=pronosticos_recientes,
                         requerimientos_pendientes=requerimientos_pendientes)


@bp.route('/planeacion/generar-pronostico')
@login_required
@estudiante_required
def generar_pronostico():
    """Vista para generar pronósticos con diferentes métodos"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    productos = Producto.query.filter_by(activo=True).all()
    
    # Producto seleccionado (si viene en query params)
    producto_id = request.args.get('producto_id', type=int)
    producto_seleccionado = None
    datos_historicos = []
    comparacion_metodos = {}
    mejor_metodo_nombre = None
    mejor_metodo_datos = {}
    
    if producto_id:
        producto_seleccionado = Producto.query.get(producto_id)
        
        if producto_seleccionado:
            # Obtener ventas históricas
            ventas = Venta.query.filter_by(
                empresa_id=empresa.id,
                producto_id=producto_id
            ).order_by(Venta.dia_simulacion).all()
            
            # Agrupar por día y sumar cantidades
            ventas_por_dia = {}
            for venta in ventas:
                dia = venta.dia_simulacion
                if dia not in ventas_por_dia:
                    ventas_por_dia[dia] = 0
                ventas_por_dia[dia] += venta.cantidad_solicitada
            
            # Crear lista ordenada
            dias_ordenados = sorted(ventas_por_dia.keys())
            datos_historicos = [ventas_por_dia[dia] for dia in dias_ordenados]
            
            # Comparar métodos si hay suficientes datos
            if len(datos_historicos) >= 3:
                comparacion_metodos = comparar_metodos(datos_historicos)
                mejor_metodo_nombre, mejor_metodo_datos = obtener_mejor_metodo(comparacion_metodos, 'mape')
    
    return render_template('estudiante/planeacion/generar_pronostico.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         productos=productos,
                         producto_seleccionado=producto_seleccionado,
                         datos_historicos=datos_historicos,
                         comparacion_metodos=comparacion_metodos,
                         mejor_metodo_nombre=mejor_metodo_nombre,
                         mejor_metodo_datos=mejor_metodo_datos)


@bp.route('/planeacion/guardar-pronostico', methods=['POST'])
@login_required
@estudiante_required
def guardar_pronostico():
    """Guardar un pronóstico generado"""
    # Acceso permitido para todos los roles - Panel unificado
    try:
        producto_id = int(request.form.get('producto_id'))
        metodo = request.form.get('metodo')
        demanda_pronosticada = float(request.form.get('demanda_pronosticada'))
        dia_pronostico = int(request.form.get('dia_pronostico'))
        
        # Parámetros del método
        parametros = {}
        if 'n' in request.form:
            parametros['n'] = int(request.form.get('n'))
        if 'alpha' in request.form:
            parametros['alpha'] = float(request.form.get('alpha'))
        if 'beta' in request.form:
            parametros['beta'] = float(request.form.get('beta'))
        
        # Errores calculados
        error_mape = float(request.form.get('error_mape', 0))
        error_mad = float(request.form.get('error_mad', 0))
        
        # Datos históricos usados (JSON)
        datos_historicos_str = request.form.get('datos_historicos', '[]')
        import json
        datos_historicos = json.loads(datos_historicos_str)
        
        simulacion = Simulacion.query.first()
        
        # Crear pronóstico
        pronostico = Pronostico(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            dia_generacion=simulacion.dia_actual,
            dia_pronostico=dia_pronostico,
            metodo_usado=metodo,
            parametros=parametros,
            demanda_pronosticada=demanda_pronosticada,
            error_mape=error_mape,
            error_mad=error_mad,
            datos_historicos=datos_historicos
        )
        
        db.session.add(pronostico)
        
        # Registrar decisión
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            dia_simulacion=simulacion.dia_actual,
            tipo_decision='pronostico_generado',
            datos_decision={
                'producto_id': producto_id,
                'metodo': metodo,
                'demanda_pronosticada': demanda_pronosticada,
                'dia_pronostico': dia_pronostico
            }
        )
        
        db.session.add(decision)
        db.session.commit()
        
        flash(f'Pronóstico guardado: {demanda_pronosticada:.0f} unidades para día {dia_pronostico}', 'success')
        return redirect(url_for('estudiante.generar_pronostico', producto_id=producto_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar pronóstico: {str(e)}', 'error')
        return redirect(url_for('estudiante.generar_pronostico'))


@bp.route('/planeacion/requerimientos')
@login_required
@estudiante_required
def requerimientos_compra():
    """Vista para crear requerimientos de compra"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    
    # Obtener productos y sus datos
    productos = Producto.query.filter_by(activo=True).all()
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    inventarios_dict = {inv.producto_id: inv for inv in inventarios}
    
    # Pronósticos más recientes por producto
    pronosticos_recientes = {}
    for producto in productos:
        pronostico = Pronostico.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto.id
        ).order_by(Pronostico.created_at.desc()).first()
        
        if pronostico:
            pronosticos_recientes[producto.id] = pronostico
    
    # Requerimientos existentes
    requerimientos = RequerimientoCompra.query.filter_by(
        empresa_id=empresa.id,
        usuario_planeacion_id=current_user.id
    ).order_by(RequerimientoCompra.created_at.desc()).limit(20).all()
    
    return render_template('estudiante/planeacion/requerimientos.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         productos=productos,
                         inventarios_dict=inventarios_dict,
                         pronosticos_recientes=pronosticos_recientes,
                         requerimientos=requerimientos)


@bp.route('/planeacion/crear-requerimiento', methods=['POST'])
@login_required
@estudiante_required
def crear_requerimiento():
    """Crear un requerimiento de compra basado en pronóstico"""
    # Acceso permitido para todos los roles - Panel unificado
    try:
        producto_id = int(request.form.get('producto_id'))
        demanda_pronosticada = float(request.form.get('demanda_pronosticada'))
        stock_actual = float(request.form.get('stock_actual'))
        stock_seguridad = float(request.form.get('stock_seguridad'))
        lead_time = int(request.form.get('lead_time'))
        dia_necesidad = int(request.form.get('dia_necesidad'))
        notas = request.form.get('notas', '')
        pronostico_id = request.form.get('pronostico_id')
        
        simulacion = Simulacion.query.first()
        
        # Calcular cantidad sugerida
        calculo = calcular_cantidad_pedir(
            demanda_pronosticada=demanda_pronosticada,
            stock_actual=stock_actual,
            stock_seguridad=stock_seguridad,
            lead_time=lead_time,
            demanda_promedio_diaria=demanda_pronosticada
        )
        
        cantidad_sugerida = calculo['cantidad_sugerida']
        
        # Crear requerimiento
        requerimiento = RequerimientoCompra(
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            usuario_planeacion_id=current_user.id,
            pronostico_id=int(pronostico_id) if pronostico_id else None,
            dia_generacion=simulacion.dia_actual,
            dia_necesidad=dia_necesidad,
            demanda_pronosticada=demanda_pronosticada,
            stock_actual=stock_actual,
            stock_seguridad=stock_seguridad,
            lead_time=lead_time,
            cantidad_sugerida=cantidad_sugerida,
            notas_planeacion=notas,
            estado='pendiente'
        )
        
        db.session.add(requerimiento)
        
        # Registrar decisión
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            dia_simulacion=simulacion.dia_actual,
            tipo_decision='requerimiento_compra',
            datos_decision={
                'producto_id': producto_id,
                'cantidad_sugerida': cantidad_sugerida,
                'demanda_pronosticada': demanda_pronosticada,
                'dia_necesidad': dia_necesidad
            }
        )
        
        db.session.add(decision)
        db.session.commit()
        
        flash(f'Requerimiento creado: {cantidad_sugerida:.0f} unidades para día {dia_necesidad}', 'success')
        return redirect(url_for('estudiante.requerimientos_compra'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear requerimiento: {str(e)}', 'error')
        return redirect(url_for('estudiante.requerimientos_compra'))


# APIs para gráficos de Planeación
@bp.route('/api/planeacion/historico-producto/<int:producto_id>')
@login_required
@estudiante_required
def api_historico_producto(producto_id):
    """API: Datos históricos de demanda de un producto"""
    if current_user.rol != 'planeacion':
        return jsonify({'error': 'No autorizado'}), 403
    
    empresa_id = current_user.empresa_id
    
    # Obtener ventas del producto
    ventas = Venta.query.filter_by(
        empresa_id=empresa_id,
        producto_id=producto_id
    ).order_by(Venta.dia_simulacion).all()
    
    # Agrupar por día
    ventas_por_dia = {}
    for venta in ventas:
        dia = venta.dia_simulacion
        if dia not in ventas_por_dia:
            ventas_por_dia[dia] = {'solicitado': 0, 'vendido': 0, 'perdido': 0}
        ventas_por_dia[dia]['solicitado'] += venta.cantidad_solicitada
        ventas_por_dia[dia]['vendido'] += venta.cantidad_vendida
        ventas_por_dia[dia]['perdido'] += venta.cantidad_perdida
    
    dias = sorted(ventas_por_dia.keys())
    
    resultado = {
        'labels': dias,
        'datasets': [{
            'label': 'Demanda (Solicitado)',
            'data': [ventas_por_dia[dia]['solicitado'] for dia in dias],
            'borderColor': '#3498db',
            'backgroundColor': 'rgba(52, 152, 219, 0.1)',
            'tension': 0.4
        }, {
            'label': 'Vendido',
            'data': [ventas_por_dia[dia]['vendido'] for dia in dias],
            'borderColor': '#2ecc71',
            'backgroundColor': 'rgba(46, 204, 113, 0.1)',
            'tension': 0.4
        }, {
            'label': 'Perdido',
            'data': [ventas_por_dia[dia]['perdido'] for dia in dias],
            'borderColor': '#e74c3c',
            'backgroundColor': 'rgba(231, 76, 60, 0.1)',
            'tension': 0.4
        }]
    }
    
    return jsonify(resultado)


# ============== DASHBOARD COMPRAS ==============
@bp.route('/compras')
@login_required
@estudiante_required
def dashboard_compras():
    """Dashboard específico para el rol de Compras"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    
    # Obtener productos
    productos = Producto.query.filter_by(activo=True).all()
    
    # Obtener inventarios
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    inventarios_dict = {inv.producto_id: inv for inv in inventarios}
    
    # Analizar cada producto
    analisis_productos = []
    for producto in productos:
        inventario = inventarios_dict.get(producto.id)
        
        if inventario:
            # Obtener ventas recientes
            ventas = Venta.query.filter_by(
                empresa_id=empresa.id,
                producto_id=producto.id
            ).order_by(Venta.dia_simulacion.desc()).limit(14).all()
            
            # Analizar inventario
            analisis = analizar_inventario(inventario, ventas)
            
            analisis_productos.append({
                'producto': producto,
                'inventario': inventario,
                **analisis
            })
    
    # Priorizar productos
    productos_priorizados = priorizar_productos_compra(analisis_productos)
    
    # Requerimientos de Planeación pendientes
    requerimientos = RequerimientoCompra.query.filter_by(
        empresa_id=empresa.id,
        estado='pendiente'
    ).order_by(RequerimientoCompra.created_at.desc()).all()
    
    # Órdenes de compra recientes
    ordenes_compra = Compra.query.filter_by(empresa_id=empresa.id)\
        .order_by(Compra.dia_orden.desc())\
        .limit(15).all()
    
    # Órdenes en tránsito
    ordenes_transito = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).all()
    
    # Capital comprometido
    capital_comprometido = sum([o.costo_total for o in ordenes_transito])
    capital_libre = empresa.capital_actual - capital_comprometido
    
    return render_template('estudiante/compras/dashboard.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         productos_priorizados=productos_priorizados,
                         requerimientos=requerimientos,
                         ordenes_compra=ordenes_compra,
                         ordenes_transito=ordenes_transito,
                         capital_comprometido=capital_comprometido,
                         capital_libre=capital_libre)


@bp.route('/compras/requerimientos')
@login_required
@estudiante_required
def ver_requerimientos():
    """Vista de requerimientos de Planeación"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    
    # Obtener todos los requerimientos
    requerimientos_pendientes = RequerimientoCompra.query.filter_by(
        empresa_id=empresa.id,
        estado='pendiente'
    ).order_by(RequerimientoCompra.dia_necesidad).all()
    
    requerimientos_procesados = RequerimientoCompra.query.filter_by(
        empresa_id=empresa.id
    ).filter(RequerimientoCompra.estado != 'pendiente')\
        .order_by(RequerimientoCompra.updated_at.desc())\
        .limit(20).all()
    
    return render_template('estudiante/compras/requerimientos.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         requerimientos_pendientes=requerimientos_pendientes,
                         requerimientos_procesados=requerimientos_procesados)


@bp.route('/compras/crear-orden-desde-requerimiento/<int:requerimiento_id>', methods=['POST'])
@login_required
@estudiante_required
def crear_orden_desde_requerimiento(requerimiento_id):
    """Crear orden de compra desde un requerimiento de Planeación"""
    # Acceso permitido para todos los roles - Panel unificado
    try:
        requerimiento = RequerimientoCompra.query.get_or_404(requerimiento_id)
        
        # Verificar que sea de la misma empresa
        if requerimiento.empresa_id != current_user.empresa_id:
            flash('No autorizado', 'error')
            return redirect(url_for('estudiante.ver_requerimientos'))
        
        # Cantidad (puede ser ajustada por Compras)
        cantidad = float(request.form.get('cantidad', requerimiento.cantidad_sugerida))
        notas_compras = request.form.get('notas_compras', '')
        
        simulacion = Simulacion.query.first()
        producto = Producto.query.get(requerimiento.producto_id)
        
        # Calcular costos
        costo_unitario = producto.costo_unitario
        costo_total = cantidad * costo_unitario
        
        # Validar capital
        empresa = current_user.empresa
        ordenes_pendientes = Compra.query.filter_by(
            empresa_id=empresa.id,
            estado='en_transito'
        ).all()
        
        validacion = validar_capacidad_compra(
            empresa.capital_actual,
            costo_total,
            ordenes_pendientes
        )
        
        if not validacion['puede_comprar']:
            flash(f"Capital insuficiente. {validacion['sugerencia']}", 'error')
            return redirect(url_for('estudiante.ver_requerimientos'))
        
        # Crear orden de compra
        dia_entrega = simulacion.dia_actual + producto.tiempo_entrega
        
        compra = Compra(
            empresa_id=current_user.empresa_id,
            producto_id=requerimiento.producto_id,
            dia_orden=simulacion.dia_actual,
            dia_entrega=dia_entrega,
            cantidad=cantidad,
            costo_unitario=costo_unitario,
            costo_total=costo_total,
            estado='en_transito'
        )
        
        db.session.add(compra)
        db.session.flush()  # Para obtener el ID
        
        # Actualizar requerimiento
        requerimiento.estado = 'convertido_orden'
        requerimiento.notas_compras = notas_compras
        requerimiento.orden_compra_id = compra.id
        
        # Actualizar capital
        empresa.capital_actual -= costo_total
        
        # Registrar decisión
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            dia_simulacion=simulacion.dia_actual,
            tipo_decision='orden_compra_requerimiento',
            datos_decision={
                'requerimiento_id': requerimiento_id,
                'producto_id': requerimiento.producto_id,
                'cantidad_sugerida': requerimiento.cantidad_sugerida,
                'cantidad_ordenada': cantidad,
                'costo_total': costo_total
            }
        )
        
        db.session.add(decision)
        db.session.commit()
        
        flash(f'Orden creada: {cantidad:.0f} unidades de {producto.nombre}. Llegará día {dia_entrega}', 'success')
        return redirect(url_for('estudiante.ver_requerimientos'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear orden: {str(e)}', 'error')
        return redirect(url_for('estudiante.ver_requerimientos'))


@bp.route('/compras/crear-orden-manual', methods=['POST'])
@login_required
@estudiante_required
def crear_orden_manual():
    """Crear orden de compra manual (sin requerimiento)"""
    # Acceso permitido para todos los roles - Panel unificado
    try:
        producto_id = int(request.form.get('producto_id'))
        cantidad = float(request.form.get('cantidad'))
        
        simulacion = Simulacion.query.first()
        producto = Producto.query.get(producto_id)
        
        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('estudiante.dashboard_compras'))
        
        # Calcular costos
        costo_unitario = producto.costo_unitario
        costo_total = cantidad * costo_unitario
        
        # Validar capital
        empresa = current_user.empresa
        ordenes_pendientes = Compra.query.filter_by(
            empresa_id=empresa.id,
            estado='en_transito'
        ).all()
        
        validacion = validar_capacidad_compra(
            empresa.capital_actual,
            costo_total,
            ordenes_pendientes
        )
        
        if not validacion['puede_comprar']:
            flash(f"Capital insuficiente. {validacion['sugerencia']}", 'error')
            return redirect(url_for('estudiante.dashboard_compras'))
        
        # Crear orden
        dia_entrega = simulacion.dia_actual + producto.tiempo_entrega
        
        compra = Compra(
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            dia_orden=simulacion.dia_actual,
            dia_entrega=dia_entrega,
            cantidad=cantidad,
            costo_unitario=costo_unitario,
            costo_total=costo_total,
            estado='en_transito'
        )
        
        # Actualizar capital
        empresa.capital_actual -= costo_total
        
        # Registrar decisión
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            dia_simulacion=simulacion.dia_actual,
            tipo_decision='orden_compra_manual',
            datos_decision={
                'producto_id': producto_id,
                'cantidad': cantidad,
                'costo_total': costo_total
            }
        )
        
        db.session.add(compra)
        db.session.add(decision)
        db.session.commit()
        
        flash(f'Orden creada: {cantidad:.0f} unidades. Llegará día {dia_entrega}', 'success')
        return redirect(url_for('estudiante.dashboard_compras'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear orden: {str(e)}', 'error')
        return redirect(url_for('estudiante.dashboard_compras'))


@bp.route('/compras/marcar-requerimiento-revisado/<int:requerimiento_id>', methods=['POST'])
@login_required
@estudiante_required
def marcar_requerimiento_revisado(requerimiento_id):
    """Marcar requerimiento como revisado sin crear orden"""
    # Acceso permitido para todos los roles - Panel unificado
    requerimiento = RequerimientoCompra.query.get_or_404(requerimiento_id)
    
    if requerimiento.empresa_id != current_user.empresa_id:
        flash('No autorizado', 'error')
        return redirect(url_for('estudiante.ver_requerimientos'))
    
    notas = request.form.get('notas_compras', '')
    
    requerimiento.estado = 'revisado'
    requerimiento.notas_compras = notas
    
    db.session.commit()
    
    flash('Requerimiento marcado como revisado', 'info')
    return redirect(url_for('estudiante.ver_requerimientos'))


# APIs para Compras
@bp.route('/api/compras/inventario-status')
@login_required
@estudiante_required
def api_inventario_status():
    """API: Estado del inventario para gráficos"""
    if current_user.rol != 'compras':
        return jsonify({'error': 'No autorizado'}), 403
    
    empresa_id = current_user.empresa_id
    
    # Obtener inventarios
    inventarios = Inventario.query.filter_by(empresa_id=empresa_id).all()
    
    productos = []
    stock_actual = []
    punto_reorden = []
    stock_seguridad = []
    
    for inv in inventarios:
        productos.append(inv.producto.nombre)
        stock_actual.append(inv.cantidad_actual)
        punto_reorden.append(inv.punto_reorden)
        stock_seguridad.append(inv.stock_seguridad)
    
    resultado = {
        'labels': productos,
        'datasets': [{
            'label': 'Stock Actual',
            'data': stock_actual,
            'backgroundColor': '#3498db'
        }, {
            'label': 'Punto de Reorden',
            'data': punto_reorden,
            'backgroundColor': '#f39c12'
        }, {
            'label': 'Stock de Seguridad',
            'data': stock_seguridad,
            'backgroundColor': '#2ecc71'
        }]
    }
    
    return jsonify(resultado)


# ============== DASHBOARD LOGÍSTICA ==============
# ============== DASHBOARD LOGÍSTICA ==============
@bp.route('/logistica')
@login_required
@estudiante_required
def dashboard_logistica():
    """Dashboard específico para el rol de Logística"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    
    # Obtener inventarios
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    productos = Producto.query.filter_by(activo=True).all()
    
    # Órdenes de compra en tránsito (pendientes de recibir)
    ordenes_transito = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).order_by(Compra.dia_entrega).all()
    
    # Órdenes que llegan hoy
    ordenes_hoy = [o for o in ordenes_transito if o.dia_entrega == simulacion.dia_actual]
    
    # Despachos regionales pendientes y en tránsito
    despachos_pendientes = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        estado='pendiente'
    ).count()
    
    despachos_transito = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).count()
    
    # Análisis de inventario por región
    regiones = ['Andina', 'Caribe', 'Pacífica', 'Orinoquía', 'Amazonía']
    stock_por_region = {}
    
    for region in regiones:
        # Obtener ventas de esta región
        ventas_region = Venta.query.filter_by(
            empresa_id=empresa.id,
            region=region
        ).all()
        
        # Calcular stock necesario (simplificado - en producción habría tabla de stock regional)
        total_vendido = sum(v.cantidad_vendida for v in ventas_region[-14:])  # Últimos 14 días
        
        stock_por_region[region] = {
            'ventas_recientes': total_vendido,
            'tiempo_entrega': calcular_tiempo_entrega_region(region)
        }
    
    # Generar alertas para cada producto
    alertas_generales = []
    for inv in inventarios:
        ventas_producto = Venta.query.filter_by(
            empresa_id=empresa.id,
            producto_id=inv.producto_id
        ).order_by(Venta.dia_simulacion.desc()).limit(14).all()
        
        alertas = generar_alertas_logistica(inv, ventas_producto, ordenes_transito)
        if alertas:
            alertas_generales.extend([{**a, 'producto': inv.producto.nombre} for a in alertas])
    
    # Movimientos recientes de inventario
    movimientos_recientes = MovimientoInventario.query.filter_by(
        empresa_id=empresa.id
    ).order_by(MovimientoInventario.created_at.desc()).limit(10).all()
    
    return render_template('estudiante/logistica/dashboard.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         inventarios=inventarios,
                         ordenes_transito=ordenes_transito,
                         ordenes_hoy=ordenes_hoy,
                         despachos_pendientes=despachos_pendientes,
                         despachos_transito=despachos_transito,
                         stock_por_region=stock_por_region,
                         alertas=alertas_generales,
                         movimientos_recientes=movimientos_recientes,
                         productos=productos)


@bp.route('/logistica/recepcion')
@login_required
@estudiante_required
def vista_recepcion():
    """Vista de recepción de órdenes de compra"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    
    # Órdenes en tránsito
    ordenes_transito = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).order_by(Compra.dia_entrega).all()
    
    # Órdenes recibidas (entregadas)
    ordenes_recibidas = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='entregado'
    ).order_by(Compra.dia_entrega.desc()).limit(20).all()
    
    return render_template('estudiante/logistica/recepcion.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         ordenes_transito=ordenes_transito,
                         ordenes_recibidas=ordenes_recibidas)


@bp.route('/logistica/recibir-orden/<int:compra_id>', methods=['POST'])
@login_required
@estudiante_required
def recibir_orden_compra(compra_id):
    """Procesar recepción de una orden de compra"""
    # Acceso permitido para todos los roles - Panel unificado
    try:
        compra = Compra.query.get_or_404(compra_id)
        
        if compra.empresa_id != current_user.empresa_id:
            flash('No autorizado', 'error')
            return redirect(url_for('estudiante.vista_recepcion'))
        
        if compra.estado != 'en_transito':
            flash('Esta orden ya fue recibida o no está en tránsito', 'warning')
            return redirect(url_for('estudiante.vista_recepcion'))
        
        simulacion = Simulacion.query.first()
        
        # Verificar que sea el día de entrega o posterior
        if simulacion.dia_actual < compra.dia_entrega:
            flash(f'Esta orden llega el día {compra.dia_entrega}. Aún no puede ser recibida.', 'warning')
            return redirect(url_for('estudiante.vista_recepcion'))
        
        # Obtener o crear inventario
        inventario = Inventario.query.filter_by(
            empresa_id=current_user.empresa_id,
            producto_id=compra.producto_id
        ).first()
        
        if not inventario:
            # Crear inventario si no existe
            inventario = Inventario(
                empresa_id=current_user.empresa_id,
                producto_id=compra.producto_id,
                cantidad_actual=0,
                costo_promedio=compra.costo_unitario
            )
            db.session.add(inventario)
        
        # Procesar recepción
        resultado = procesar_recepcion_compra(compra, inventario)
        
        # Actualizar estado de la compra
        compra.estado = 'entregado'
        
        # Registrar movimiento de inventario
        movimiento = MovimientoInventario(
            empresa_id=current_user.empresa_id,
            producto_id=compra.producto_id,
            usuario_id=current_user.id,
            dia_simulacion=simulacion.dia_actual,
            tipo_movimiento='entrada_compra',
            cantidad=compra.cantidad,
            saldo_anterior=resultado['cantidad_anterior'],
            saldo_nuevo=resultado['cantidad_nueva'],
            compra_id=compra.id,
            observaciones=f"Recepción de compra. Costo unitario: ${compra.costo_unitario:,.0f}"
        )
        
        db.session.add(movimiento)
        
        # Registrar decisión
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            dia_simulacion=simulacion.dia_actual,
            tipo_decision='recepcion_compra',
            datos_decision={
                'compra_id': compra.id,
                'producto_id': compra.producto_id,
                'cantidad': compra.cantidad
            },
            resultado=resultado
        )
        
        db.session.add(decision)
        db.session.commit()
        
        flash(f'Orden recibida: {compra.cantidad:.0f} unidades de {compra.producto.nombre}. '
              f'Nuevo stock: {resultado["cantidad_nueva"]:.0f}', 'success')
        
        return redirect(url_for('estudiante.vista_recepcion'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al recibir orden: {str(e)}', 'error')
        return redirect(url_for('estudiante.vista_recepcion'))


@bp.route('/logistica/despacho')
@login_required
@estudiante_required
def vista_despacho():
    """Vista de despacho a regiones"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    
    # Inventarios disponibles
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    
    # Calcular stock disponible para cada producto
    stock_disponible = {}
    for inv in inventarios:
        disponible = calcular_stock_disponible_despacho(inv)
        stock_disponible[inv.producto_id] = disponible
    
    # Ventas recientes (últimos 5 días) para análisis de demanda
    ventas_recientes = Venta.query.filter_by(
        empresa_id=empresa.id
    ).filter(Venta.dia_simulacion > simulacion.dia_actual - 6)\
        .order_by(Venta.dia_simulacion.desc()).all()
    
    # Análisis de demanda por región
    regiones = ['Andina', 'Caribe', 'Pacífica', 'Orinoquía', 'Amazonía']
    analisis_regiones = {}
    
    for region in regiones:
        # Ventas recientes de esta región
        ventas_region = Venta.query.filter_by(
            empresa_id=empresa.id,
            region=region
        ).order_by(Venta.dia_simulacion.desc()).limit(14).all()
        
        # Calcular demanda por producto
        demanda_productos = {}
        for inv in inventarios:
            ventas_producto = [v for v in ventas_region if v.producto_id == inv.producto_id]
            total = sum(v.cantidad_vendida for v in ventas_producto)
            dias = len(set(v.dia_simulacion for v in ventas_producto)) or 1
            demanda_productos[inv.producto_id] = total / dias
        
        analisis_regiones[region] = {
            'demanda_productos': demanda_productos,
            'tiempo_entrega': calcular_tiempo_entrega_region(region)
        }
    
    # Despachos pendientes y en tránsito
    despachos_activos = DespachoRegional.query.filter_by(
        empresa_id=empresa.id
    ).filter(DespachoRegional.estado.in_(['pendiente', 'en_transito']))\
        .order_by(DespachoRegional.created_at.desc()).all()
    
    # Despachos entregados recientes
    despachos_entregados = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        estado='entregado'
    ).order_by(DespachoRegional.dia_entrega_real.desc()).limit(15).all()
    
    # Productos para el selector
    productos = Producto.query.all()
    
    return render_template('estudiante/logistica/despacho.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         inventarios=inventarios,
                         stock_disponible=stock_disponible,
                         ventas_recientes=ventas_recientes,
                         regiones=regiones,
                         analisis_regiones=analisis_regiones,
                         despachos_activos=despachos_activos,
                         despachos_historial=despachos_entregados,
                         productos=productos)


@bp.route('/logistica/crear-despacho', methods=['POST'])
@login_required
@estudiante_required
def crear_despacho_regional():
    """Crear un despacho a una región"""
    # Acceso permitido para todos los roles - Panel unificado
    try:
        producto_id = int(request.form.get('producto_id'))
        region = request.form.get('region')
        cantidad = float(request.form.get('cantidad'))
        
        simulacion = Simulacion.query.first()
        
        # Obtener inventario
        inventario = Inventario.query.filter_by(
            empresa_id=current_user.empresa_id,
            producto_id=producto_id
        ).first()
        
        if not inventario:
            flash('Inventario no encontrado', 'error')
            return redirect(url_for('estudiante.vista_despacho'))
        
        # Validar despacho
        validacion = validar_despacho_region(inventario, cantidad)
        
        if not validacion['puede_despachar']:
            flash(validacion['recomendacion'], 'error')
            return redirect(url_for('estudiante.vista_despacho'))
        
        # Calcular tiempo de entrega
        tiempo_entrega = calcular_tiempo_entrega_region(region)
        dia_entrega = simulacion.dia_actual + tiempo_entrega
        
        # Crear despacho
        despacho = DespachoRegional(
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            usuario_logistica_id=current_user.id,
            region=region,
            dia_despacho=simulacion.dia_actual,
            dia_entrega_estimado=dia_entrega,
            cantidad=cantidad,
            estado='en_transito'
        )
        
        # Actualizar inventario (reservar)
        inventario.cantidad_reservada += cantidad
        inventario.cantidad_actual -= cantidad
        
        # Registrar movimiento
        movimiento = MovimientoInventario(
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            usuario_id=current_user.id,
            dia_simulacion=simulacion.dia_actual,
            tipo_movimiento='salida_despacho',
            cantidad=cantidad,
            saldo_anterior=inventario.cantidad_actual + cantidad,
            saldo_nuevo=inventario.cantidad_actual,
            observaciones=f"Despacho a región {region}"
        )
        
        db.session.add(despacho)
        db.session.add(movimiento)
        db.session.flush()
        
        # Vincular movimiento con despacho
        movimiento.despacho_id = despacho.id
        
        # Registrar decisión
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            dia_simulacion=simulacion.dia_actual,
            tipo_decision='despacho_regional',
            datos_decision={
                'producto_id': producto_id,
                'region': region,
                'cantidad': cantidad,
                'dia_entrega': dia_entrega
            }
        )
        
        db.session.add(decision)
        db.session.commit()
        
        if validacion.get('alerta_stock_bajo'):
            flash(f'Despacho creado. {validacion["recomendacion"]}', 'warning')
        else:
            flash(f'Despacho creado: {cantidad:.0f} unidades a {region}. Llegada estimada: día {dia_entrega}', 'success')
        
        return redirect(url_for('estudiante.vista_despacho'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear despacho: {str(e)}', 'error')
        return redirect(url_for('estudiante.vista_despacho'))


@bp.route('/logistica/movimientos')
@login_required
@estudiante_required
def vista_movimientos():
    """Vista de movimientos de inventario"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.first()
    empresa = current_user.empresa
    
    # Obtener movimientos
    tipo_filtro = request.args.get('tipo_movimiento', '')
    producto_filtro = request.args.get('producto_id', '')
    
    query = MovimientoInventario.query.filter_by(empresa_id=empresa.id)
    
    if tipo_filtro and tipo_filtro != '':
        query = query.filter_by(tipo_movimiento=tipo_filtro)
    
    if producto_filtro and producto_filtro != '':
        query = query.filter_by(producto_id=int(producto_filtro))
    
    movimientos = query.order_by(MovimientoInventario.created_at.desc()).limit(100).all()
    
    # Productos para filtro
    productos = Producto.query.filter_by(activo=True).all()
    
    # Estadísticas
    total_entradas = db.session.query(db.func.sum(MovimientoInventario.cantidad)).filter_by(
        empresa_id=empresa.id,
        tipo_movimiento='entrada_compra'
    ).scalar() or 0
    
    total_salidas_venta = db.session.query(db.func.sum(MovimientoInventario.cantidad)).filter_by(
        empresa_id=empresa.id,
        tipo_movimiento='salida_venta'
    ).scalar() or 0
    
    total_salidas_despacho = db.session.query(db.func.sum(MovimientoInventario.cantidad)).filter_by(
        empresa_id=empresa.id,
        tipo_movimiento='salida_despacho'
    ).scalar() or 0
    
    # Crear diccionario de estadísticas
    estadisticas = {
        'total_entradas': total_entradas,
        'total_salidas_venta': total_salidas_venta,
        'total_salidas_despacho': total_salidas_despacho
    }
    
    return render_template('estudiante/logistica/movimientos.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         movimientos=movimientos,
                         productos=productos,
                         estadisticas=estadisticas,
                         tipo_filtro=tipo_filtro,
                         producto_filtro=producto_filtro)


@bp.route('/logistica/actualizar-inventario', methods=['POST'])
@login_required
@estudiante_required
def actualizar_parametros_inventario():
    """Actualizar parámetros de control de inventario"""
    # Acceso permitido para todos los roles - Panel unificado
    inventario_id = int(request.form.get('inventario_id'))
    punto_reorden = float(request.form.get('punto_reorden'))
    stock_seguridad = float(request.form.get('stock_seguridad'))
    
    inventario = Inventario.query.get(inventario_id)
    
    if not inventario or inventario.empresa_id != current_user.empresa_id:
        flash('Inventario no encontrado', 'error')
        return redirect(url_for('estudiante.dashboard_logistica'))
    
    inventario.punto_reorden = punto_reorden
    inventario.stock_seguridad = stock_seguridad
    
    # Registrar decisión
    simulacion = Simulacion.query.first()
    decision = Decision(
        usuario_id=current_user.id,
        empresa_id=current_user.empresa_id,
        dia_simulacion=simulacion.dia_actual,
        tipo_decision='parametros_inventario',
        datos_decision={
            'inventario_id': inventario_id,
            'punto_reorden': punto_reorden,
            'stock_seguridad': stock_seguridad
        }
    )
    
    db.session.add(decision)
    db.session.commit()
    
    flash('Parámetros de inventario actualizados', 'success')
    return redirect(url_for('estudiante.dashboard_logistica'))



# ============== API ENDPOINTS ==============
@bp.route('/api/inventario/<int:empresa_id>')
@login_required
@estudiante_required
def api_inventario(empresa_id):
    """API para obtener datos de inventario"""
    if current_user.empresa_id != empresa_id:
        return jsonify({'error': 'No autorizado'}), 403
    
    inventarios = Inventario.query.filter_by(empresa_id=empresa_id).all()
    
    datos = []
    for inv in inventarios:
        datos.append({
            'producto': inv.producto.nombre,
            'cantidad_actual': inv.cantidad_actual,
            'punto_reorden': inv.punto_reorden,
            'stock_seguridad': inv.stock_seguridad
        })
    
    return jsonify(datos)
