"""
Rutas para el rol Profesor (Administrador)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func
from models import (Usuario, Empresa, Simulacion, Inventario, Venta, Compra, Decision,
                    Metrica, Producto, MovimientoInventario, DespachoRegional,
                    RequerimientoCompra, Pronostico, DisrupcionEmpresa)
from extensions import db
from datetime import datetime
import random
from utils.procesamiento_dias import (
    avanzar_simulacion,
    obtener_resumen_simulacion,
    asegurar_metricas_base_dia_uno
)
from utils.reinicio_simulacion import reiniciar_simulacion
from utils.demanda_central import exportar_demanda_csv, importar_demanda_csv, generar_base_demanda_simulacion
from utils.parametros_iniciales import (
    CAPITAL_INICIAL_EMPRESA_DEFAULT,
    INVENTARIO_INICIAL_750_DEFAULT,
    INVENTARIO_INICIAL_1L_DEFAULT,
    DURACION_SIMULACION_SEMANAS,
    DIAS_HISTORICO_DEMANDA,
)

bp = Blueprint('profesor', __name__, url_prefix='/profesor')

def admin_required(f):
    """Decorador para verificar que el usuario sea admin o profesor"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Acceso denegado. Debe iniciar sesión.', 'error')
            return redirect(url_for('auth.login'))
        
        # Permitir acceso a profesores/admin y super_admin
        if current_user.tipo_usuario != 'profesor' and not current_user.es_super_admin:
            flash('Acceso denegado. Solo para administradores.', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """Decorador para verificar que el usuario sea super_admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_super_admin:
            flash('Acceso denegado. Solo para super administradores.', 'error')
            return redirect(url_for('profesor.home'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal del profesor"""
    # Obtener la simulación activa
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    if not simulacion:
        # Crear simulación por defecto si no existe ninguna activa
        simulacion = Simulacion(
            nombre='Simulación 1',
            semana_actual=1,
            dia_actual=1,
            estado='pausado',
            activa=True,
            duracion_semanas=DURACION_SIMULACION_SEMANAS,
            capital_inicial_empresas=CAPITAL_INICIAL_EMPRESA_DEFAULT
        )
        db.session.add(simulacion)
        db.session.commit()

        ok, _ = generar_base_demanda_simulacion(simulacion, dias_historico=DIAS_HISTORICO_DEMANDA, replace=True)
        if ok:
            db.session.commit()
    
    # Obtener empresas de la simulación activa
    empresas = Empresa.query.filter_by(simulacion_id=simulacion.id, activa=True).all()
    asegurar_metricas_base_dia_uno(simulacion, commit=True)
    total_estudiantes = Usuario.query.filter(Usuario.rol != 'admin').count()
    
    # Reportar siempre el último día procesado para mantener coherencia operativa.
    dia_reporte = max(1, int(simulacion.dia_actual or 1) - 1)
    ids_empresas = [e.id for e in empresas]
    metricas_dia = Metrica.query.filter(
        Metrica.semana_simulacion == dia_reporte,
        Metrica.empresa_id.in_(ids_empresas)
    ).all()
    
    # Disrupciones de la simulacion activa para panel de seguimiento
    from utils.catalogo_disrupciones import get_disrupcion
    disrupciones_sim = DisrupcionEmpresa.query.filter_by(
        simulacion_id=simulacion.id
    ).order_by(DisrupcionEmpresa.empresa_id, DisrupcionEmpresa.semana_inicio).all()

    return render_template('profesor/dashboard.html',
                         simulacion=simulacion,
                         dia_reporte=dia_reporte,
                         empresas=empresas,
                         total_estudiantes=total_estudiantes,
                         metricas_dia=metricas_dia,
                         disrupciones_sim=disrupciones_sim,
                         capital_inicial_default=CAPITAL_INICIAL_EMPRESA_DEFAULT,
                         inv_750_default=INVENTARIO_INICIAL_750_DEFAULT,
                         inv_1l_default=INVENTARIO_INICIAL_1L_DEFAULT,
                         get_disrupcion=get_disrupcion)


@bp.route('/control-simulacion', methods=['POST'])
@login_required
@admin_required
def control_simulacion():
    """Controlar el avance de la simulación"""
    accion = request.form.get('accion')
    # Obtener la simulación activa
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    if not simulacion:
        flash('No existe una simulación activa', 'error')
        return redirect(url_for('profesor.dashboard'))
    
    if accion == 'iniciar':
        if simulacion.estado == 'pausado':
            simulacion.estado = 'en_curso'
            if not simulacion.fecha_inicio:
                simulacion.fecha_inicio = datetime.utcnow()
            db.session.commit()
            flash('✅ Simulación iniciada. Los estudiantes ahora pueden trabajar.', 'success')
        else:
            flash('La simulación ya está en curso', 'info')
    
    elif accion == 'pausar':
        if simulacion.estado == 'en_curso':
            simulacion.estado = 'pausado'
            db.session.commit()
            flash('⏸️ Simulación pausada. Los estudiantes pueden seguir tomando decisiones.', 'info')
        else:
            flash('La simulación no está en curso', 'warning')
    
    elif accion == 'avanzar_dia':
        if simulacion.estado != 'en_curso':
            flash('⚠️ La simulación debe estar en curso para avanzar. Presiona "Iniciar" primero.', 'warning')
        else:
            # Usar la función de procesamiento automático
            success, mensaje, resumen = avanzar_simulacion()
            
            if success:
                flash(mensaje, 'success')
                
                # Agregar resumen de eventos procesados
                if resumen:
                    flash(f"📊 Procesadas {resumen['total_ventas']} ventas, {resumen['total_compras_recibidas']} compras recibidas, {resumen['total_despachos_entregados']} despachos entregados", 'info')
                    

            else:
                flash(mensaje, 'error')
    
    elif accion == 'finalizar':
        simulacion.estado = 'finalizado'
        simulacion.fecha_fin = datetime.utcnow()
        db.session.commit()
        flash('🏁 Simulación finalizada. Puedes revisar los reportes finales.', 'info')
    
    return redirect(url_for('profesor.dashboard'))


@bp.route('/reiniciar-simulacion', methods=['POST'])
@login_required
@admin_required
def reiniciar_simulacion_endpoint():
    """Reinicia la simulación creando una nueva y manteniendo histórico"""
    try:
        # Obtener parámetros
        capital_inicial = float(request.form.get('capital_inicial', CAPITAL_INICIAL_EMPRESA_DEFAULT))
        nombre_simulacion = request.form.get('nombre_simulacion', None)
        
        # Validar capital
        if capital_inicial < 1000000:
            flash('⚠️ El capital inicial debe ser al menos $1,000,000', 'warning')
            return redirect(url_for('profesor.dashboard'))
        
        # Parámetros de inventario inicial
        inv_750ml = int(request.form.get('inv_750ml', INVENTARIO_INICIAL_750_DEFAULT))
        inv_1l = int(request.form.get('inv_1l', INVENTARIO_INICIAL_1L_DEFAULT))

        # Ejecutar reinicio
        nueva_sim, mensaje = reiniciar_simulacion(
            capital_inicial, nombre_simulacion, inv_750ml, inv_1l
        )
        
        if nueva_sim:
            flash(f'✅ {mensaje}', 'success')
        else:
            flash(f'❌ {mensaje}', 'error')
    
    except Exception as e:
        flash(f'❌ Error al reiniciar: {str(e)}', 'error')
    
    return redirect(url_for('profesor.dashboard'))


@bp.route('/demanda/descargar-csv')
@login_required
@admin_required
def descargar_demanda_csv():
    """Descarga la base central de demanda diaria de la simulación activa."""
    simulacion = Simulacion.query.filter_by(activa=True).first()
    if not simulacion:
        flash('No hay simulación activa para descargar demanda.', 'warning')
        return redirect(url_for('profesor.dashboard'))

    csv_text = exportar_demanda_csv(simulacion.id)
    filename = f"demanda_central_sim_{simulacion.id}.csv"

    return Response(
        csv_text,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        },
    )


