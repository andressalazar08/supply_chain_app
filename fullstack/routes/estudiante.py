"""
Rutas para el rol Estudiante
Dashboard diferenciado seg�n rol: Ventas, Planeaci�n, Compras, Log�stica
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import (Usuario, Empresa, Simulacion, Inventario, Venta, Compra, Decision,
                    Producto, Pronostico, RequerimientoCompra, MovimientoInventario, DespachoRegional,
                    DisrupcionEmpresa)
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
bp = Blueprint('estudiante', __name__, url_prefix='/estudiante')

def obtener_simulacion_activa():
    """Helper para obtener la simulaci�n actualmente activa"""
    return Simulacion.query.filter_by(activa=True).first()

def estudiante_required(f):
    """Decorador para verificar que el usuario sea estudiante"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol == 'admin':
            flash('Acceso denegado. Solo para estudiantes.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@bp.route('/home')
@login_required
def home():
    """P�gina de inicio del estudiante mostrando su empresa asignada"""
    empresas_acceso = []
    
    # Solo mostrar la empresa asignada al estudiante
    if current_user.empresa_id and current_user.rol:
        empresa = current_user.empresa
        if empresa and empresa.activa:
            empresas_acceso.append({
                'empresa': empresa,
                'rol': current_user.rol
            })
    
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    return render_template('estudiante/home.html',
                         empresas_acceso=empresas_acceso,
                         simulacion=simulacion)


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
    Permite acceso a los 4 m�dulos: Ventas, Planeaci�n, Compras, Log�stica
    """
    empresa = current_user.empresa
    
    # Verificar que el estudiante tenga empresa asignada
    if not empresa or not current_user.rol:
        flash('?? No tienes una empresa asignada. Contacta con tu profesor.', 'warning')
        return redirect(url_for('estudiante.home'))
    
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    if not simulacion:
        flash('No existe una simulaci�n activa', 'error')
        return redirect(url_for('auth.login'))
    
    # Obtener datos generales
    productos = Producto.query.filter_by(activo=True).all()
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    
    # Ventas del d�a actual
    ventas_dia = Venta.query.filter_by(
        empresa_id=empresa.id,
        semana_simulacion=simulacion.semana_actual
    ).all()
    
    # M�trica del d�a
    from models import Metrica
    metrica_hoy = Metrica.query.filter_by(
        empresa_id=empresa.id,
        semana_simulacion=simulacion.semana_actual
    ).first()
    
    # Pron�sticos activos
    pronosticos_activos = Pronostico.query.filter_by(
        empresa_id=empresa.id
    ).count()
    
    # �rdenes en tr�nsito
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
    
    # �rdenes pr�ximas a llegar (pr�ximos 3 d�as)
    ordenes_proximas = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).filter(
        Compra.semana_entrega <= simulacion.semana_actual + 3
    ).order_by(Compra.semana_entrega).limit(5).all()

    # --- DISRUPCIONES ---
    # Garantizar que esta empresa tenga sus disrupciones creadas aunque se haya
    # incorporado a la simulacion despues del avance de semana que las genera.
    from utils.procesamiento_dias import verificar_y_activar_disrupciones
    nuevas_disrupciones = verificar_y_activar_disrupciones(simulacion)
    if nuevas_disrupciones:
        db.session.commit()

    # Disrupci�n activa sin respuesta (muestra el modal)
    disrupcion_pendiente = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.empresa_id == empresa.id,
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.opcion_elegida == None
    ).first()

    # Disrupciones reci�n expiradas cuya notificaci�n de cierre a�n no se vio
    disrupciones_finalizadas = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.empresa_id == empresa.id,
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.activa == False,
        DisrupcionEmpresa.notificacion_fin_vista == False
    ).all()

    # Disrupciones activas con decisi�n ya tomada (para info en dashboard)
    disrupciones_activas = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.empresa_id == empresa.id,
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.opcion_elegida != None
    ).all()

    # Cargar definiciones del cat�logo para el template
    from utils.catalogo_disrupciones import CATALOGO_DISRUPCIONES, get_disrupcion

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
                         disrupcion_pendiente=disrupcion_pendiente,
                         disrupciones_finalizadas=disrupciones_finalizadas,
                         disrupciones_activas=disrupciones_activas,
                         get_disrupcion=get_disrupcion)


@bp.route('/api/disrupcion/responder', methods=['POST'])
@login_required
@estudiante_required
def responder_disrupcion():
    """Registra la opci�n elegida por el equipo ante una disrupci�n."""
    empresa = current_user.empresa
    simulacion = Simulacion.query.filter_by(activa=True).first()

    disrupcion_id = request.form.get('disrupcion_id', type=int)
    opcion = request.form.get('opcion', '').upper()

    dis = DisrupcionEmpresa.query.get_or_404(disrupcion_id)

    # Validaciones de seguridad
    if dis.empresa_id != empresa.id:
        flash('No autorizado.', 'error')
        return redirect(url_for('estudiante.dashboard_general'))

    if dis.opcion_elegida:
        flash('Ya se registr� una decisi�n para esta disrupci�n.', 'warning')
        return redirect(url_for('estudiante.dashboard_general'))

    from utils.catalogo_disrupciones import get_disrupcion
    definicion = get_disrupcion(dis.disrupcion_key)
    if not definicion or opcion not in definicion['opciones']:
        flash('Opci�n inv�lida.', 'error')
        return redirect(url_for('estudiante.dashboard_general'))

    # Registrar decisi�n
    dis.opcion_elegida = opcion
    dis.usuario_decision_id = current_user.id
    dis.fecha_decision = datetime.utcnow()

    # Efecto inmediato disrupcion 2 Opcion A: auto-generar orden de compra adicional
    if (opcion == 'A' and dis.disrupcion_key == 'aumento_demanda'
            and dis.producto_afectado_id and not dis.efecto_inicial_aplicado):
        from utils.catalogo_disrupciones import get_disrupcion as _gd2
        cat2 = _gd2(dis.disrupcion_key)
        duracion = cat2['duracion_semanas'] if cat2 else 2
        producto_afectado = dis.producto_afectado
        compras_auto_factor = definicion['opciones']['A']['efectos'].get('compras_auto_factor', 0.40)
        cantidad_auto = round(producto_afectado.demanda_promedio * duracion * compras_auto_factor)
        orden_auto = Compra(
            empresa_id=empresa.id,
            producto_id=dis.producto_afectado_id,
            semana_orden=simulacion.semana_actual,
            semana_entrega=simulacion.semana_actual + 1,
            cantidad=cantidad_auto,
            costo_unitario=producto_afectado.costo_unitario,
            costo_total=cantidad_auto * producto_afectado.costo_unitario,
            estado='en_transito',
        )
        db.session.add(orden_auto)
        dis.efecto_inicial_aplicado = True
        msg_extra = (f' Se emiti\u00f3 autom\u00e1ticamente una orden de compra de {cantidad_auto} unidades '
                     f'de {producto_afectado.nombre} (entrega semana {simulacion.semana_actual + 1}).')

    # Efecto inmediato de Opci\xf3n C (disrupcion 1): extender compras pendientes
    elif (opcion == 'C' and dis.disrupcion_key == 'retraso_proveedor'
          and dis.producto_afectado_id and not dis.efecto_inicial_aplicado):
        delay = definicion['opciones']['C']['efectos'].get('delay_compras_pendientes', 2)
        compras_pendientes = Compra.query.filter(
            Compra.empresa_id == empresa.id,
            Compra.producto_id == dis.producto_afectado_id,
            Compra.estado.in_(['pendiente', 'en_transito'])
        ).all()
        for c in compras_pendientes:
            c.semana_entrega += delay
        dis.efecto_inicial_aplicado = True
        msg_extra = f' Las {len(compras_pendientes)} \xf3rdenes pendientes de {dis.producto_afectado.nombre} se retrasaron {delay} semanas.'

    # Efecto inmediato Opcion D (disrupcion 2): actualizar precio real del producto
    elif (opcion == 'D' and dis.disrupcion_key == 'aumento_demanda'
          and dis.producto_afectado_id and not dis.efecto_inicial_aplicado):
        from models import Producto
        producto_afectado = dis.producto_afectado
        precio_original = float(producto_afectado.precio_actual)
        mult_precio = definicion['opciones']['D']['efectos'].get('precio_multiplicador', 1.15)
        nuevo_precio = round(precio_original * mult_precio)
        producto_afectado.precio_actual = nuevo_precio
        dis.datos_extra = {'precio_original': precio_original}
        dis.efecto_inicial_aplicado = True
        msg_extra = (f' El precio de {producto_afectado.nombre} se ajust\u00f3 a '
                     f'${nuevo_precio:,.0f} (era ${precio_original:,.0f}). '
                     'Volver\u00e1 al precio original al finalizar la disrupci\u00f3n.')

    else:
        msg_extra = ''

    # Registrar en tabla de decisiones
    decision = Decision(
        usuario_id=current_user.id,
        empresa_id=empresa.id,
        semana_simulacion=simulacion.semana_actual,
        tipo_decision='disrupcion_respuesta',
        datos_decision={
            'disrupcion_key': dis.disrupcion_key,
            'opcion_elegida': opcion,
            'producto_afectado_id': dis.producto_afectado_id,
        }
    )
    db.session.add(decision)
    db.session.commit()

    flash(f'? Decisi�n registrada: Opci�n {opcion} � {definicion["opciones"][opcion]["titulo"]}.{msg_extra}', 'success')
    return redirect(url_for('estudiante.dashboard_general'))


@bp.route('/api/disrupcion/marcar-fin-visto', methods=['POST'])
@login_required
@estudiante_required
def marcar_disrupcion_fin_vista():
    """Marca como vista la notificaci�n de cierre de una disrupci�n."""
    dis_ids = request.form.getlist('disrupcion_ids[]', type=int)
    empresa = current_user.empresa
    for did in dis_ids:
        dis = DisrupcionEmpresa.query.get(did)
        if dis and dis.empresa_id == empresa.id:
            dis.notificacion_fin_vista = True
    db.session.commit()
    return jsonify({'ok': True})


# ============== DASHBOARD VENTAS ==============
@bp.route('/ventas')
@login_required
@estudiante_required
def dashboard_ventas():
    simulacion = Simulacion.query.filter_by(activa=True).first()
    empresa = current_user.empresa
    
    return render_template('estudiante/ventas/dashboard.html',
                         simulacion=simulacion,
                         empresa=empresa)


@bp.route('/api/ventas/dashboard')
@login_required
@estudiante_required
def api_ventas_dashboard():
    """API para m�tricas del dashboard"""
    try:
        empresa = current_user.empresa
        simulacion = Simulacion.query.filter_by(activa=True).first()
        
        # Ventas del d�a actual
        ventas_hoy = Venta.query.filter_by(
            empresa_id=empresa.id,
            semana_simulacion=simulacion.semana_actual
        ).all()
        
        total_unidades = sum([v.cantidad_vendida for v in ventas_hoy])
        total_ingresos = sum([v.ingreso_total for v in ventas_hoy])
        total_perdidas = sum([v.cantidad_perdida for v in ventas_hoy])
        
        # Calcular margen promedio
        margenes = [v.margen for v in ventas_hoy if v.margen > 0]
        margen_promedio = int(sum(margenes) / len(margenes)) if margenes else 0
        
        # Top productos (�ltimos 7 d�as)
        from sqlalchemy import func
        top_productos = db.session.query(
            Producto.nombre,
            func.sum(Venta.cantidad_vendida).label('cantidad')
        ).join(Venta).filter(
            Venta.empresa_id == empresa.id,
            Venta.semana_simulacion >= max(1, simulacion.semana_actual - 7)
        ).group_by(Producto.nombre).order_by(func.sum(Venta.cantidad_vendida).desc()).limit(5).all()
        
        # Ventas por regi�n (�ltimos 7 d�as)
        ventas_region = db.session.query(
            Venta.region,
            func.sum(Venta.cantidad_vendida).label('cantidad'),
            func.sum(Venta.ingreso_total).label('ingresos')
        ).filter(
            Venta.empresa_id == empresa.id,
            Venta.semana_simulacion >= max(1, simulacion.semana_actual - 7)
        ).group_by(Venta.region).all()
        
        return jsonify({
            'success': True,
            'metricas': {
                'ventas_hoy': int(total_unidades),
                'ingresos_hoy': int(total_ingresos),
                'margen_promedio': margen_promedio,
                'ventas_perdidas': int(total_perdidas)
            },
            'top_productos': [{'nombre': p[0], 'cantidad': int(p[1])} for p in top_productos],
            'ventas_region': [{'nombre': v[0], 'cantidad': int(v[1]), 'ingresos': int(v[2])} for v in ventas_region]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/ventas/matriz-precios')
@login_required
@estudiante_required
def api_ventas_matriz_precios():
    """API para obtener matriz de precios actual"""
    try:
        empresa = current_user.empresa
        productos = Producto.query.filter_by(activo=True).all()
        
        regiones = ['Andina', 'Caribe', 'Pac�fica', 'Orinoqu�a', 'Amazon�a']
        
        productos_data = []
        for producto in productos:
            precios = {}
            
            # Obtener precios actuales por regi�n (�ltimas ventas)
            for region in regiones:
                ultima_venta = Venta.query.filter_by(
                    empresa_id=empresa.id,
                    producto_id=producto.id,
                    region=region
                ).order_by(Venta.semana_simulacion.desc()).first()
                
                precios[region] = ultima_venta.precio_unitario if ultima_venta else producto.precio_actual
            
            productos_data.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'costo': producto.costo_unitario,
                'precios': precios
            })
        
        return jsonify({
            'success': True,
            'productos': productos_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/ventas/actualizar-precios', methods=['POST'])
@login_required
@estudiante_required
def api_ventas_actualizar_precios():
    """API para actualizar m�ltiples precios"""
    try:
        data = request.get_json()
        cambios = data.get('cambios', [])
        
        if not cambios:
            return jsonify({'success': False, 'message': 'No hay cambios para aplicar'}), 400
        
        empresa = current_user.empresa
        simulacion = Simulacion.query.filter_by(activa=True).first()
        
        actualizados = 0
        
        # Registrar cada cambio de precio como decisi�n
        for cambio in cambios:
            producto_id = cambio['producto_id']
            region = cambio['region']
            precio = cambio['precio']
            
            producto = Producto.query.get(producto_id)
            
            # Registrar decisi�n de cambio de precio
            decision = Decision(
                usuario_id=current_user.id,
                empresa_id=empresa.id,
                tipo_decision='ajuste_precio',
                semana_simulacion=simulacion.semana_actual,
                datos_decision={
                    'producto_id': producto_id,
                    'producto_nombre': producto.nombre,
                    'region': region,
                    'precio_nuevo': precio,
                    'descripcion': f'Precio ajustado a ${precio} en {region}'
                }
            )
            db.session.add(decision)
            actualizados += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{actualizados} precios actualizados',
            'actualizados': actualizados
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/ventas/analisis-regiones')
@login_required
@estudiante_required
def api_ventas_analisis_regiones():
    """API para an�lisis detallado por regi�n"""
    try:
        empresa = current_user.empresa
        simulacion = Simulacion.query.filter_by(activa=True).first()
        
        regiones = ['Andina', 'Caribe', 'Pac�fica', 'Orinoqu�a', 'Amazon�a']
        regiones_data = []
        
        for region in regiones:
            # Ventas �ltimos 7 d�as
            ventas_recientes = Venta.query.filter_by(
                empresa_id=empresa.id,
                region=region
            ).filter(
                Venta.semana_simulacion >= max(1, simulacion.semana_actual - 7)
            ).all()
            
            # Ventas 7 d�as anteriores para calcular tendencia
            ventas_anteriores = Venta.query.filter_by(
                empresa_id=empresa.id,
                region=region
            ).filter(
                Venta.semana_simulacion >= max(1, simulacion.semana_actual - 14),
                Venta.semana_simulacion < max(1, simulacion.semana_actual - 7)
            ).all()
            
            ingresos_recientes = sum([v.ingreso_total for v in ventas_recientes])
            ingresos_anteriores = sum([v.ingreso_total for v in ventas_anteriores])
            
            # Calcular tendencia
            tendencia = 0
            if ingresos_anteriores > 0:
                tendencia = int(((ingresos_recientes - ingresos_anteriores) / ingresos_anteriores) * 100)
            
            # Producto m�s vendido
            from sqlalchemy import func
            top = db.session.query(
                Producto.nombre
            ).join(Venta).filter(
                Venta.empresa_id == empresa.id,
                Venta.region == region,
                Venta.semana_simulacion >= max(1, simulacion.semana_actual - 7)
            ).group_by(Producto.nombre).order_by(func.sum(Venta.cantidad_vendida).desc()).first()
            
            regiones_data.append({
                'nombre': region,
                'ventas_totales': len(ventas_recientes),
                'ingresos': int(ingresos_recientes),
                'tendencia': tendencia,
                'top_producto': top[0] if top else 'N/A',
                'ventas_perdidas': int(sum([v.cantidad_perdida for v in ventas_recientes]))
            })
        
        return jsonify({
            'success': True,
            'regiones': regiones_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/ventas/competitividad')
@login_required
@estudiante_required
def api_ventas_competitividad():
    """API para obtener informaci�n de competitividad de precios vs mercado"""
    try:
        empresa = current_user.empresa
        simulacion = Simulacion.query.filter_by(activa=True).first()
        
        if not simulacion:
            return jsonify({'success': False, 'message': 'No hay simulaci�n activa'}), 404
        
        productos = Producto.query.filter_by(activo=True).all()
        empresas_competencia = Empresa.query.filter_by(simulacion_id=simulacion.id).all()
        
        competitividad_data = []
        
        for producto in productos:
            # Calcular precio promedio del mercado
            precios_mercado = []
            for emp in empresas_competencia:
                # Por ahora asumimos que todas las empresas usan el mismo precio_actual del producto
                # En el futuro esto podr�a ser por empresa
                inventario = Inventario.query.filter_by(
                    empresa_id=emp.id,
                    producto_id=producto.id
                ).first()
                
                if inventario and inventario.cantidad_actual > 0:
                    precios_mercado.append(producto.precio_actual)
            
            precio_promedio_mercado = sum(precios_mercado) / len(precios_mercado) if precios_mercado else producto.precio_actual
            precio_empresa = producto.precio_actual
            
            # Calcular ratio y clasificaci�n
            ratio = precio_empresa / precio_promedio_mercado if precio_promedio_mercado > 0 else 1.0
            
            if ratio > 1.5:
                clasificacion = 'Muy Alto'
                color = 'danger'
                expectativa_ventas = 'Muy Bajas'
            elif ratio > 1.2:
                clasificacion = 'Alto'
                color = 'warning'
                expectativa_ventas = 'Bajas'
            elif ratio > 0.9:
                clasificacion = 'Competitivo'
                color = 'success'
                expectativa_ventas = 'Normales'
            elif ratio > 0.7:
                clasificacion = 'Bajo'
                color = 'info'
                expectativa_ventas = 'Altas'
            else:
                clasificacion = 'Muy Bajo'
                color = 'warning'
                expectativa_ventas = 'Medias (posible desconfianza)'
            
            # Obtener stock actual
            inventario_empresa = Inventario.query.filter_by(
                empresa_id=empresa.id,
                producto_id=producto.id
            ).first()
            
            stock_actual = inventario_empresa.cantidad_actual if inventario_empresa else 0
            
            competitividad_data.append({
                'producto': producto.nombre,
                'producto_id': producto.id,
                'precio_empresa': precio_empresa,
                'precio_mercado': precio_promedio_mercado,
                'ratio': ratio,
                'diferencia_porcentual': (ratio - 1) * 100,
                'clasificacion': clasificacion,
                'color': color,
                'expectativa_ventas': expectativa_ventas,
                'stock': stock_actual
            })
        
        return jsonify({
            'success': True,
            'competitividad': competitividad_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/ventas/ajustar-precio', methods=['POST'])
@login_required
@estudiante_required
def ajustar_precio():
    """Ajustar precio de un producto - Accesible para todos los roles"""
    # Comentado: Todos los estudiantes pueden acceder a todos los m�dulos para colaborar
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
        
        # Registrar la decisi�n
        simulacion = Simulacion.query.filter_by(activa=True).first()
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            semana_simulacion=simulacion.semana_actual,
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
        flash('Datos inv�lidos', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al ajustar precio: {str(e)}', 'error')
    
    return redirect(url_for('estudiante.dashboard_ventas'))


@bp.route('/ventas/analisis-regional')
@login_required
@estudiante_required
def analisis_regional():
    """Vista detallada de an�lisis por regi�n"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.filter_by(activa=True).first()
    empresa = current_user.empresa
    
    # Datos por regi�n en los �ltimos 14 d�as
    regiones = ['Caribe', 'Pacifica', 'Orinoquia', 'Amazonia', 'Andina']
    dias_analisis = 14
    
    datos_regionales = {}
    for region in regiones:
        ventas = Venta.query.filter_by(
            empresa_id=empresa.id,
            region=region
        ).filter(
            Venta.semana_simulacion >= max(1, simulacion.semana_actual - dias_analisis)
        ).all()
        
        datos_regionales[region] = {
            'ventas': ventas,
            'total_ingresos': sum([v.ingreso_total for v in ventas]),
            'total_unidades': sum([v.cantidad_vendida for v in ventas]),
            'ventas_perdidas': sum([v.cantidad_perdida for v in ventas]),
            'dias_con_ventas': len(set([v.semana_simulacion for v in ventas])),
            'ingreso_promedio_dia': sum([v.ingreso_total for v in ventas]) / dias_analisis if ventas else 0
        }
    
    return render_template('estudiante/ventas/analisis_regional.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         regiones=regiones,
                         datos_regionales=datos_regionales,
                         dias_analisis=dias_analisis)


# API Endpoints para gr�ficos din�micos
@bp.route('/api/ventas/historico-region')
@login_required
@estudiante_required
def api_ventas_historico_region():
    """API: Datos hist�ricos de ventas por regi�n"""
    if current_user.rol != 'ventas':
        return jsonify({'error': 'No autorizado'}), 403
    
    simulacion = Simulacion.query.filter_by(activa=True).first()
    empresa_id = current_user.empresa_id
    dias = int(request.args.get('dias', 14))
    
    regiones = ['Caribe', 'Pacifica', 'Orinoquia', 'Amazonia', 'Andina']
    resultado = {
        'labels': list(range(max(1, simulacion.semana_actual - dias + 1), simulacion.semana_actual + 1)),
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
                semana_simulacion=dia
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
    """API: Relaci�n precio vs demanda para un producto"""
    if current_user.rol != 'ventas':
        return jsonify({'error': 'No autorizado'}), 403
    
    empresa_id = current_user.empresa_id
    dias = int(request.args.get('dias', 14))
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    ventas = Venta.query.filter_by(
        empresa_id=empresa_id,
        producto_id=producto_id
    ).filter(
        Venta.semana_simulacion >= max(1, simulacion.semana_actual - dias)
    ).order_by(Venta.semana_simulacion).all()
    
    # Agrupar por d�a
    datos_por_dia = {}
    for venta in ventas:
        dia = venta.semana_simulacion
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
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    productos = Producto.query.filter_by(activo=True).all()
    
    labels = []
    valores = []
    
    for producto in productos:
        ventas = Venta.query.filter_by(
            empresa_id=empresa_id,
            producto_id=producto.id
        ).filter(
            Venta.semana_simulacion >= max(1, simulacion.semana_actual - dias)
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


# ============== DASHBOARD PLANEACI�N ==============
@bp.route('/planeacion')
@login_required
@estudiante_required
def dashboard_planeacion():
    """Dashboard espec�fico para el rol de Planeaci�n"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.filter_by(activa=True).first()
    empresa = current_user.empresa
    
    # Obtener productos
    productos = Producto.query.filter_by(activo=True).all()
    
    # Obtener inventarios actuales
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    inventarios_dict = {inv.producto_id: inv for inv in inventarios}
    
    # Calcular estad�sticas por producto
    stats_productos = []
    for producto in productos:
        # Ventas hist�ricas del producto
        ventas = Venta.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto.id
        ).order_by(Venta.semana_simulacion).all()
        
        # Datos para an�lisis
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
            'dias_ventas': len(set([v.semana_simulacion for v in ventas]))
        })
    
    # Pron�sticos recientes
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
    
    return render_template('estudiante/planeacion/dashboard_planeacion.html',
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
    """Vista para generar pron�sticos con diferentes m�todos"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.filter_by(activa=True).first()
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
            # Obtener ventas hist�ricas
            ventas = Venta.query.filter_by(
                empresa_id=empresa.id,
                producto_id=producto_id
            ).order_by(Venta.semana_simulacion).all()
            
            # Agrupar por d�a y sumar cantidades
            ventas_por_dia = {}
            for venta in ventas:
                dia = venta.semana_simulacion
                if dia not in ventas_por_dia:
                    ventas_por_dia[dia] = 0
                ventas_por_dia[dia] += venta.cantidad_solicitada
            
            # Crear lista ordenada
            dias_ordenados = sorted(ventas_por_dia.keys())
            datos_historicos = [ventas_por_dia[dia] for dia in dias_ordenados]
            
            # Comparar m�todos si hay suficientes datos
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
    """Guardar un pron�stico generado"""
    # Acceso permitido para todos los roles - Panel unificado
    try:
        producto_id = int(request.form.get('producto_id'))
        metodo = request.form.get('metodo')
        demanda_pronosticada = float(request.form.get('demanda_pronosticada'))
        semana_pronostico = int(request.form.get('semana_pronostico'))
        
        # Par�metros del m�todo
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
        
        # Datos hist�ricos usados (JSON)
        datos_historicos_str = request.form.get('datos_historicos', '[]')
        import json
        datos_historicos = json.loads(datos_historicos_str)
        
        simulacion = Simulacion.query.filter_by(activa=True).first()
        
        # Crear pron�stico
        pronostico = Pronostico(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            semana_generacion=simulacion.semana_actual,
            semana_pronostico=semana_pronostico,
            metodo_usado=metodo,
            parametros=parametros,
            demanda_pronosticada=demanda_pronosticada,
            error_mape=error_mape,
            error_mad=error_mad,
            datos_historicos=datos_historicos
        )
        
        db.session.add(pronostico)
        
        # Registrar decisi�n
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            semana_simulacion=simulacion.semana_actual,
            tipo_decision='pronostico_generado',
            datos_decision={
                'producto_id': producto_id,
                'metodo': metodo,
                'demanda_pronosticada': demanda_pronosticada,
                'semana_pronostico': semana_pronostico
            }
        )
        
        db.session.add(decision)
        db.session.commit()
        
        flash(f'Pron�stico guardado: {demanda_pronosticada:.0f} unidades para d�a {semana_pronostico}', 'success')
        return redirect(url_for('estudiante.generar_pronostico', producto_id=producto_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar pron�stico: {str(e)}', 'error')
        return redirect(url_for('estudiante.generar_pronostico'))


@bp.route('/planeacion/requerimientos')
@login_required
@estudiante_required
def requerimientos_compra():
    """Vista para crear requerimientos de compra"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.filter_by(activa=True).first()
    empresa = current_user.empresa
    
    # Obtener productos y sus datos
    productos = Producto.query.filter_by(activo=True).all()
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    inventarios_dict = {inv.producto_id: inv for inv in inventarios}
    
    # Pron�sticos m�s recientes por producto
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
    """Crear un requerimiento de compra basado en pron�stico"""
    # Acceso permitido para todos los roles - Panel unificado
    try:
        producto_id = int(request.form.get('producto_id'))
        demanda_pronosticada = float(request.form.get('demanda_pronosticada'))
        stock_actual = float(request.form.get('stock_actual'))
        stock_seguridad = float(request.form.get('stock_seguridad'))
        lead_time = int(request.form.get('lead_time'))
        semana_necesidad = int(request.form.get('semana_necesidad'))
        notas = request.form.get('notas', '')
        pronostico_id = request.form.get('pronostico_id')
        
        simulacion = Simulacion.query.filter_by(activa=True).first()
        
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
            semana_generacion=simulacion.semana_actual,
            semana_necesidad=semana_necesidad,
            demanda_pronosticada=demanda_pronosticada,
            stock_actual=stock_actual,
            stock_seguridad=stock_seguridad,
            lead_time=lead_time,
            cantidad_sugerida=cantidad_sugerida,
            notas_planeacion=notas,
            estado='pendiente'
        )
        
        db.session.add(requerimiento)
        
        # Registrar decisi�n
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            semana_simulacion=simulacion.semana_actual,
            tipo_decision='requerimiento_compra',
            datos_decision={
                'producto_id': producto_id,
                'cantidad_sugerida': cantidad_sugerida,
                'demanda_pronosticada': demanda_pronosticada,
                'semana_necesidad': semana_necesidad
            }
        )
        
        db.session.add(decision)
        db.session.commit()
        
        flash(f'Requerimiento creado: {cantidad_sugerida:.0f} unidades para d�a {semana_necesidad}', 'success')
        return redirect(url_for('estudiante.requerimientos_compra'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear requerimiento: {str(e)}', 'error')
        return redirect(url_for('estudiante.requerimientos_compra'))


# APIs para gr�ficos de Planeaci�n
@bp.route('/api/planeacion/historico-producto/<int:producto_id>')
@login_required
@estudiante_required
def api_historico_producto(producto_id):
    """API: Datos hist�ricos de demanda de un producto"""
    if current_user.rol != 'planeacion':
        return jsonify({'error': 'No autorizado'}), 403
    
    empresa_id = current_user.empresa_id
    
    # Obtener ventas del producto
    ventas = Venta.query.filter_by(
        empresa_id=empresa_id,
        producto_id=producto_id
    ).order_by(Venta.semana_simulacion).all()
    
    # Agrupar por d�a
    ventas_por_dia = {}
    for venta in ventas:
        dia = venta.semana_simulacion
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
    """Dashboard espec�fico para el rol de Compras"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.filter_by(activa=True).first()
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
            ).order_by(Venta.semana_simulacion.desc()).limit(14).all()
            
            # Analizar inventario
            analisis = analizar_inventario(inventario, ventas)
            
            analisis_productos.append({
                'producto': producto,
                'inventario': inventario,
                **analisis
            })
    
    # Priorizar productos
    productos_priorizados = priorizar_productos_compra(analisis_productos)
    
    # Requerimientos de Planeaci�n pendientes
    requerimientos = RequerimientoCompra.query.filter_by(
        empresa_id=empresa.id,
        estado='pendiente'
    ).order_by(RequerimientoCompra.created_at.desc()).all()
    
    # �rdenes de compra recientes
    ordenes_compra = Compra.query.filter_by(empresa_id=empresa.id)\
        .order_by(Compra.semana_orden.desc())\
        .limit(15).all()
    
    # �rdenes en tr�nsito
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
    """Vista de requerimientos de Planeaci�n"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.filter_by(activa=True).first()
    empresa = current_user.empresa
    
    # Obtener todos los requerimientos
    requerimientos_pendientes = RequerimientoCompra.query.filter_by(
        empresa_id=empresa.id,
        estado='pendiente'
    ).order_by(RequerimientoCompra.semana_necesidad).all()
    
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
    """Crear orden de compra desde un requerimiento de Planeaci�n"""
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
        
        simulacion = Simulacion.query.filter_by(activa=True).first()
        producto = Producto.query.get(requerimiento.producto_id)
        
        # Calcular costos (con posible ajuste por disrupci�n Opci�n A)
        costo_unitario = producto.costo_unitario
        tiempo_entrega = producto.tiempo_entrega

        dis_opcion_a = DisrupcionEmpresa.query.filter(
            DisrupcionEmpresa.empresa_id == current_user.empresa_id,
            DisrupcionEmpresa.simulacion_id == simulacion.id,
            DisrupcionEmpresa.producto_afectado_id == requerimiento.producto_id,
            DisrupcionEmpresa.activa == True,
            DisrupcionEmpresa.opcion_elegida == 'A'
        ).first()
        if dis_opcion_a:
            from utils.catalogo_disrupciones import get_disrupcion
            cat = get_disrupcion(dis_opcion_a.disrupcion_key)
            if cat:
                efectos_a = cat['opciones']['A']['efectos']
                costo_unitario *= efectos_a.get('costo_multiplicador', 1.20)
                tiempo_entrega = efectos_a.get('tiempo_entrega_override', tiempo_entrega)
                pedido_min = efectos_a.get('pedido_minimo', 0)
                if cantidad < pedido_min:
                    flash(f'?? Con el proveedor alterno, el pedido m�nimo es {pedido_min:.0f} unidades.', 'error')
                    return redirect(url_for('estudiante.ver_requerimientos'))

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
        semana_entrega = simulacion.semana_actual + tiempo_entrega

        compra = Compra(
            empresa_id=current_user.empresa_id,
            producto_id=requerimiento.producto_id,
            semana_orden=simulacion.semana_actual,
            semana_entrega=semana_entrega,
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
        
        # Registrar decisi�n
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            semana_simulacion=simulacion.semana_actual,
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
        
        flash(f'Orden creada: {cantidad:.0f} unidades de {producto.nombre}. Llegar� d�a {semana_entrega}', 'success')
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
        
        simulacion = Simulacion.query.filter_by(activa=True).first()
        producto = Producto.query.get(producto_id)
        
        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('estudiante.dashboard_compras'))
        
        # Calcular costos (con posible ajuste por disrupci�n Opci�n A)
        costo_unitario = producto.costo_unitario
        tiempo_entrega = producto.tiempo_entrega

        dis_opcion_a = DisrupcionEmpresa.query.filter(
            DisrupcionEmpresa.empresa_id == current_user.empresa_id,
            DisrupcionEmpresa.simulacion_id == simulacion.id,
            DisrupcionEmpresa.producto_afectado_id == producto_id,
            DisrupcionEmpresa.activa == True,
            DisrupcionEmpresa.opcion_elegida == 'A'
        ).first()
        if dis_opcion_a:
            from utils.catalogo_disrupciones import get_disrupcion
            cat = get_disrupcion(dis_opcion_a.disrupcion_key)
            if cat:
                efectos_a = cat['opciones']['A']['efectos']
                costo_unitario *= efectos_a.get('costo_multiplicador', 1.20)
                tiempo_entrega = efectos_a.get('tiempo_entrega_override', tiempo_entrega)
                pedido_min = efectos_a.get('pedido_minimo', 0)
                if cantidad < pedido_min:
                    flash(f'?? Con el proveedor alterno, el pedido m�nimo es {pedido_min:.0f} unidades.', 'error')
                    return redirect(url_for('estudiante.dashboard_compras'))

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
        semana_entrega = simulacion.semana_actual + tiempo_entrega
        
        compra = Compra(
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            semana_orden=simulacion.semana_actual,
            semana_entrega=semana_entrega,
            cantidad=cantidad,
            costo_unitario=costo_unitario,
            costo_total=costo_total,
            estado='en_transito'
        )
        
        # Actualizar capital
        empresa.capital_actual -= costo_total
        
        # Registrar decisi�n
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            semana_simulacion=simulacion.semana_actual,
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
        
        flash(f'Orden creada: {cantidad:.0f} unidades. Llegar� d�a {semana_entrega}', 'success')
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
    """API: Estado del inventario para gr�ficos"""
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


# ============== DASHBOARD LOG�STICA ==============
# ============== DASHBOARD LOG�STICA ==============
@bp.route('/logistica')
@login_required
@estudiante_required
def dashboard_logistica():
    """Dashboard espec�fico para el rol de Log�stica"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.filter_by(activa=True).first()
    empresa = current_user.empresa
    
    # Obtener inventarios
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    productos = Producto.query.filter_by(activo=True).all()
    
    # �rdenes de compra en tr�nsito (pendientes de recibir)
    ordenes_transito = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).order_by(Compra.semana_entrega).all()
    
    # �rdenes que llegan hoy
    ordenes_hoy = [o for o in ordenes_transito if o.semana_entrega == simulacion.semana_actual]
    
    # Despachos regionales pendientes y en tr�nsito
    despachos_pendientes = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        estado='pendiente'
    ).count()
    
    despachos_transito = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).count()
    
    # An�lisis de inventario por regi�n
    regiones = ['Andina', 'Caribe', 'Pac�fica', 'Orinoqu�a', 'Amazon�a']
    stock_por_region = {}
    
    for region in regiones:
        # Obtener ventas de esta regi�n
        ventas_region = Venta.query.filter_by(
            empresa_id=empresa.id,
            region=region
        ).all()
        
        # Calcular stock necesario (simplificado - en producci�n habr�a tabla de stock regional)
        total_vendido = sum(v.cantidad_vendida for v in ventas_region[-14:])  # �ltimos 14 d�as
        
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
        ).order_by(Venta.semana_simulacion.desc()).limit(14).all()
        
        alertas = generar_alertas_logistica(inv, ventas_producto, ordenes_transito)
        if alertas:
            alertas_generales.extend([{**a, 'producto': inv.producto.nombre} for a in alertas])
    
    # Movimientos recientes de inventario
    movimientos_recientes = MovimientoInventario.query.filter_by(
        empresa_id=empresa.id
    ).order_by(MovimientoInventario.created_at.desc()).limit(10).all()
    
    return render_template('estudiante/logistica/dashboard_logistica.html',
                         simulacion=simulacion,
                         empresa=empresa)


