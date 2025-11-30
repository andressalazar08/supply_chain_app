"""
Rutas para el rol Profesor (Administrador)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import Usuario, Empresa, Simulacion, Inventario, Venta, Compra, Decision, Escenario, Metrica, Producto, DisrupcionActiva
from extensions import db
from datetime import datetime
import random
from utils.disrupciones import (
    obtener_disrupciones_disponibles,
    crear_disrupcion_parametros,
    obtener_disrupciones_activas_empresa,
    REGIONES_COLOMBIA
)
from utils.procesamiento_dias import (
    avanzar_simulacion,
    obtener_resumen_simulacion
)

bp = Blueprint('profesor', __name__, url_prefix='/profesor')

def admin_required(f):
    """Decorador para verificar que el usuario sea admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('Acceso denegado. Solo para administradores.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal del profesor"""
    simulacion = Simulacion.query.first()
    if not simulacion:
        # Crear simulación por defecto
        simulacion = Simulacion(dia_actual=1, estado='pausado')
        db.session.add(simulacion)
        db.session.commit()
    
    empresas = Empresa.query.filter_by(activa=True).all()
    total_estudiantes = Usuario.query.filter(Usuario.rol != 'admin').count()
    
    # Obtener métricas del día actual
    metricas_dia = Metrica.query.filter_by(dia_simulacion=simulacion.dia_actual).all()
    
    return render_template('profesor/dashboard.html',
                         simulacion=simulacion,
                         empresas=empresas,
                         total_estudiantes=total_estudiantes,
                         metricas_dia=metricas_dia)


@bp.route('/control-simulacion', methods=['POST'])
@login_required
@admin_required
def control_simulacion():
    """Controlar el avance de la simulación"""
    accion = request.form.get('accion')
    simulacion = Simulacion.query.first()
    
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
                    
                    # Mostrar alertas críticas
                    if resumen['alertas']:
                        for empresa_alertas in resumen['alertas']:
                            alertas_criticas = [a for a in empresa_alertas['alertas'] if a['tipo'] == 'critico']
                            if alertas_criticas:
                                flash(f"⚠️ {empresa_alertas['empresa']}: {len(alertas_criticas)} alertas críticas de inventario", 'warning')
            else:
                flash(mensaje, 'error')
    
    elif accion == 'finalizar':
        simulacion.estado = 'finalizado'
        simulacion.fecha_fin = datetime.utcnow()
        db.session.commit()
        flash('🏁 Simulación finalizada. Puedes revisar los reportes finales.', 'info')
    
    elif accion == 'reiniciar':
        # Confirmación adicional requerida
        confirmacion = request.form.get('confirmacion')
        if confirmacion == 'REINICIAR':
            simulacion.dia_actual = 1
            simulacion.estado = 'pausado'
            simulacion.fecha_inicio = None
            simulacion.fecha_fin = None
            db.session.commit()
            flash('🔄 Simulación reiniciada al día 1. Todos los datos históricos se mantienen.', 'warning')
        else:
            flash('⚠️ Para reiniciar, debes confirmar escribiendo "REINICIAR"', 'warning')
    
    return redirect(url_for('profesor.dashboard'))


@bp.route('/empresas')
@login_required
@admin_required
def gestionar_empresas():
    """Gestionar empresas participantes"""
    empresas = Empresa.query.all()
    return render_template('profesor/empresas.html', empresas=empresas)


@bp.route('/empresas/crear', methods=['POST'])
@login_required
@admin_required
def crear_empresa():
    """Crear nueva empresa"""
    nombre = request.form.get('nombre')
    capital_inicial = float(request.form.get('capital_inicial', 1000000))
    
    empresa = Empresa(
        nombre=nombre,
        capital_inicial=capital_inicial,
        capital_actual=capital_inicial
    )
    db.session.add(empresa)
    db.session.commit()
    
    flash(f'Empresa {nombre} creada exitosamente', 'success')
    return redirect(url_for('profesor.gestionar_empresas'))


@bp.route('/estudiantes')
@login_required
@admin_required
def gestionar_estudiantes():
    """Gestionar estudiantes"""
    estudiantes = Usuario.query.filter(Usuario.rol != 'admin').all()
    empresas = Empresa.query.all()
    return render_template('profesor/estudiantes.html', 
                         estudiantes=estudiantes,
                         empresas=empresas)


@bp.route('/estudiantes/crear', methods=['POST'])
@login_required
@admin_required
def crear_estudiante():
    """Crear nuevo estudiante"""
    from werkzeug.security import generate_password_hash
    
    rol = request.form.get('rol')
    empresa_id = int(request.form.get('empresa_id'))
    nombre_completo = request.form.get('nombre_completo')
    email = request.form.get('email')
    
    # Generar username automático: estudiante_rol_empresa
    roles_num = {
        'ventas': '1',
        'planeacion': '2',
        'compras': '3',
        'logistica': '4'
    }
    username = f"estudiante_{roles_num[rol]}_{empresa_id}"
    
    # Verificar si ya existe
    if Usuario.query.filter_by(username=username).first():
        flash(f'Ya existe un estudiante con rol {rol} en la empresa {empresa_id}', 'error')
        return redirect(url_for('profesor.gestionar_estudiantes'))
    
    # Contraseña por defecto (puede cambiarse después)
    password = generate_password_hash('estudiante123')
    
    estudiante = Usuario(
        username=username,
        password=password,
        rol=rol,
        empresa_id=empresa_id,
        nombre_completo=nombre_completo,
        email=email
    )
    
    db.session.add(estudiante)
    db.session.commit()
    
    flash(f'Estudiante {username} creado exitosamente', 'success')
    return redirect(url_for('profesor.gestionar_estudiantes'))


@bp.route('/escenarios/activar/<int:escenario_id>', methods=['POST'])
@login_required
@admin_required
def activar_escenario(escenario_id):
    """Activar o desactivar un escenario (DEPRECATED - usa nueva API)"""
    return redirect(url_for('profesor.gestion_escenarios'))


@bp.route('/reportes')
@login_required
@admin_required
def ver_reportes():
    """Ver reportes y análisis de desempeño"""
    simulacion = Simulacion.query.first()
    empresas = Empresa.query.all()
    
    # Obtener métricas de todas las empresas
    metricas_empresas = []
    for empresa in empresas:
        metricas = Metrica.query.filter_by(
            empresa_id=empresa.id,
            dia_simulacion=simulacion.dia_actual
        ).first()
        
        metricas_empresas.append({
            'empresa': empresa,
            'metricas': metricas
        })
    
    return render_template('profesor/reportes.html',
                         simulacion=simulacion,
                         metricas_empresas=metricas_empresas)


@bp.route('/api/metricas/<int:empresa_id>')
@login_required
@admin_required
def api_metricas_empresa(empresa_id):
    """API para obtener métricas de una empresa"""
    metricas = Metrica.query.filter_by(empresa_id=empresa_id).order_by(Metrica.dia_simulacion).all()
    
    datos = []
    for metrica in metricas:
        datos.append({
            'dia': metrica.dia_simulacion,
            'ingresos': metrica.ingresos,
            'costos': metrica.costos,
            'utilidad': metrica.utilidad,
            'nivel_servicio': metrica.nivel_servicio,
            'rotacion_inventario': metrica.rotacion_inventario
        })
    
    return jsonify(datos)


def procesar_dia(dia_actual):
    """
    Procesa todos los eventos del día:
    - Genera demanda
    - Procesa ventas
    - Actualiza inventarios
    - Recibe órdenes de compra
    - Calcula métricas
    """
    empresas = Empresa.query.filter_by(activa=True).all()
    productos = Producto.query.filter_by(activo=True).all()
    
    # Regiones de Colombia
    regiones = ['Caribe', 'Pacifica', 'Orinoquia', 'Amazonia', 'Andina']
    canales = ['retail', 'mayorista', 'distribuidor']
    
    # Factores de demanda por región (población relativa)
    factor_regional = {
        'Caribe': 0.9,
        'Pacifica': 0.85,
        'Orinoquia': 0.7,
        'Amazonia': 0.6,
        'Andina': 1.2  # Región más poblada
    }
    
    for empresa in empresas:
        for producto in productos:
            # Generar ventas en múltiples regiones
            num_regiones = random.randint(2, 4)  # Vende en 2-4 regiones por día
            regiones_activas = random.sample(regiones, num_regiones)
            
            for region in regiones_activas:
                # Generar demanda regional con factor de ajuste
                demanda_base = producto.demanda_promedio * factor_regional[region]
                
                # Aplicar elasticidad del precio
                factor_precio = 1.0
                if hasattr(producto, 'precio_actual') and hasattr(producto, 'precio_base'):
                    variacion_precio = (producto.precio_actual - producto.precio_base) / producto.precio_base
                    factor_precio = 1 - (variacion_precio * producto.elasticidad_precio)
                
                demanda_ajustada = demanda_base * factor_precio
                demanda = max(1, int(random.gauss(demanda_ajustada, producto.desviacion_demanda)))
                
                # Verificar inventario
                inventario = Inventario.query.filter_by(
                    empresa_id=empresa.id,
                    producto_id=producto.id
                ).first()
                
                if inventario:
                    cantidad_vendida = min(demanda, inventario.cantidad_actual)
                    cantidad_perdida = demanda - cantidad_vendida
                    
                    # Precio con pequeña variación por canal
                    precio_base = producto.precio_actual if hasattr(producto, 'precio_actual') else producto.precio_base
                    canal = random.choice(canales)
                    factor_canal = {'retail': 1.0, 'mayorista': 0.9, 'distribuidor': 0.85}
                    precio_unitario = precio_base * factor_canal[canal]
                    
                    ingreso_total = cantidad_vendida * precio_unitario
                    margen = ((precio_unitario - producto.costo_unitario) / precio_unitario * 100) if precio_unitario > 0 else 0
                    
                    # Registrar venta
                    venta = Venta(
                        empresa_id=empresa.id,
                        producto_id=producto.id,
                        dia_simulacion=dia_actual,
                        region=region,
                        canal=canal,
                        cantidad_solicitada=demanda,
                        cantidad_vendida=cantidad_vendida,
                        cantidad_perdida=cantidad_perdida,
                        precio_unitario=precio_unitario,
                        ingreso_total=ingreso_total,
                        costo_unitario=producto.costo_unitario,
                        margen=margen
                    )
                    db.session.add(venta)
                    
                    # Actualizar inventario
                    inventario.cantidad_actual -= cantidad_vendida
        
        # Procesar órdenes de compra que llegan este día
        compras_pendientes = Compra.query.filter_by(
            empresa_id=empresa.id,
            dia_entrega=dia_actual,
            estado='en_transito'
        ).all()
        
        for compra in compras_pendientes:
            inventario = Inventario.query.filter_by(
                empresa_id=empresa.id,
                producto_id=compra.producto_id
            ).first()
            
            if inventario:
                inventario.cantidad_actual += compra.cantidad
            
            compra.estado = 'entregado'
    
    db.session.commit()
    
    # Calcular métricas del día
    calcular_metricas(dia_actual)


def calcular_metricas(dia_actual):
    """Calcula las métricas de desempeño para todas las empresas"""
    empresas = Empresa.query.filter_by(activa=True).all()
    
    for empresa in empresas:
        # Calcular ingresos del día
        ventas_dia = Venta.query.filter_by(
            empresa_id=empresa.id,
            dia_simulacion=dia_actual
        ).all()
        
        ingresos = sum([v.ingreso_total for v in ventas_dia])
        
        # Calcular costos del día
        compras_dia = Compra.query.filter_by(
            empresa_id=empresa.id,
            dia_orden=dia_actual
        ).all()
        
        costos = sum([c.costo_total for c in compras_dia])
        
        # Calcular nivel de servicio
        total_solicitado = sum([v.cantidad_solicitada for v in ventas_dia])
        total_vendido = sum([v.cantidad_vendida for v in ventas_dia])
        nivel_servicio = (total_vendido / total_solicitado * 100) if total_solicitado > 0 else 100
        
        # Crear registro de métrica
        metrica = Metrica(
            empresa_id=empresa.id,
            dia_simulacion=dia_actual,
            ingresos=ingresos,
            costos=costos,
            utilidad=ingresos - costos,
            nivel_servicio=nivel_servicio
        )
        
        db.session.add(metrica)
    
    db.session.commit()


@bp.route('/escenarios')
@login_required
@admin_required
def gestion_escenarios():
    """Panel de gestión de disrupciones y escenarios"""
    simulacion = Simulacion.query.first()
    
    # Obtener disrupciones activas
    disrupciones_activas = DisrupcionActiva.query.filter_by(
        simulacion_id=simulacion.id,
        activo=True
    ).filter(
        DisrupcionActiva.dia_fin >= simulacion.dia_actual
    ).order_by(DisrupcionActiva.dia_inicio.desc()).all()
    
    # Obtener histórico de disrupciones
    disrupciones_historico = DisrupcionActiva.query.filter_by(
        simulacion_id=simulacion.id
    ).filter(
        DisrupcionActiva.dia_fin < simulacion.dia_actual
    ).order_by(DisrupcionActiva.created_at.desc()).limit(20).all()
    
    # Obtener catálogo de disrupciones disponibles
    catalogo = obtener_disrupciones_disponibles()
    
    # Obtener productos y empresas para los filtros
    productos = Producto.query.all()
    empresas = Empresa.query.filter_by(activa=True).all()
    
    return render_template('profesor/escenarios.html',
                         simulacion=simulacion,
                         disrupciones_activas=disrupciones_activas,
                         disrupciones_historico=disrupciones_historico,
                         catalogo=catalogo,
                         productos=productos,
                         empresas=empresas,
                         regiones=REGIONES_COLOMBIA)


@bp.route('/escenarios/activar', methods=['POST'])
@login_required
@admin_required
def activar_disrupcion():
    """Activa una nueva disrupción en la simulación"""
    simulacion = Simulacion.query.first()
    
    tipo_disrupcion = request.form.get('tipo_disrupcion')
    severidad = request.form.get('severidad')
    nombre_custom = request.form.get('nombre_custom')
    razon_custom = request.form.get('razon_custom')
    duracion_dias = int(request.form.get('duracion_dias', 7))
    visible = request.form.get('visible_estudiantes') == 'on'
    
    # Productos afectados (opcional)
    productos_ids = request.form.getlist('productos[]')
    productos_ids = [int(p) for p in productos_ids if p]
    
    # Regiones afectadas (opcional)
    regiones = request.form.getlist('regiones[]')
    
    # Empresas afectadas (opcional - null = todas)
    empresas_ids = request.form.getlist('empresas[]')
    empresas_ids = [int(e) for e in empresas_ids if e] if empresas_ids else None
    
    try:
        # Crear parámetros de la disrupción
        config = crear_disrupcion_parametros(
            tipo_disrupcion=tipo_disrupcion,
            severidad=severidad,
            productos=productos_ids if productos_ids else None,
            regiones=regiones if regiones else None,
            razon=razon_custom
        )
        
        # Crear la disrupción
        disrupcion = DisrupcionActiva(
            simulacion_id=simulacion.id,
            profesor_id=current_user.id,
            nombre=nombre_custom if nombre_custom else config['nombre'],
            tipo_disrupcion=tipo_disrupcion,
            descripcion=config['descripcion'],
            icono=config['icono'],
            dia_inicio=simulacion.dia_actual,
            dia_fin=simulacion.dia_actual + duracion_dias,
            activo=True,
            parametros=config['parametros'],
            severidad=severidad,
            visible_estudiantes=visible,
            empresas_afectadas=empresas_ids
        )
        
        db.session.add(disrupcion)
        db.session.commit()
        
        flash(f'✅ Disrupción "{disrupcion.nombre}" activada exitosamente desde el día {simulacion.dia_actual} hasta el día {disrupcion.dia_fin}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al activar disrupción: {str(e)}', 'error')
    
    return redirect(url_for('profesor.gestion_escenarios'))


@bp.route('/escenarios/desactivar/<int:disrupcion_id>', methods=['POST'])
@login_required
@admin_required
def desactivar_disrupcion(disrupcion_id):
    """Desactiva una disrupción activa"""
    disrupcion = DisrupcionActiva.query.get_or_404(disrupcion_id)
    
    disrupcion.activo = False
    disrupcion.dia_fin = Simulacion.query.first().dia_actual - 1
    
    db.session.commit()
    
    flash(f'🔴 Disrupción "{disrupcion.nombre}" desactivada', 'info')
    return redirect(url_for('profesor.gestion_escenarios'))


@bp.route('/escenarios/eliminar/<int:disrupcion_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_disrupcion(disrupcion_id):
    """Elimina una disrupción del histórico"""
    disrupcion = DisrupcionActiva.query.get_or_404(disrupcion_id)
    
    db.session.delete(disrupcion)
    db.session.commit()
    
    flash(f'🗑️ Disrupción "{disrupcion.nombre}" eliminada del histórico', 'info')
    return redirect(url_for('profesor.gestion_escenarios'))


@bp.route('/escenarios/plantilla/<tipo>/<severidad>')
@login_required
@admin_required
def obtener_plantilla_disrupcion(tipo, severidad):
    """API para obtener la plantilla de una disrupción"""
    try:
        config = crear_disrupcion_parametros(tipo, severidad)
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@bp.route('/resumen-simulacion')
@login_required
@admin_required
def resumen_simulacion():
    """Obtiene el resumen actual de la simulación"""
    simulacion = Simulacion.query.first()
    
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