@bp.route('/demanda/cargar-csv', methods=['POST'])
@login_required
@admin_required
def cargar_demanda_csv():
    """Carga y valida una base de demanda diaria en CSV para la simulación activa."""
    simulacion = Simulacion.query.filter_by(activa=True).first()
    if not simulacion:
        flash('No hay simulación activa para cargar demanda.', 'warning')
        return redirect(url_for('profesor.dashboard'))

    archivo = request.files.get('archivo_demanda_csv')
    if not archivo or not archivo.filename:
        flash('Debes seleccionar un archivo CSV para cargar.', 'warning')
        return redirect(url_for('profesor.dashboard'))

    if not archivo.filename.lower().endswith('.csv'):
        flash('El archivo debe tener extensión .csv', 'warning')
        return redirect(url_for('profesor.dashboard'))

    try:
        ok, mensaje = importar_demanda_csv(simulacion, archivo, min_historico=30)
        if not ok:
            db.session.rollback()
            flash(f'❌ {mensaje}', 'error')
            return redirect(url_for('profesor.dashboard'))

        db.session.commit()
        flash(f'✅ {mensaje}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error cargando CSV de demanda: {str(e)}', 'error')

    return redirect(url_for('profesor.dashboard'))


@bp.route('/api/historial-simulaciones')
@login_required
@admin_required
def api_historial_simulaciones():
    """API para obtener el historial de todas las simulaciones"""
    try:
        simulaciones = Simulacion.query.order_by(Simulacion.created_at.desc()).all()
        
        simulaciones_data = []
        for sim in simulaciones:
            # Contar empresas de esta simulación
            total_empresas = Empresa.query.filter_by(simulacion_id=sim.id).count()
            
            simulaciones_data.append({
                'id': sim.id,
                'nombre': sim.nombre,
                'semana_actual': sim.semana_actual,
                'dia_actual': sim.dia_actual,
                'estado': sim.estado,
                'activa': sim.activa,
                'fecha_inicio': sim.fecha_inicio.strftime('%Y-%m-%d %H:%M') if sim.fecha_inicio else None,
                'fecha_fin': sim.fecha_fin.strftime('%Y-%m-%d %H:%M') if sim.fecha_fin else None,
                'capital_inicial_empresas': sim.capital_inicial_empresas,
                'total_empresas': total_empresas
            })
        
        return jsonify({
            'success': True,
            'simulaciones': simulaciones_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500



@bp.route('/empresas')
@login_required
@admin_required
def gestionar_empresas():
    """Gestionar empresas participantes"""
    # Filtrar empresas según el tipo de usuario
    if current_user.es_super_admin:
        empresas = Empresa.query.all()
    else:
        empresas = Empresa.query.filter_by(profesor_id=current_user.id).all()
    
    # Calcular estadísticas
    estudiantes_total = sum(len(e.estudiantes) for e in empresas)
    capital_total = sum(e.capital_actual for e in empresas)
    
    # Obtener lista de profesores (solo para super admin)
    profesores = []
    if current_user.es_super_admin:
        profesores = Usuario.query.filter_by(tipo_usuario='profesor', activo=True).all()
    
    return render_template('profesor/empresas.html', 
                         empresas=empresas,
                         estudiantes_total=estudiantes_total,
                         capital_total=capital_total,
                         profesores=profesores)


@bp.route('/empresas/crear', methods=['POST'])
@login_required
@admin_required
def crear_empresa():
    """Crear nueva empresa"""
    try:
        nombre = request.form.get('nombre')
        capital_inicial = float(request.form.get('capital_inicial', 1000000))
        capital_actual = float(request.form.get('capital_actual', capital_inicial))
        activa = request.form.get('activa', '1') == '1'
        
        # Determinar el profesor responsable
        if current_user.es_super_admin and request.form.get('profesor_id'):
            profesor_id = int(request.form.get('profesor_id'))
        else:
            profesor_id = current_user.id
        
        empresa = Empresa(
            nombre=nombre,
            capital_inicial=capital_inicial,
            capital_actual=capital_actual,
            activa=activa,
            profesor_id=profesor_id
        )
        db.session.add(empresa)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Empresa {nombre} creada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@bp.route('/empresas/<int:id>')
@login_required
@admin_required
def obtener_empresa(id):
    """Obtener datos de una empresa específica"""
    empresa = Empresa.query.get_or_404(id)
    
    # Verificar permisos
    if not current_user.es_super_admin and empresa.profesor_id != current_user.id:
        return jsonify({'success': False, 'message': 'No tienes permiso para acceder a esta empresa'}), 403
    
    return jsonify({
        'success': True,
        'empresa': {
            'id': empresa.id,
            'nombre': empresa.nombre,
            'capital_inicial': empresa.capital_inicial,
            'capital_actual': empresa.capital_actual,
            'activa': empresa.activa,
            'profesor_id': empresa.profesor_id
        }
    })


@bp.route('/empresas/<int:id>/editar', methods=['POST'])
@login_required
@admin_required
def editar_empresa(id):
    """Editar una empresa existente"""
    try:
        empresa = Empresa.query.get_or_404(id)
        
        # Verificar permisos
        if not current_user.es_super_admin and empresa.profesor_id != current_user.id:
            return jsonify({'success': False, 'message': 'No tienes permiso para editar esta empresa'}), 403
        
        empresa.nombre = request.form.get('nombre', empresa.nombre)
        empresa.capital_inicial = float(request.form.get('capital_inicial', empresa.capital_inicial))
        empresa.capital_actual = float(request.form.get('capital_actual', empresa.capital_actual))
        empresa.activa = request.form.get('activa', '1') == '1'
        
        # Solo super admin puede cambiar el profesor responsable
        if current_user.es_super_admin and request.form.get('profesor_id'):
            empresa.profesor_id = int(request.form.get('profesor_id'))
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Empresa {empresa.nombre} actualizada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@bp.route('/empresas/<int:id>/toggle-estado', methods=['POST'])
@login_required
@admin_required
def toggle_estado_empresa(id):
    """Activar/Desactivar una empresa"""
    try:
        empresa = Empresa.query.get_or_404(id)
        
        # Verificar permisos
        if not current_user.es_super_admin and empresa.profesor_id != current_user.id:
            return jsonify({'success': False, 'message': 'No tienes permiso para modificar esta empresa'}), 403
        
        empresa.activa = not empresa.activa
        db.session.commit()
        
        estado = 'activada' if empresa.activa else 'desactivada'
        return jsonify({'success': True, 'message': f'Empresa {empresa.nombre} {estado} exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@bp.route('/empresas/<int:id>/eliminar', methods=['POST'])
@login_required
@super_admin_required
def eliminar_empresa(id):
    """Eliminar una empresa (solo super admin)"""
    try:
        empresa = Empresa.query.get_or_404(id)
        nombre = empresa.nombre
        
        # Desvincular estudiantes (permitir reasignación)
        for estudiante in empresa.estudiantes:
            estudiante.empresa_id = None
            estudiante.rol = None
        
        # Eliminar datos relacionados en orden para evitar errores de integridad
        # 1. Movimientos de inventario
        MovimientoInventario.query.filter_by(empresa_id=id).delete()
        
        # 2. Despachos regionales
        DespachoRegional.query.filter_by(empresa_id=id).delete()
        
        # 3. Requerimientos de compra
        RequerimientoCompra.query.filter_by(empresa_id=id).delete()
        
        # 4. Pronósticos
        Pronostico.query.filter_by(empresa_id=id).delete()
        
        # 5. Métricas
        Metrica.query.filter_by(empresa_id=id).delete()
        
        # 6. Decisiones
        Decision.query.filter_by(empresa_id=id).delete()
        
        # 7. Compras
        Compra.query.filter_by(empresa_id=id).delete()
        
        # 8. Ventas
        Venta.query.filter_by(empresa_id=id).delete()
        
        # 9. Inventarios
        Inventario.query.filter_by(empresa_id=id).delete()

        # 10. Disrupciones
        DisrupcionEmpresa.query.filter_by(empresa_id=id).delete()

        # 11. Finalmente eliminar la empresa
        db.session.delete(empresa)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Empresa {nombre} eliminada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@bp.route('/empresas/<int:id>/reportes')
@login_required
@admin_required
def reportes_empresa(id):
    """Ver reportes y análisis de una empresa específica"""
    empresa = Empresa.query.get_or_404(id)
    
    # Verificar permisos
    if not current_user.es_super_admin and empresa.profesor_id != current_user.id:
        flash('No tienes permiso para ver los reportes de esta empresa', 'danger')
        return redirect(url_for('profesor.gestionar_empresas'))
    
    # Obtener estudiantes de la empresa
    estudiantes = empresa.estudiantes
    
    # Obtener todas las decisiones de la empresa
    decisiones = Decision.query.filter_by(empresa_id=id).order_by(Decision.semana_simulacion.desc(), Decision.created_at.desc()).all()
    
    # Obtener métricas por día
    metricas_dias = Metrica.query.filter_by(empresa_id=id).order_by(Metrica.semana_simulacion.asc()).all()
    
    # Calcular estadísticas generales
    total_decisiones = len(decisiones)
    dias_activos = len(set(d.semana_simulacion for d in decisiones)) if decisiones else 0
    
    # Agrupar decisiones por rol
    decisiones_por_rol = {}
    for estudiante in estudiantes:
        if estudiante.rol:
            if estudiante.rol not in decisiones_por_rol:
                decisiones_por_rol[estudiante.rol] = {
                    'estudiantes': [],
                    'total_decisiones': 0,
                    'promedio_dia': 0,
                    'ultimo_dia': 0
                }
            
            decisiones_por_rol[estudiante.rol]['estudiantes'].append(estudiante)
            
            # Contar decisiones de este estudiante
            decisiones_est = [d for d in decisiones if d.usuario_id == estudiante.id]
            decisiones_por_rol[estudiante.rol]['total_decisiones'] += len(decisiones_est)
            
            if decisiones_est:
                ultimo_dia = max(d.semana_simulacion for d in decisiones_est)
                if ultimo_dia > decisiones_por_rol[estudiante.rol]['ultimo_dia']:
                    decisiones_por_rol[estudiante.rol]['ultimo_dia'] = ultimo_dia
    
    # Calcular promedios por día
    for rol_data in decisiones_por_rol.values():
        if rol_data['ultimo_dia'] > 0:
            rol_data['promedio_dia'] = rol_data['total_decisiones'] / rol_data['ultimo_dia']
    
    # Agrupar decisiones por estudiante
    decisiones_estudiantes = {}
    for estudiante in estudiantes:
        decisiones_estudiantes[estudiante.id] = [d for d in decisiones if d.usuario_id == estudiante.id]
    
    # Decisiones para timeline (ordenadas por fecha)
    decisiones_timeline = sorted(decisiones, key=lambda x: (x.semana_simulacion, x.created_at), reverse=True)[:100]

    # --- Datos operativos enriquecidos ---
    # Inventario actual
    inventarios = Inventario.query.filter_by(empresa_id=id).all()

    # Ventas agrupadas por producto
    ventas_todas = Venta.query.filter_by(empresa_id=id).all()
    ventas_por_producto = {}
    for v in ventas_todas:
        pid = v.producto_id
        if pid not in ventas_por_producto:
            ventas_por_producto[pid] = {
                'nombre': v.producto.nombre if v.producto else f'Producto {pid}',
                'unidades_vendidas': 0,
                'unidades_perdidas': 0,
                'ingresos': 0.0,
            }
        ventas_por_producto[pid]['unidades_vendidas'] += v.cantidad_vendida
        ventas_por_producto[pid]['unidades_perdidas'] += v.cantidad_perdida
        ventas_por_producto[pid]['ingresos'] += v.ingreso_total

    # Resumen financiero acumulado
    total_ingresos = sum(m.ingresos for m in metricas_dias)
    total_costos   = sum(m.costos   for m in metricas_dias)
    total_utilidad = sum(m.utilidad for m in metricas_dias)
    # nivel_servicio en Metrica ya es el acumulado hasta esa semana.
    # El valor correcto es el de la ÚLTIMA semana registrada (ya acumula todo el historial).
    nivel_servicio_promedio = metricas_dias[-1].nivel_servicio if metricas_dias else 0

    # Compras activas (en tránsito)
    compras_activas = Compra.query.filter_by(
        empresa_id=id, estado='en_transito'
    ).order_by(Compra.semana_entrega.asc()).all()

    return render_template('profesor/reportes_empresa.html',
                         empresa=empresa,
                         estudiantes=estudiantes,
                         total_decisiones=total_decisiones,
                         dias_activos=dias_activos,
                         decisiones_por_rol=decisiones_por_rol,
                         decisiones_estudiantes=decisiones_estudiantes,
                         decisiones_timeline=decisiones_timeline,
                         metricas_dias=metricas_dias,
                         inventarios=inventarios,
                         ventas_por_producto=ventas_por_producto,
                         total_ingresos=total_ingresos,
                         total_costos=total_costos,
                         total_utilidad=total_utilidad,
                         nivel_servicio_promedio=nivel_servicio_promedio,
                         compras_activas=compras_activas)


@bp.route('/reportes')
@login_required
@admin_required
def ver_reportes():
    """Redirige al listado de empresas para acceder a reportes activos por empresa."""
    flash('Selecciona una empresa para ver su reporte detallado.', 'info')
    return redirect(url_for('profesor.gestionar_empresas'))


@bp.route('/api/metricas/<int:empresa_id>')
@login_required
@admin_required
def api_metricas_empresa(empresa_id):
    """API para obtener métricas de una empresa"""
    metricas = Metrica.query.filter_by(empresa_id=empresa_id).order_by(Metrica.semana_simulacion).all()
    
    datos = []
    for metrica in metricas:
        datos.append({
            'dia': metrica.semana_simulacion,
            'ingresos': metrica.ingresos,
            'costos': metrica.costos,
            'utilidad': metrica.utilidad,
            'nivel_servicio': metrica.nivel_servicio,
            'rotacion_inventario': metrica.rotacion_inventario
        })
    
    return jsonify(datos)


@bp.route('/resumen-simulacion')
@login_required
@admin_required
def resumen_simulacion():
    """Obtiene el resumen actual de la simulación"""
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    if not simulacion:
        return jsonify({
            'success': False,
            'error': 'No existe simulación activa'
        }), 404
    
    resumen = obtener_resumen_simulacion(simulacion)
    
    return jsonify({
        'success': True,
        'resumen': resumen
    })


@bp.route('/estudiantes')
@login_required
@admin_required
def gestionar_estudiantes():
    """Página para gestionar estudiantes"""
    # Obtener filtros
    filtro_estado = request.args.get('estado', 'pendiente')  # pendiente, asignado, todos
    filtro_universidad = request.args.get('universidad', '')
    filtro_sede = request.args.get('sede', '')
    filtro_buscar = request.args.get('buscar', '')
    
    # Query base - solo estudiantes
    query = Usuario.query.filter_by(tipo_usuario='estudiante')
    
    # Filtrar por profesor si no es super admin
    if not current_user.es_super_admin:
        query = query.filter(
            db.or_(
                Usuario.profesor_id == current_user.id,
                Usuario.profesor_id == None  # Estudiantes sin asignar pueden ser asignados por cualquier profesor
            )
        )
    
    # Aplicar filtro de búsqueda (email o nombre)
    if filtro_buscar:
        buscar_term = f'%{filtro_buscar}%'
        query = query.filter(
            db.or_(
                Usuario.email.ilike(buscar_term),
                Usuario.nombre_completo.ilike(buscar_term),
                Usuario.codigo_estudiante.ilike(buscar_term)
            )
        )
    
    # Aplicar filtros de estado
    if filtro_estado == 'pendiente':
        query = query.filter(Usuario.rol == None)
    elif filtro_estado == 'asignado':
        query = query.filter(Usuario.rol != None)
    
    if filtro_universidad:
        query = query.filter_by(universidad=filtro_universidad)
    
    if filtro_sede:
        query = query.filter_by(sede=filtro_sede)
    
    estudiantes = query.order_by(Usuario.created_at.desc()).all()
    
    # Obtener empresas disponibles según privilegios
    if current_user.es_super_admin:
        empresas = Empresa.query.filter_by(activa=True).all()
    else:
        empresas = Empresa.query.filter_by(activa=True, profesor_id=current_user.id).all()
    
    # Roles disponibles para asignar
    roles_disponibles = ['ventas', 'compras', 'logistica']
    
    # Listas para filtros
    universidades = db.session.query(Usuario.universidad).filter(
        Usuario.tipo_usuario=='estudiante',
        Usuario.universidad != None
    ).distinct().all()
    universidades = [u[0] for u in universidades if u[0]]
    
    sedes = db.session.query(Usuario.sede).filter(
        Usuario.tipo_usuario=='estudiante',
        Usuario.sede != None
    ).distinct().all()
    sedes = [s[0] for s in sedes if s[0]]
    
    return render_template('profesor/gestionar_estudiantes.html',
                         estudiantes=estudiantes,
                         empresas=empresas,
                         roles_disponibles=roles_disponibles,
                         universidades=universidades,
                         sedes=sedes,
                         filtro_estado=filtro_estado,
                         filtro_universidad=filtro_universidad,
                         filtro_sede=filtro_sede,
                         filtro_buscar=filtro_buscar)


@bp.route('/estudiantes/<int:id>/asignar', methods=['POST'])
@login_required
@admin_required
def asignar_estudiante(id):
    """Asignar rol y empresa a un estudiante"""
    estudiante = Usuario.query.get_or_404(id)
    
    # Verificar que sea un estudiante
    if estudiante.tipo_usuario != 'estudiante':
        return jsonify({
            'success': False,
            'error': 'Solo se pueden asignar roles a estudiantes'
        }), 400
    
    rol = request.form.get('rol')
    empresa_id = request.form.get('empresa_id')
    
    if not rol or not empresa_id:
        return jsonify({
            'success': False,
            'error': 'Debe especificar rol y empresa'
        }), 400
    
    # Validar rol
    roles_validos = ['ventas', 'compras', 'logistica']
    if rol not in roles_validos:
        return jsonify({
            'success': False,
            'error': 'Rol no válido'
        }), 400
    
    # Validar empresa
    empresa = Empresa.query.get(empresa_id)
    if not empresa or not empresa.activa:
        return jsonify({
            'success': False,
            'error': 'Empresa no válida'
        }), 400
    
    # Verificar que el profesor tenga permisos sobre esta empresa
    if not current_user.es_super_admin and empresa.profesor_id != current_user.id:
        return jsonify({
            'success': False,
            'error': 'No tienes permisos sobre esta empresa'
        }), 403
    
    # Asignar
    estudiante.rol = rol
    estudiante.empresa_id = empresa_id
    estudiante.profesor_id = empresa.profesor_id  # Vincular con el profesor de la empresa
    
    # Generar username si no lo tiene
    if not estudiante.username or estudiante.username.startswith('temp_'):
        estudiante.username = f'estudiante_{empresa.nombre}_{rol}'
    
    db.session.commit()
    
    flash(f'✅ Estudiante {estudiante.nombre_completo or estudiante.username} asignado a {empresa.nombre} como {rol.upper()}', 'success')
    
    return jsonify({
        'success': True,
        'message': f'Estudiante asignado correctamente'
    })


@bp.route('/estudiantes/<int:id>/desasignar', methods=['POST'])
@login_required
@admin_required
def desasignar_estudiante(id):
    """Remover asignación de rol y empresa a un estudiante"""
    estudiante = Usuario.query.get_or_404(id)
    
    if estudiante.tipo_usuario != 'estudiante':
        return jsonify({
            'success': False,
            'error': 'Solo se pueden desasignar estudiantes'
        }), 400
    
    estudiante.rol = None
    estudiante.empresa_id = None
    
    db.session.commit()
    
    flash(f'✅ Estudiante {estudiante.nombre_completo or estudiante.username} desasignado correctamente', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Estudiante desasignado correctamente'
    })


@bp.route('/')
@bp.route('/home')
@login_required
@admin_required
def home():
    """Página de inicio del docente con resumen de empresas"""
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    # Filtrar empresas según si es super admin o profesor regular
    if current_user.es_super_admin:
        # Super admin ve todas las empresas
        empresas = Empresa.query.filter_by(activa=True).all()
    else:
        # Profesor regular solo ve sus empresas
        empresas = Empresa.query.filter_by(activa=True, profesor_id=current_user.id).all()
    
    # Contar estudiantes según privilegios
    if current_user.es_super_admin:
        total_estudiantes = Usuario.query.filter(
            Usuario.tipo_usuario == 'estudiante',
            Usuario.rol != None
        ).count()
        
        estudiantes_pendientes = Usuario.query.filter(
            Usuario.tipo_usuario == 'estudiante',
            Usuario.rol == None
        ).count()
    else:
        # Profesor regular solo ve sus estudiantes
        total_estudiantes = Usuario.query.filter(
            Usuario.profesor_id == current_user.id,
            Usuario.rol != None
        ).count()
        
        estudiantes_pendientes = Usuario.query.filter(
            Usuario.profesor_id == current_user.id,
            Usuario.rol == None
        ).count()
    
    return render_template('profesor/home.html',
                         simulacion=simulacion,
                         empresas=empresas,
                         total_estudiantes=total_estudiantes,
                         estudiantes_pendientes=estudiantes_pendientes)


@bp.route('/api/empresa/<int:empresa_id>/estudiantes')
@login_required
@admin_required
def api_empresa_estudiantes(empresa_id):
    """API para obtener estudiantes de una empresa"""
    empresa = Empresa.query.get_or_404(empresa_id)
    estudiantes = Usuario.query.filter_by(empresa_id=empresa_id).all()
    
    return jsonify({
        'success': True,
        'estudiantes': [{
            'id': est.id,
            'nombre_completo': est.nombre_completo or est.username,
            'email': est.email,
            'rol': est.rol,
            'codigo_estudiante': est.codigo_estudiante
        } for est in estudiantes]
    })


# ============================================================================
# RUTAS PARA GESTIÓN DE PROFESORES (SOLO SUPER ADMIN)
# ============================================================================

@bp.route('/profesores')
@login_required
@super_admin_required
def gestionar_profesores():
    """Página para gestionar profesores - Solo super admin"""
    filtro_buscar = request.args.get('buscar', '')
    filtro_universidad = request.args.get('universidad', '')
    
    # Query base - solo profesores
    query = Usuario.query.filter_by(tipo_usuario='profesor')
    
    # Aplicar filtro de búsqueda
    if filtro_buscar:
        buscar_term = f'%{filtro_buscar}%'
        query = query.filter(
            db.or_(
                Usuario.email.ilike(buscar_term),
                Usuario.nombre_completo.ilike(buscar_term),
                Usuario.codigo_profesor.ilike(buscar_term)
            )
        )
    
    if filtro_universidad:
        query = query.filter_by(universidad=filtro_universidad)
    
    profesores = query.order_by(Usuario.created_at.desc()).all()
    
    # Listas para filtros
    universidades = db.session.query(Usuario.universidad).filter(
        Usuario.tipo_usuario=='profesor',
        Usuario.universidad != None
    ).distinct().all()
    universidades = [u[0] for u in universidades if u[0]]
    
    # Estadísticas
    for profesor in profesores:
        profesor.total_estudiantes = Usuario.query.filter_by(profesor_id=profesor.id).count()
        profesor.total_empresas = Empresa.query.filter_by(profesor_id=profesor.id).count()
    
    return render_template('profesor/gestionar_profesores.html',
                         profesores=profesores,
                         universidades=universidades,
                         filtro_buscar=filtro_buscar,
                         filtro_universidad=filtro_universidad)


@bp.route('/profesores/crear', methods=['POST'])
@login_required
@super_admin_required
def crear_profesor():
    """Crear un nuevo profesor"""
    from werkzeug.security import generate_password_hash
    
    nombre_completo = request.form.get('nombre_completo')
    email = request.form.get('email')
    password = request.form.get('password')
    universidad = request.form.get('universidad')
    codigo_profesor = request.form.get('codigo_profesor')
    
    if not all([nombre_completo, email, password]):
        return jsonify({'success': False, 'error': 'Campos obligatorios incompletos'}), 400
    
    # Verificar si el email ya existe
    if Usuario.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'El email ya está registrado'}), 400
    
    # Generar username desde email
    username = email.split('@')[0]
    base_username = username
    counter = 1
    while Usuario.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1
    
    # Crear nuevo profesor
    nuevo_profesor = Usuario(
        username=username,
        password=generate_password_hash(password),
        nombre_completo=nombre_completo,
        email=email,
        tipo_usuario='profesor',
        rol='admin',  # Los profesores tienen rol admin
        universidad=universidad or 'No especificada',
        codigo_profesor=codigo_profesor,
        es_super_admin=False,
        activo=True
    )
    
    try:
        db.session.add(nuevo_profesor)
        db.session.commit()
        flash(f'✅ Profesor {nombre_completo} creado exitosamente', 'success')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/profesores/<int:id>/toggle-estado', methods=['POST'])
@login_required
@super_admin_required
def toggle_estado_profesor(id):
    """Activar/Desactivar profesor"""
    profesor = Usuario.query.get_or_404(id)
    
    if profesor.tipo_usuario != 'profesor':
        return jsonify({'success': False, 'error': 'Solo se puede modificar el estado de profesores'}), 400
    
    profesor.activo = not profesor.activo
    db.session.commit()
    
    estado = 'activado' if profesor.activo else 'desactivado'
    flash(f'Profesor {profesor.nombre_completo} {estado}', 'success')
    
    return jsonify({'success': True, 'activo': profesor.activo})


@bp.route('/profesores/<int:id>/eliminar', methods=['POST'])
@login_required
@super_admin_required
def eliminar_profesor(id):
    """Eliminar profesor y reasignar sus recursos"""
    profesor = Usuario.query.get_or_404(id)
    
    if profesor.tipo_usuario != 'profesor':
        return jsonify({'success': False, 'error': 'Solo se pueden eliminar profesores'}), 400
    
    # Reasignar estudiantes al super admin
    estudiantes = Usuario.query.filter_by(profesor_id=profesor.id).all()
    for est in estudiantes:
        est.profesor_id = current_user.id
    
    # Reasignar empresas al super admin
    empresas = Empresa.query.filter_by(profesor_id=profesor.id).all()
    for emp in empresas:
        emp.profesor_id = current_user.id
    
    db.session.delete(profesor)
    db.session.commit()
    
    flash(f'Profesor eliminado. {len(estudiantes)} estudiantes y {len(empresas)} empresas reasignados', 'info')
    return jsonify({'success': True})


@bp.route('/api/market-share')
@login_required
@admin_required
def api_market_share():
    """API: Cuota de mercado por empresa (para el administrador/profesor)"""
    simulacion = Simulacion.query.filter_by(activa=True).first()
    if not simulacion:
        return jsonify({'error': 'No hay simulación activa'}), 404

    empresas = Empresa.query.filter_by(simulacion_id=simulacion.id, activa=True).all()
    dia_reporte = max(1, int(simulacion.dia_actual or 1) - 1)
    empresa_ids = [e.id for e in empresas]

    nombres = []
    market_shares = []
    capitales = []
    niveles_servicio = []

    # Snapshot principal: cuota acumulada por ingresos hasta el día de reporte.
    ingresos_acumulados_rows = db.session.query(
        Venta.empresa_id,
        func.sum(Venta.ingreso_total).label('ingresos_total')
    ).filter(
        Venta.empresa_id.in_(empresa_ids),
        Venta.semana_simulacion >= 1,
        Venta.semana_simulacion <= dia_reporte
    ).group_by(Venta.empresa_id).all()

    ingresos_acumulados = {
        int(row.empresa_id): float(row.ingresos_total or 0)
        for row in ingresos_acumulados_rows
    }
    total_ingresos_acumulados = sum(ingresos_acumulados.values())

    for empresa in empresas:
        ingresos_empresa = float(ingresos_acumulados.get(empresa.id, 0))
        share_acumulado = (
            round(ingresos_empresa / total_ingresos_acumulados * 100, 2)
            if total_ingresos_acumulados > 0 else 0.0
        )

        metrica = Metrica.query.filter_by(
            empresa_id=empresa.id,
            semana_simulacion=dia_reporte
        ).first()
        if not metrica:
            metrica = Metrica.query.filter_by(
                empresa_id=empresa.id
            ).order_by(Metrica.semana_simulacion.desc()).first()

        nombres.append(empresa.nombre)
        market_shares.append(share_acumulado)
        capitales.append(round(empresa.capital_actual, 0))
        niveles_servicio.append(round(metrica.nivel_servicio, 1) if metrica else 100.0)

    # Evolución de market share diario: últimos 30 días con ventas reales.
    ultimo_dia = dia_reporte
    primer_dia = max(1, ultimo_dia - 29)
    dias_evolucion = list(range(primer_dia, ultimo_dia + 1))

    ingresos_diarios_rows = db.session.query(
        Venta.semana_simulacion,
        Venta.empresa_id,
        func.sum(Venta.ingreso_total).label('ingresos_total')
    ).filter(
        Venta.empresa_id.in_(empresa_ids),
        Venta.semana_simulacion >= primer_dia,
        Venta.semana_simulacion <= ultimo_dia,
    ).group_by(Venta.semana_simulacion, Venta.empresa_id).all()

    ingresos_por_dia_empresa = {}
    total_por_dia = {}
    for row in ingresos_diarios_rows:
        dia = int(row.semana_simulacion)
        eid = int(row.empresa_id)
        ingreso = float(row.ingresos_total or 0)
        ingresos_por_dia_empresa[(dia, eid)] = ingreso
        total_por_dia[dia] = total_por_dia.get(dia, 0.0) + ingreso

    evolucion = {}
    for empresa in empresas:
        shares_evol = []
        for dia in dias_evolucion:
            total_dia = float(total_por_dia.get(dia, 0.0))
            ingreso_empresa_dia = float(ingresos_por_dia_empresa.get((dia, empresa.id), 0.0))
            if total_dia > 0:
                shares_evol.append(round(ingreso_empresa_dia / total_dia * 100, 2))
            else:
                shares_evol.append(None)
        evolucion[empresa.nombre] = shares_evol

    return jsonify({
        'empresas': nombres,
        'market_share': market_shares,
        'capitales': capitales,
        'niveles_servicio': niveles_servicio,
        'evolucion_dias': dias_evolucion,
        'evolucion': evolucion
    })