@bp.route('/logistica/recepcion')
@login_required
@estudiante_required
def vista_recepcion():
    """Vista de recepci�n de �rdenes de compra"""
    # Acceso permitido para todos los roles - Panel unificado
    simulacion = Simulacion.query.filter_by(activa=True).first()
    empresa = current_user.empresa
    
    # �rdenes en tr�nsito
    ordenes_transito = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).order_by(Compra.semana_entrega).all()
    
    # �rdenes recibidas (entregadas)
    ordenes_recibidas = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='entregado'
    ).order_by(Compra.semana_entrega.desc()).limit(20).all()
    
    return render_template('estudiante/logistica/recepcion.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         ordenes_transito=ordenes_transito,
                         ordenes_recibidas=ordenes_recibidas)


@bp.route('/logistica/recibir-orden/<int:compra_id>', methods=['POST'])
@login_required
@estudiante_required
def recibir_orden_compra(compra_id):
    """Procesar recepci�n de una orden de compra"""
    # Acceso permitido para todos los roles - Panel unificado
    try:
        compra = Compra.query.get_or_404(compra_id)
        
        if compra.empresa_id != current_user.empresa_id:
            flash('No autorizado', 'error')
            return redirect(url_for('estudiante.vista_recepcion'))
        
        if compra.estado != 'en_transito':
            flash('Esta orden ya fue recibida o no est� en tr�nsito', 'warning')
            return redirect(url_for('estudiante.vista_recepcion'))
        
        simulacion = Simulacion.query.filter_by(activa=True).first()
        
        # Verificar que sea el d�a de entrega o posterior
        if simulacion.semana_actual < compra.semana_entrega:
            flash(f'Esta orden llega el d�a {compra.semana_entrega}. A�n no puede ser recibida.', 'warning')
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
        
        # Procesar recepci�n
        resultado = procesar_recepcion_compra(compra, inventario)
        
        # Actualizar estado de la compra
        compra.estado = 'entregado'
        
        # Registrar movimiento de inventario
        movimiento = MovimientoInventario(
            empresa_id=current_user.empresa_id,
            producto_id=compra.producto_id,
            usuario_id=current_user.id,
            semana_simulacion=simulacion.semana_actual,
            tipo_movimiento='entrada_compra',
            cantidad=compra.cantidad,
            saldo_anterior=resultado['cantidad_anterior'],
            saldo_nuevo=resultado['cantidad_nueva'],
            compra_id=compra.id,
            observaciones=f"Recepci�n de compra. Costo unitario: ${compra.costo_unitario:,.0f}"
        )
        
        db.session.add(movimiento)
        
        # Registrar decisi�n
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            semana_simulacion=simulacion.semana_actual,
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
    simulacion = Simulacion.query.filter_by(activa=True).first()
    empresa = current_user.empresa
    
    # Inventarios disponibles
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    
    # Calcular stock disponible para cada producto
    stock_disponible = {}
    for inv in inventarios:
        disponible = calcular_stock_disponible_despacho(inv)
        stock_disponible[inv.producto_id] = disponible
    
    # Ventas recientes (�ltimos 5 d�as) para an�lisis de demanda
    ventas_recientes = Venta.query.filter_by(
        empresa_id=empresa.id
    ).filter(Venta.semana_simulacion > simulacion.semana_actual - 6)\
        .order_by(Venta.semana_simulacion.desc()).all()
    
    # An�lisis de demanda por regi�n
    regiones = ['Andina', 'Caribe', 'Pac�fica', 'Orinoqu�a', 'Amazon�a']
    analisis_regiones = {}
    
    for region in regiones:
        # Ventas recientes de esta regi�n
        ventas_region = Venta.query.filter_by(
            empresa_id=empresa.id,
            region=region
        ).order_by(Venta.semana_simulacion.desc()).limit(14).all()
        
        # Calcular demanda por producto
        demanda_productos = {}
        for inv in inventarios:
            ventas_producto = [v for v in ventas_region if v.producto_id == inv.producto_id]
            total = sum(v.cantidad_vendida for v in ventas_producto)
            dias = len(set(v.semana_simulacion for v in ventas_producto)) or 1
            demanda_productos[inv.producto_id] = total / dias
        
        analisis_regiones[region] = {
            'demanda_productos': demanda_productos,
            'tiempo_entrega': calcular_tiempo_entrega_region(region)
        }
    
    # Despachos pendientes y en tr�nsito
    despachos_activos = DespachoRegional.query.filter_by(
        empresa_id=empresa.id
    ).filter(DespachoRegional.estado.in_(['pendiente', 'en_transito']))\
        .order_by(DespachoRegional.created_at.desc()).all()
    
    # Despachos entregados recientes
    despachos_entregados = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        estado='entregado'
    ).order_by(DespachoRegional.semana_entrega_real.desc()).limit(15).all()
    
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
    """Crear un despacho a una regi�n"""
    # Acceso permitido para todos los roles - Panel unificado
    try:
        producto_id = int(request.form.get('producto_id'))
        region = request.form.get('region')
        cantidad = float(request.form.get('cantidad'))
        
        simulacion = Simulacion.query.filter_by(activa=True).first()
        
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
        semana_entrega = simulacion.semana_actual + tiempo_entrega
        
        # Crear despacho
        despacho = DespachoRegional(
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            usuario_logistica_id=current_user.id,
            region=region,
            semana_despacho=simulacion.semana_actual,
            semana_entrega_estimado=semana_entrega,
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
            semana_simulacion=simulacion.semana_actual,
            tipo_movimiento='salida_despacho',
            cantidad=cantidad,
            saldo_anterior=inventario.cantidad_actual + cantidad,
            saldo_nuevo=inventario.cantidad_actual,
            observaciones=f"Despacho a regi�n {region}"
        )
        
        db.session.add(despacho)
        db.session.add(movimiento)
        db.session.flush()
        
        # Vincular movimiento con despacho
        movimiento.despacho_id = despacho.id
        
        # Registrar decisi�n
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            semana_simulacion=simulacion.semana_actual,
            tipo_decision='despacho_regional',
            datos_decision={
                'producto_id': producto_id,
                'region': region,
                'cantidad': cantidad,
                'semana_entrega': semana_entrega
            }
        )
        
        db.session.add(decision)
        db.session.commit()
        
        if validacion.get('alerta_stock_bajo'):
            flash(f'Despacho creado. {validacion["recomendacion"]}', 'warning')
        else:
            flash(f'Despacho creado: {cantidad:.0f} unidades a {region}. Llegada estimada: d�a {semana_entrega}', 'success')
        
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
    simulacion = Simulacion.query.filter_by(activa=True).first()
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
    
    # Estad�sticas
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
    
    # Crear diccionario de estad�sticas
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
    """Actualizar par�metros de control de inventario"""
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
    
    # Registrar decisi�n
    simulacion = Simulacion.query.filter_by(activa=True).first()
    decision = Decision(
        usuario_id=current_user.id,
        empresa_id=current_user.empresa_id,
        semana_simulacion=simulacion.semana_actual,
        tipo_decision='parametros_inventario',
        datos_decision={
            'inventario_id': inventario_id,
            'punto_reorden': punto_reorden,
            'stock_seguridad': stock_seguridad
        }
    )
    
    db.session.add(decision)
    db.session.commit()
    
    flash('Par�metros de inventario actualizados', 'success')
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


# ============== API PLANEACI�N - PRON�STICOS Y MRP ==============

@bp.route('/api/producto/<int:producto_id>/historico')
@login_required
@estudiante_required
def api_producto_historico(producto_id):
    """API: Obtener datos hist�ricos de demanda de un producto"""
    empresa = current_user.empresa
    
    # Obtener ventas hist�ricas
    ventas = Venta.query.filter_by(
        empresa_id=empresa.id,
        producto_id=producto_id
    ).order_by(Venta.semana_simulacion).all()
    
    historico = []
    for venta in ventas:
        historico.append({
            'dia': venta.semana_simulacion,
            'demanda_real': venta.cantidad_vendida + venta.cantidad_perdida,
            'ventas': venta.cantidad_vendida,
            'perdida': venta.cantidad_perdida
        })
    
    return jsonify({'historico': historico})


@bp.route('/api/calcular-pronostico', methods=['POST'])
@login_required
@estudiante_required
def api_calcular_pronostico():
    """API: Calcular pron�stico con diferentes m�todos"""
    data = request.get_json()
    producto_id = data.get('producto_id')
    metodo = data.get('metodo')
    parametros = data.get('parametros', {})
    dias_pronostico = data.get('dias_pronostico', 7)
    
    empresa = current_user.empresa
    
    # Obtener datos hist�ricos
    ventas = Venta.query.filter_by(
        empresa_id=empresa.id,
        producto_id=producto_id
    ).order_by(Venta.semana_simulacion).all()
    
    if not ventas:
        return jsonify({'error': 'No hay datos hist�ricos para este producto'}), 400
    
    # Preparar serie temporal
    demanda_historica = [v.cantidad_vendida + v.cantidad_perdida for v in ventas]
    
    # Calcular pron�stico seg�n m�todo
    pronosticos = []
    
    if metodo == 'promedio_movil':
        n = parametros.get('n', 3)
        pronosticos = promedio_movil(demanda_historica, n, dias_pronostico)
    
    elif metodo == 'exp_simple':
        alpha = parametros.get('alpha', 0.3)
        pronosticos = suavizacion_exponencial_simple(demanda_historica, alpha, dias_pronostico)
    
    elif metodo == 'holt':
        alpha = parametros.get('alpha', 0.3)
        beta = parametros.get('beta', 0.2)
        pronosticos = suavizacion_exponencial_doble_holt(demanda_historica, alpha, beta, dias_pronostico)
    
    elif metodo == 'manual':
        # Para m�todo manual, devolver el promedio como base
        promedio = sum(demanda_historica) / len(demanda_historica)
        pronosticos = [promedio] * dias_pronostico
    
    else:
        return jsonify({'error': 'M�todo no v�lido'}), 400
    
    # Calcular m�tricas de error
    mape = 0
    mad = 0
    
    if len(demanda_historica) > 1:
        # Calcular error en los datos hist�ricos
        errores = []
        for i in range(1, len(demanda_historica)):
            if metodo == 'promedio_movil':
                n = parametros.get('n', 3)
                if i >= n:
                    pred = sum(demanda_historica[i-n:i]) / n
                    error = abs(demanda_historica[i] - pred)
                    errores.append(error)
                    if demanda_historica[i] > 0:
                        mape += (error / demanda_historica[i]) * 100
        
        if errores:
            mad = sum(errores) / len(errores)
            if len(errores) > 0:
                mape = mape / len(errores)
    
    # Preparar datos hist�ricos para gr�fico
    historico = [{'dia': v.semana_simulacion, 'demanda_real': v.cantidad_vendida + v.cantidad_perdida} for v in ventas]
    
    return jsonify({
        'pronosticos': pronosticos,
        'historico': historico,
        'mape': mape,
        'mad': mad,
        'promedio': sum(demanda_historica) / len(demanda_historica) if demanda_historica else 0
    })


@bp.route('/api/guardar-pronostico', methods=['POST'])
@login_required
@estudiante_required
def api_guardar_pronostico():
    """API: Guardar pron�stico en base de datos"""
    data = request.get_json()
    producto_id = data.get('producto_id')
    metodo = data.get('metodo')
    pronosticos = data.get('pronosticos', [])
    mape = data.get('mape', 0)
    mad = data.get('mad', 0)
    
    empresa = current_user.empresa
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    # Guardar cada pron�stico
    for i, valor in enumerate(pronosticos):
        semana_pronostico = simulacion.semana_actual + i + 1
        
        pronostico = Pronostico(
            usuario_id=current_user.id,
            empresa_id=empresa.id,
            producto_id=producto_id,
            semana_generacion=simulacion.semana_actual,
            semana_pronostico=semana_pronostico,
            metodo_usado=metodo,
            demanda_pronosticada=valor,
            error_mape=mape,
            error_mad=mad
        )
        db.session.add(pronostico)
    
    db.session.commit()
    
    return jsonify({'success': True, 'pronosticos_guardados': len(pronosticos)})


@bp.route('/api/calcular-mrp')
@login_required
@estudiante_required
def api_calcular_mrp():
    """API: Calcular MRP (Material Requirements Planning) para todos los productos"""
    empresa = current_user.empresa
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    productos = Producto.query.filter_by(activo=True).all()
    
    resultados = []
    criticos = 0
    advertencia = 0
    optimos = 0
    capital_total = 0
    
    for producto in productos:
        # Stock actual
        inventario = Inventario.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto.id
        ).first()
        
        stock_actual = inventario.cantidad_actual if inventario else 0
        
        # Pedidos en tr�nsito
        compras_transito = Compra.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto.id,
            estado='en_transito'
        ).all()
        
        en_transito = sum([c.cantidad for c in compras_transito])
        
        # Pron�stico pr�ximos 7 d�as
        pronosticos = Pronostico.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto.id
        ).filter(
            Pronostico.semana_pronostico > simulacion.semana_actual,
            Pronostico.semana_pronostico <= simulacion.semana_actual + 7
        ).all()
        
        if pronosticos:
            pronostico_total = sum([p.demanda_pronosticada for p in pronosticos])
        else:
            # Si no hay pron�stico, usar promedio hist�rico
            ventas = Venta.query.filter_by(
                empresa_id=empresa.id,
                producto_id=producto.id
            ).all()
            
            if ventas:
                demanda_promedio = sum([v.cantidad_vendida + v.cantidad_perdida for v in ventas]) / len(ventas)
                pronostico_total = demanda_promedio * 7
            else:
                pronostico_total = 0
        
        # C�lculo de cobertura
        stock_disponible = stock_actual + en_transito
        dias_cobertura = (stock_disponible / (pronostico_total / 7)) if pronostico_total > 0 else 999
        
        # Determinar status y recomendaci�n
        if dias_cobertura < 3:
            status_class = 'status-critico'
            status_text = 'CR�TICO'
            criticos += 1
            # Recomendar para 10 d�as
            cantidad_recomendada = max(0, int((pronostico_total / 7) * 10 - stock_disponible))
            justificacion = f'Stock bajo ({dias_cobertura:.1f} d�as)'
        elif dias_cobertura < 7:
            status_class = 'status-bajo'
            status_text = 'ADVERTENCIA'
            advertencia += 1
            cantidad_recomendada = max(0, int((pronostico_total / 7) * 10 - stock_disponible))
            justificacion = f'Stock justo ({dias_cobertura:.1f} d�as)'
        else:
            status_class = 'status-optimo'
            status_text = '�PTIMO'
            optimos += 1
            cantidad_recomendada = 0
            justificacion = f'Stock suficiente ({dias_cobertura:.1f} d�as)'
        
        capital_total += cantidad_recomendada * producto.costo_unitario
        
        resultados.append({
            'id': producto.id,
            'stock_actual': stock_actual,
            'en_transito': en_transito,
            'pronostico_proximos_dias': int(pronostico_total),
            'dias_cobertura': dias_cobertura,
            'status_class': status_class,
            'status_text': status_text,
            'cantidad_recomendada': cantidad_recomendada,
            'justificacion': justificacion
        })
    
    return jsonify({
        'productos': resultados,
        'resumen': {
            'criticos': criticos,
            'advertencia': advertencia,
            'optimos': optimos,
            'capital_requerido': capital_total
        }
    })


@bp.route('/api/producto/<int:producto_id>/precio')
@login_required
@estudiante_required
def api_producto_precio(producto_id):
    """API: Obtener precio de un producto"""
    producto = Producto.query.get_or_404(producto_id)
    
    return jsonify({
        'precio_compra': producto.costo_unitario,
        'precio_venta': producto.precio_actual
    })


@bp.route('/api/generar-requerimiento', methods=['POST'])
@login_required
@estudiante_required
def api_generar_requerimiento():
    """API: Generar requerimiento de compra"""
    data = request.get_json()
    producto_id = data.get('producto_id')
    cantidad = data.get('cantidad')
    
    empresa = current_user.empresa
    simulacion = Simulacion.query.filter_by(activa=True).first()
    producto = Producto.query.get(producto_id)
    
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    # Obtener inventario actual
    inventario = Inventario.query.filter_by(
        empresa_id=empresa.id,
        producto_id=producto_id
    ).first()
    
    stock_actual = inventario.cantidad_actual if inventario else 0
    stock_seguridad = inventario.stock_seguridad if inventario else 0
    
    # Crear requerimiento
    requerimiento = RequerimientoCompra(
        empresa_id=empresa.id,
        producto_id=producto_id,
        usuario_planeacion_id=current_user.id,
        semana_generacion=simulacion.semana_actual,
        semana_necesidad=simulacion.semana_actual + producto.tiempo_entrega,
        demanda_pronosticada=cantidad,
        stock_actual=stock_actual,
        stock_seguridad=stock_seguridad,
        lead_time=producto.tiempo_entrega,
        cantidad_sugerida=cantidad,
        estado='pendiente'
    )
    
    db.session.add(requerimiento)
    
    # Registrar decisi�n
    decision = Decision(
        usuario_id=current_user.id,
        empresa_id=empresa.id,
        tipo_decision='requerimiento_compra',
        semana_simulacion=simulacion.semana_actual,
        datos_decision={
            'producto_id': producto_id,
            'cantidad': cantidad,
            'costo_estimado': cantidad * producto.costo_unitario,
            'descripcion': f'Requerimiento de {cantidad} unidades de {producto.nombre}'
        }
    )
    db.session.add(decision)
    
    db.session.commit()
    
    return jsonify({'success': True, 'requerimiento_id': requerimiento.id})


@bp.route('/api/generar-todas-ordenes', methods=['POST'])
@login_required
@estudiante_required
def api_generar_todas_ordenes():
    """API: Generar requerimientos para todos los productos con recomendaciones"""
    empresa = current_user.empresa
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    # Calcular MRP primero
    response = api_calcular_mrp()
    data = response.get_json()
    
    ordenes_generadas = 0
    
    for prod in data['productos']:
        if prod['cantidad_recomendada'] > 0:
            producto = Producto.query.get(prod['id'])
            
            # Obtener inventario actual
            inventario = Inventario.query.filter_by(
                empresa_id=empresa.id,
                producto_id=prod['id']
            ).first()
            
            stock_actual = inventario.cantidad_actual if inventario else 0
            stock_seguridad = inventario.stock_seguridad if inventario else 0
            
            requerimiento = RequerimientoCompra(
                empresa_id=empresa.id,
                producto_id=prod['id'],
                usuario_planeacion_id=current_user.id,
                semana_generacion=simulacion.semana_actual,
                semana_necesidad=simulacion.semana_actual + producto.tiempo_entrega,
                demanda_pronosticada=prod['pronostico_proximos_dias'] / 7,
                stock_actual=stock_actual,
                stock_seguridad=stock_seguridad,
                lead_time=producto.tiempo_entrega,
                cantidad_sugerida=prod['cantidad_recomendada'],
                estado='pendiente',
                notas_planeacion=prod['justificacion']
            )
            
            db.session.add(requerimiento)
            
            # Registrar decisi�n
            decision = Decision(
                usuario_id=current_user.id,
                empresa_id=empresa.id,
                tipo_decision='requerimiento_compra',
                semana_simulacion=simulacion.semana_actual,
                datos_decision={
                    'producto_id': prod['id'],
                    'cantidad': prod['cantidad_recomendada'],
                    'automatico': True,
                    'justificacion': prod['justificacion'],
                    'descripcion': f'Requerimiento autom�tico de {prod["cantidad_recomendada"]} unidades de {producto.nombre}'
                }
            )
            db.session.add(decision)
            
            ordenes_generadas += 1
    
    db.session.commit()
    
    return jsonify({'success': True, 'ordenes_generadas': ordenes_generadas})


# ============== API LOG�STICA ==============
@bp.route('/api/logistica/stock')
@login_required
@estudiante_required
def api_logistica_stock():
    """Obtener stock disponible para despachos"""
    empresa = current_user.empresa
    
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    
    stock_data = []
    for inv in inventarios:
        stock_data.append({
            'producto_id': inv.producto_id,
            'producto_nombre': inv.producto.nombre,
            'stock_actual': inv.cantidad_actual,
            'stock_seguridad': inv.stock_seguridad,
            'capacidad_maxima': inv.producto.capacidad_produccion if hasattr(inv.producto, 'capacidad_produccion') else 1000
        })
    
    return jsonify({'success': True, 'stock': stock_data})


@bp.route('/api/logistica/despachar', methods=['POST'])
@login_required
@estudiante_required
def api_logistica_despachar():
    """Crear un nuevo despacho regional"""
    empresa = current_user.empresa
    simulacion = Simulacion.query.filter_by(activa=True).first()
    data = request.get_json()
    
    producto_id = data.get('producto_id')
    cantidad = data.get('cantidad')
    region = data.get('region')
    
    if not all([producto_id, cantidad, region]):
        return jsonify({'success': False, 'message': 'Faltan datos requeridos'}), 400
    
    # Validar producto
    producto = Producto.query.get(producto_id)
    if not producto:
        return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404
    
    # Validar inventario
    inventario = Inventario.query.filter_by(
        empresa_id=empresa.id,
        producto_id=producto_id
    ).first()
    
    if not inventario:
        return jsonify({'success': False, 'message': 'Producto no disponible en inventario'}), 400
    
    if inventario.cantidad_actual < cantidad:
        return jsonify({
            'success': False, 
            'message': f'Stock insuficiente. Disponible: {inventario.cantidad_actual}'
        }), 400
    
    # Calcular tiempo de entrega seg�n regi�n
    tiempos_entrega = {
        'Andina': 3,
        'Caribe': 4,
        'Pac�fica': 4,
        'Orinoqu�a': 5,
        'Amazon�a': 6
    }
    dias_entrega = tiempos_entrega.get(region, 4)
    dia_llegada = simulacion.semana_actual + dias_entrega
    
    # Crear despacho
    despacho = DespachoRegional(
        empresa_id=empresa.id,
        producto_id=producto_id,
        region=region,
        cantidad=cantidad,
        semana_despacho=simulacion.semana_actual,
        semana_entrega_estimado=dia_llegada,
        estado='en_transito',
        usuario_logistica_id=current_user.id
    )
    
    # Actualizar inventario
    inventario.cantidad_actual -= cantidad
    
    # Registrar movimiento
    movimiento = MovimientoInventario(
        empresa_id=empresa.id,
        producto_id=producto_id,
        tipo_movimiento='salida_despacho',
        cantidad=cantidad,
        semana_simulacion=simulacion.semana_actual,
        descripcion=f'Despacho a {region}',
        usuario_id=current_user.id
    )
    
    # Registrar decisi�n
    decision = Decision(
        usuario_id=current_user.id,
        empresa_id=empresa.id,
        tipo_decision='despacho_regional',
        semana_simulacion=simulacion.semana_actual,
        datos_decision={
            'producto_id': producto_id,
            'producto_nombre': producto.nombre,
            'cantidad': cantidad,
            'region': region,
            'dia_llegada': dia_llegada,
            'descripcion': f'Despacho de {cantidad} unidades de {producto.nombre} a {region}'
        }
    )
    
    db.session.add(despacho)
    db.session.add(movimiento)
    db.session.add(decision)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Despacho creado exitosamente. Llegar� a {region} el d�a {dia_llegada}'
    })


@bp.route('/api/logistica/despachar-multiple', methods=['POST'])
@login_required
@estudiante_required
def api_logistica_despachar_multiple():
    """Crear m�ltiples despachos a diferentes regiones en una sola operaci�n"""
    try:
        data = request.get_json()
        producto_id = data.get('producto_id')
        despachos_data = data.get('despachos', [])  # [{region: 'Andina', cantidad: 50}, ...]
        
        if not producto_id or not despachos_data:
            return jsonify({
                'success': False,
                'message': 'Datos incompletos'
            }), 400
        
        # Validar que hay al menos un despacho
        if len(despachos_data) == 0:
            return jsonify({
                'success': False,
                'message': 'Debe especificar al menos una regi�n con cantidad'
            }), 400
        
        empresa = current_user.empresa
        if not empresa:
            return jsonify({
                'success': False,
                'message': 'No tienes una empresa asignada'
            }), 400
            
        simulacion = Simulacion.query.filter_by(activa=True).first()
        if not simulacion:
            return jsonify({
                'success': False,
                'message': 'No hay simulaci�n activa'
            }), 400
            
        producto = Producto.query.get(producto_id)
        inventario = Inventario.query.filter_by(
            empresa_id=empresa.id,
            producto_id=producto_id
        ).first()
        
        if not producto or not inventario:
            return jsonify({
                'success': False,
                'message': 'Producto no encontrado en inventario'
            }), 404
        
        # Calcular cantidad total
        cantidad_total = sum(d.get('cantidad', 0) for d in despachos_data)
        
        # Validar stock suficiente
        if inventario.cantidad_actual < cantidad_total:
            return jsonify({
                'success': False,
                'message': f'Stock insuficiente. Disponible: {inventario.cantidad_actual}, Solicitado: {cantidad_total}'
            }), 400
        
        # Tiempos de entrega seg�n regi�n
        tiempos_entrega = {
            'Andina': 3,
            'Caribe': 4,
            'Pac�fica': 4,
            'Orinoqu�a': 5,
            'Amazon�a': 6
        }
        
        despachos_creados = []
        
        # Crear cada despacho
        for despacho_info in despachos_data:
            region = despacho_info.get('region')
            cantidad = despacho_info.get('cantidad', 0)
            
            if cantidad <= 0:
                continue
            
            dias_entrega = tiempos_entrega.get(region, 4)
            dia_llegada = simulacion.semana_actual + dias_entrega
            
            # Crear despacho
            despacho = DespachoRegional(
                empresa_id=empresa.id,
                producto_id=producto_id,
                region=region,
                cantidad=cantidad,
                semana_despacho=simulacion.semana_actual,
                semana_entrega_estimado=dia_llegada,
                estado='en_transito',
                usuario_logistica_id=current_user.id
            )
            
            db.session.add(despacho)
            despachos_creados.append({
                'region': region,
                'cantidad': cantidad,
                'dia_llegada': dia_llegada
            })
        
        # Actualizar inventario una sola vez con el total
        saldo_anterior = inventario.cantidad_actual
        inventario.cantidad_actual -= cantidad_total
        saldo_nuevo = inventario.cantidad_actual
        
        # Registrar movimiento total
        regiones_str = ', '.join([f"{d['region']}: {d['cantidad']}" for d in despachos_creados])
        movimiento = MovimientoInventario(
            empresa_id=empresa.id,
            producto_id=producto_id,
            tipo_movimiento='salida_despacho',
            cantidad=cantidad_total,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_nuevo,
            semana_simulacion=simulacion.semana_actual,
            observaciones=f'Despachos m�ltiples ({regiones_str})',
            usuario_id=current_user.id
        )
        
        # Registrar decisi�n
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=empresa.id,
            tipo_decision='despacho_regional_multiple',
            semana_simulacion=simulacion.semana_actual,
            datos_decision={
                'producto_id': producto_id,
                'producto_nombre': producto.nombre,
                'cantidad_total': cantidad_total,
                'despachos': despachos_creados,
                'descripcion': f'Despachos de {cantidad_total} unidades de {producto.nombre} a {len(despachos_creados)} regiones'
            }
        )
        
        db.session.add(movimiento)
        db.session.add(decision)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(despachos_creados)} despachos creados exitosamente',
            'despachos_creados': len(despachos_creados),
            'cantidad_total': cantidad_total,
            'despachos': despachos_creados
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al procesar despachos: {str(e)}'
        }), 500


@bp.route('/api/logistica/transito')
@login_required
@estudiante_required
def api_logistica_transito():
    """Obtener compras y despachos en tr�nsito"""
    empresa = current_user.empresa
    
    # Compras en tr�nsito
    compras = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).order_by(Compra.semana_entrega).all()
    
    compras_data = []
    for compra in compras:
        compras_data.append({
            'id': compra.id,
            'producto_id': compra.producto_id,
            'producto_nombre': compra.producto.nombre,
            'cantidad': compra.cantidad,
            'semana_entrega': compra.semana_entrega
        })
    
    # Despachos en tr�nsito
    despachos = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).order_by(DespachoRegional.semana_entrega_estimado).all()
    
    despachos_data = []
    for despacho in despachos:
        despachos_data.append({
            'id': despacho.id,
            'producto_id': despacho.producto_id,
            'producto_nombre': despacho.producto.nombre,
            'cantidad': despacho.cantidad,
            'region_destino': despacho.region,
            'dia_llegada': despacho.semana_entrega_estimado
        })
    
    return jsonify({
        'success': True,
        'compras': compras_data,
        'despachos': despachos_data
    })
