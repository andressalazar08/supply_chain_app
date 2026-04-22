"""
Rutas para el rol Estudiante
Dashboard diferenciado seg�n rol: Ventas, Planeaci�n, Compras, Log�stica
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from functools import wraps
import csv
import io
from types import SimpleNamespace
from sqlalchemy import func
from models import (Usuario, Empresa, Simulacion, Inventario, Venta, Compra, Decision,
                    Producto, Pronostico, RequerimientoCompra, MovimientoInventario, DespachoRegional,
                    DisrupcionEmpresa, DemandaMercadoDiaria, DisponibilidadVehiculo)
from extensions import db
from datetime import datetime
from utils.pronosticos import (
    promedio_movil, suavizacion_exponencial_simple, suavizacion_exponencial_doble_holt,
    comparar_metodos, obtener_mejor_metodo, calcular_cantidad_pedir
)
from utils.inventario import (
    calcular_consumo_diario, calcular_dias_cobertura,
    calcular_costo_total_compra, validar_capacidad_compra
)
from utils.logistica import (
    calcular_tiempo_entrega_region, procesar_recepcion_compra, validar_despacho_region,
    distribuir_stock_por_demanda, analizar_cobertura_regional, generar_alertas_logistica,
    sugerir_redistribucion, calcular_stock_disponible_despacho,
    obtener_ciclo_region, seleccionar_vehiculos_optimos
)
from utils.parametros_iniciales import FLOTA_VEHICULOS
bp = Blueprint('estudiante', __name__, url_prefix='/estudiante')

# Tarifa base de transporte por unidad según región (flota propia).
TARIFA_TRANSPORTE_POR_REGION = {
    'Andina': 500,
    'Pacífica': 1000,
    'Caribe': 1000,
    'Orinoquía': 1500,
    'Amazonía': 2000,
}


def _tarifa_transporte_region(region):
    """Retorna la tarifa base por unidad para la región dada."""
    return float(TARIFA_TRANSPORTE_POR_REGION.get(region, 1000))
ROL_PLANEACION_COMPRAS = 'compras'

REGIONES_CANONICAS = [
    'Andina',
    'Caribe',
    'Pac\u00edfica',
    'Orinoqu\u00eda',
    'Amazon\u00eda',
]

REGION_VARIANTES = {
    'Andina': ['Andina'],
    'Caribe': ['Caribe'],
    'Pac\u00edfica': ['Pac\u00edfica', 'Pacifica', 'Pac�fica'],
    'Orinoqu\u00eda': ['Orinoqu\u00eda', 'Orinoquia', 'Orinoqu�a'],
    'Amazon\u00eda': ['Amazon\u00eda', 'Amazonia', 'Amazon�a'],
}


def variantes_region(region):
    """Retorna alias válidos de una región para tolerar datos legados mal codificados."""
    return REGION_VARIANTES.get(region, [region])


def _role_set_for_user(user_role):
    """Mapea roles legados a su conjunto funcional equivalente."""
    if user_role in ['planeacion', 'compras', ROL_PLANEACION_COMPRAS]:
        return {'planeacion', 'compras', ROL_PLANEACION_COMPRAS}
    return {user_role}


def _role_allowed(user_role, allowed_roles):
    return bool(_role_set_for_user(user_role).intersection(set(allowed_roles)))


LEAD_TIME_BASE_REFERENCIA_ESPECIAL = 2
LEAD_TIME_BASE_RESTO = 3
LEAD_TIME_DISRUPCION_ACTUAL_REFERENCIA_ESPECIAL = 4
LEAD_TIME_DISRUPCION_ACTUAL_RESTO = 6
LEAD_TIME_DISRUPCION_EXTERNO_REFERENCIA_ESPECIAL = 2
LEAD_TIME_DISRUPCION_EXTERNO_RESTO = 3
COSTO_EXTRA_PROVEEDOR_EXTERNO = 5000

PROVEEDORES_COMPRA = {
    'ACTUAL': {
        'nombre': 'Proveedor actual',
    },
    'EXTERNO': {
        'nombre': 'Proveedor externo',
    },
}

VEHICULOS_LOGISTICA = {
    codigo: {
        'nombre': f'Vehículo {codigo}',
        'capacidad': conf.get('capacidad'),
        'externo': bool(conf.get('por_unidad', False)),
    }
    for codigo, conf in FLOTA_VEHICULOS.items()
    if codigo != 'V_EXTERNO'
}
VEHICULOS_LOGISTICA['EXTERNO'] = {
    'nombre': 'Vehículo externo',
    'capacidad': None,
    'externo': True,
}


def _disrupcion_falla_flota_activa(simulacion, empresa_id):
    if not simulacion:
        return False

    return DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.empresa_id == empresa_id,
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.disrupcion_key == 'falla_flota',
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.opcion_elegida != None,
    ).first() is not None


def _opcion_falla_flota(simulacion, empresa_id):
    if not simulacion:
        return None

    dis = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.empresa_id == empresa_id,
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.disrupcion_key == 'falla_flota',
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.opcion_elegida != None,
    ).first()
    return dis.opcion_elegida if dis else None


def _obtener_capacidades_vehiculos(simulacion, empresa_id):
    """Retorna el catálogo de vehículos con disponibilidad según disrupciones activas."""
    catalogo = {}
    for codigo, conf in VEHICULOS_LOGISTICA.items():
        catalogo[codigo] = {
            'codigo': codigo,
            'nombre': conf['nombre'],
            'capacidad': conf['capacidad'],
            'externo': conf['externo'],
            'disponible': True,
            'dia_retorno': None,
        }

    # Marcar vehículos ocupados por ciclo de uso.
    if simulacion:
        ocupados = db.session.query(
            DisponibilidadVehiculo.vehiculo_id,
            db.func.max(DisponibilidadVehiculo.dia_disponible_retorno).label('dia_retorno')
        ).filter(
            DisponibilidadVehiculo.empresa_id == empresa_id,
            DisponibilidadVehiculo.dia_disponible_retorno >= simulacion.dia_actual,
        ).group_by(
            DisponibilidadVehiculo.vehiculo_id
        ).all()
        for vehiculo_id, dia_retorno in ocupados:
            if vehiculo_id in catalogo:
                catalogo[vehiculo_id]['disponible'] = False
                catalogo[vehiculo_id]['dia_retorno'] = int(dia_retorno)

    if _disrupcion_falla_flota_activa(simulacion, empresa_id):
        for codigo, conf in catalogo.items():
            if not conf['externo'] and conf['capacidad'] == 500:
                catalogo[codigo]['disponible'] = False
                catalogo[codigo]['dia_retorno'] = None

    return catalogo


def _codigos_propios_disponibles(simulacion, empresa_id):
    catalogo = _obtener_capacidades_vehiculos(simulacion, empresa_id)
    return [
        codigo for codigo, conf in catalogo.items()
        if conf['disponible'] and not conf['externo'] and conf['capacidad']
    ]


def _serializar_vehiculos(catalogo):
    return [
        {
            'codigo': v['codigo'],
            'nombre': v['nombre'],
            'capacidad': v['capacidad'],
            'externo': v['externo'],
            'disponible': v['disponible'],
            'dia_retorno': v.get('dia_retorno'),
        }
        for v in catalogo.values()
    ]


def _pedido_minimo_externo(producto):
    """Pedido mínimo por referencia solo para proveedor externo durante disrupción."""
    codigo = (producto.codigo or '').upper()
    nombre = (producto.nombre or '').upper()

    if '750' in codigo or '750' in nombre:
        return 60
    if '1L' in codigo or ' 1L' in nombre or '1 L' in nombre:
        return 50
    return 0


def _disrupcion_retraso_proveedor_activa(simulacion, empresa_id):
    """Indica si la disrupción de retraso de proveedor está activa para la empresa."""
    if not simulacion:
        return False

    return DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.empresa_id == empresa_id,
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.disrupcion_key == 'retraso_proveedor',
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.opcion_elegida != None,
    ).first() is not None


def _opcion_retraso_proveedor(simulacion, empresa_id):
    if not simulacion:
        return None

    dis = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.empresa_id == empresa_id,
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.disrupcion_key == 'retraso_proveedor',
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.opcion_elegida != None,
    ).first()
    return dis.opcion_elegida if dis else None


def _normalizar_proveedor(valor):
    proveedor = (valor or 'ACTUAL').strip().upper()
    return proveedor if proveedor in PROVEEDORES_COMPRA else 'ACTUAL'


def _es_referencia_especial(producto):
    nombre = (producto.nombre or '').upper()
    return 'SANGRE DE LA VID' in nombre or 'SUSURRO ROSADO' in nombre


def _calcular_lead_time_compra(producto, proveedor, dis_retraso_activa):
    es_especial = _es_referencia_especial(producto)

    if not dis_retraso_activa:
        return LEAD_TIME_BASE_REFERENCIA_ESPECIAL if es_especial else LEAD_TIME_BASE_RESTO

    if proveedor == 'ACTUAL':
        return (
            LEAD_TIME_DISRUPCION_ACTUAL_REFERENCIA_ESPECIAL
            if es_especial
            else LEAD_TIME_DISRUPCION_ACTUAL_RESTO
        )

    return (
        LEAD_TIME_DISRUPCION_EXTERNO_REFERENCIA_ESPECIAL
        if es_especial
        else LEAD_TIME_DISRUPCION_EXTERNO_RESTO
    )


def _validar_multiplos_pedido(producto, cantidad):
    """
    Valida que la cantidad sea múltiplo correcto según tamaño del producto.
    750mL: múltiplos de 30
    1L: múltiplos de 20
    Retorna: (es_valido, mensaje)
    """
    cantidad_int = int(cantidad) if cantidad == int(cantidad) else cantidad
    
    if '750' in producto.codigo:
        if cantidad_int % 30 != 0:
            return False, f"Productos de 750mL deben pedirse en múltiplos de 30 (ingresaste {cantidad_int})"
    elif '1L' in producto.codigo or 'L' in producto.codigo.upper():
        if cantidad_int % 20 != 0:
            return False, f"Productos de 1L deben pedirse en múltiplos de 20 (ingresaste {cantidad_int})"
    
    return True, ""


def _calcular_condiciones_compra(producto, cantidad, simulacion, empresa_id, proveedor):
    """Calcula costo/lead time según reglas operativas de Compras y disrupciones."""
    proveedor = _normalizar_proveedor(proveedor)

    # Validar múltiplos para ambos proveedores: 30 para 750mL, 20 para 1L
    multiplo_valido, mensaje_multiplo = _validar_multiplos_pedido(producto, cantidad)
    if not multiplo_valido:
        return {
            'ok': False,
            'mensaje': f'{mensaje_multiplo} ({proveedor})'
        }

    dis_retraso_activa = _disrupcion_retraso_proveedor_activa(simulacion, empresa_id)
    opcion_retraso = _opcion_retraso_proveedor(simulacion, empresa_id)

    # Sin disrupción: opera solo proveedor actual.
    if not dis_retraso_activa:
        proveedor = 'ACTUAL'
    elif opcion_retraso == 'B':
        proveedor = 'ACTUAL'

    config = PROVEEDORES_COMPRA[proveedor]

    costo_unitario = float(producto.costo_unitario)
    tiempo_entrega = _calcular_lead_time_compra(producto, proveedor, dis_retraso_activa)

    # Disrupción activa de retraso de proveedor estratégico.
    if dis_retraso_activa:
        if proveedor == 'ACTUAL':
            if simulacion.dia_actual % 2 != 0:
                return {
                    'ok': False,
                    'mensaje': 'Con disrupción activa, el proveedor actual solo recibe pedidos en días pares.'
                }
        elif proveedor == 'EXTERNO':
            costo_unitario += COSTO_EXTRA_PROVEEDOR_EXTERNO

    delay_extra = 0

    return {
        'ok': True,
        'disrupcion_retraso_activa': dis_retraso_activa,
        'proveedor': proveedor,
        'proveedor_nombre': config['nombre'],
        'costo_unitario': costo_unitario,
        'tiempo_entrega': tiempo_entrega,
        'delay_extra': delay_extra,
    }

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


def rol_required(*roles):
    """Decorador para restringir acceso a roles específicos"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not _role_allowed(current_user.rol, roles):
                flash('No tienes permiso para acceder a este módulo.', 'error')
                return redirect(url_for('estudiante.dashboard_general'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


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

    from utils.procesamiento_dias import asegurar_metricas_base_dia_uno
    asegurar_metricas_base_dia_uno(simulacion, commit=True)
    
    # Obtener datos generales
    productos = Producto.query.filter_by(activo=True).all()
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    
    # Ventas del d�a actual
    ventas_dia = Venta.query.filter_by(
        empresa_id=empresa.id,
        semana_simulacion=simulacion.dia_actual
    ).all()
    
    # M�trica del d�a
    from models import Metrica
    metrica_hoy = Metrica.query.filter_by(
        empresa_id=empresa.id,
        semana_simulacion=simulacion.dia_actual
    ).first()
    if not metrica_hoy:
        metrica_hoy = Metrica.query.filter(
            Metrica.empresa_id == empresa.id,
            Metrica.semana_simulacion <= simulacion.dia_actual
        ).order_by(Metrica.semana_simulacion.desc()).first()
    if not metrica_hoy:
        metrica_hoy = SimpleNamespace(
            ingresos=0,
            costos=0,
            utilidad=0,
            nivel_servicio=100.0,
            rotacion_inventario=0,
            market_share=0,
        )

    metricas_acumuladas = Metrica.query.filter(
        Metrica.empresa_id == empresa.id,
        Metrica.semana_simulacion >= 1,
        Metrica.semana_simulacion <= simulacion.dia_actual,
    ).all()
    ingresos_acumulados = sum(m.ingresos or 0 for m in metricas_acumuladas)
    costos_acumulados = sum(m.costos or 0 for m in metricas_acumuladas)
    utilidad_acumulada = sum(m.utilidad or 0 for m in metricas_acumuladas)
    
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
        Compra.semana_entrega <= simulacion.dia_actual + 21
    ).order_by(Compra.semana_entrega).limit(5).all()

    # Histórico operativo desde el día 1 (sin mezclar histórico negativo).
    dia_actual = int(simulacion.dia_actual or 1)
    dias_periodo = list(range(1, dia_actual + 1))

    demanda_rows = db.session.query(
        DemandaMercadoDiaria.dia_simulacion,
        DemandaMercadoDiaria.producto_id,
        func.sum(DemandaMercadoDiaria.demanda_base).label('demanda_total')
    ).filter(
        DemandaMercadoDiaria.simulacion_id == simulacion.id,
        DemandaMercadoDiaria.dia_simulacion >= 1,
        DemandaMercadoDiaria.dia_simulacion <= dia_actual,
    ).group_by(
        DemandaMercadoDiaria.dia_simulacion,
        DemandaMercadoDiaria.producto_id,
    ).all()

    ventas_rows = db.session.query(
        Venta.semana_simulacion,
        Venta.producto_id,
        func.sum(Venta.cantidad_solicitada).label('pedidos_total'),
        func.sum(Venta.cantidad_vendida).label('vendidas_total'),
        func.sum(Venta.cantidad_perdida).label('perdidas_total'),
        func.sum(Venta.ingreso_total).label('ingresos_total')
    ).filter(
        Venta.empresa_id == empresa.id,
        Venta.semana_simulacion >= 1,
        Venta.semana_simulacion <= dia_actual,
    ).group_by(
        Venta.semana_simulacion,
        Venta.producto_id,
    ).all()

    demanda_por_dia = {d: 0 for d in dias_periodo}
    pedidos_por_dia = {d: 0 for d in dias_periodo}
    vendidas_por_dia = {d: 0 for d in dias_periodo}
    perdidas_por_dia = {d: 0 for d in dias_periodo}
    ingresos_por_dia = {d: 0 for d in dias_periodo}

    demanda_por_dia_producto = {}
    for row in demanda_rows:
        d = int(row.dia_simulacion)
        p = int(row.producto_id)
        demanda_valor = int(round(row.demanda_total or 0))
        demanda_por_dia_producto[(d, p)] = demanda_valor
        if d in demanda_por_dia:
            demanda_por_dia[d] += demanda_valor

    ventas_por_dia_producto = {}
    for row in ventas_rows:
        d = int(row.semana_simulacion)
        p = int(row.producto_id)
        pedidos_valor = int(round(row.pedidos_total or 0))
        vendidas_valor = int(round(row.vendidas_total or 0))
        perdidas_valor = int(round(row.perdidas_total or 0))
        ingresos_valor = float(row.ingresos_total or 0)
        ventas_por_dia_producto[(d, p)] = {
            'pedidos_demandados': pedidos_valor,
            'unidades_vendidas': vendidas_valor,
            'unidades_perdidas': perdidas_valor,
            'ingresos': ingresos_valor,
        }
        if d in pedidos_por_dia:
            pedidos_por_dia[d] += pedidos_valor
            vendidas_por_dia[d] += vendidas_valor
            perdidas_por_dia[d] += perdidas_valor
            ingresos_por_dia[d] += ingresos_valor

    historico_operacion = []
    producto_nombre_map = {p.id: p.nombre for p in productos}
    producto_ids_ordenados = sorted(producto_nombre_map.keys(), key=lambda pid: producto_nombre_map[pid])
    for d in reversed(dias_periodo):
        for pid in producto_ids_ordenados:
            demanda_base = demanda_por_dia_producto.get((d, pid), 0)
            venta_item = ventas_por_dia_producto.get((d, pid), {})
            pedidos_demandados = int(venta_item.get('pedidos_demandados', 0))
            unidades_vendidas = int(venta_item.get('unidades_vendidas', 0))
            unidades_perdidas = int(venta_item.get('unidades_perdidas', 0))
            ingresos = float(venta_item.get('ingresos', 0))

            if demanda_base <= 0 and pedidos_demandados <= 0 and unidades_vendidas <= 0 and unidades_perdidas <= 0 and ingresos <= 0:
                continue

            historico_operacion.append({
                'dia': d,
                'producto': producto_nombre_map.get(pid, f'Producto {pid}'),
                'demanda_base': demanda_base,
                'pedidos_demandados': pedidos_demandados,
                'unidades_vendidas': unidades_vendidas,
                'unidades_perdidas': unidades_perdidas,
                'ingresos': ingresos,
            })

    total_ventas_periodo = sum(vendidas_por_dia.values())
    ingresos_periodo = sum(ingresos_por_dia.values())
    promedio_diario_periodo = (total_ventas_periodo / len(dias_periodo)) if dias_periodo else 0

    # --- DISRUPCIONES ---
    # Garantizar que esta empresa tenga sus disrupciones creadas y expiradas
    # correctamente incluso si el estudiante entra sin que el motor haya corrido.
    from utils.procesamiento_dias import verificar_y_activar_disrupciones, verificar_y_expirar_disrupciones
    expiradas = verificar_y_expirar_disrupciones(simulacion)
    nuevas_disrupciones = verificar_y_activar_disrupciones(simulacion)
    if expiradas or nuevas_disrupciones:
        db.session.commit()

    # Disrupción activa sin respuesta (muestra el modal)
    disrupcion_pendiente_query = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.empresa_id == empresa.id,
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.opcion_elegida == None
    )
    if current_user.rol != 'compras':
        disrupcion_pendiente_query = disrupcion_pendiente_query.filter(
            DisrupcionEmpresa.disrupcion_key != 'retraso_proveedor'
        )
    if current_user.rol != 'ventas':
        disrupcion_pendiente_query = disrupcion_pendiente_query.filter(
            DisrupcionEmpresa.disrupcion_key != 'aumento_demanda'
        )
    if current_user.rol != 'logistica':
        disrupcion_pendiente_query = disrupcion_pendiente_query.filter(
            DisrupcionEmpresa.disrupcion_key != 'falla_flota'
        )
    disrupcion_pendiente = disrupcion_pendiente_query.first()

    # Disrupciones recién expiradas cuya notificación de cierre aún no se vio
    disrupciones_finalizadas_query = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.empresa_id == empresa.id,
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.activa == False,
        DisrupcionEmpresa.notificacion_fin_vista == False
    )
    if current_user.rol != 'compras':
        disrupciones_finalizadas_query = disrupciones_finalizadas_query.filter(
            DisrupcionEmpresa.disrupcion_key != 'retraso_proveedor'
        )
    if current_user.rol != 'ventas':
        disrupciones_finalizadas_query = disrupciones_finalizadas_query.filter(
            DisrupcionEmpresa.disrupcion_key != 'aumento_demanda'
        )
    if current_user.rol != 'logistica':
        disrupciones_finalizadas_query = disrupciones_finalizadas_query.filter(
            DisrupcionEmpresa.disrupcion_key != 'falla_flota'
        )
    disrupciones_finalizadas = disrupciones_finalizadas_query.all()

    # Disrupciones activas con decisi�n ya tomada (para info en dashboard)
    disrupciones_activas_query = DisrupcionEmpresa.query.filter(
        DisrupcionEmpresa.empresa_id == empresa.id,
        DisrupcionEmpresa.simulacion_id == simulacion.id,
        DisrupcionEmpresa.activa == True,
        DisrupcionEmpresa.opcion_elegida != None
    )
    if current_user.rol != 'compras':
        disrupciones_activas_query = disrupciones_activas_query.filter(
            DisrupcionEmpresa.disrupcion_key != 'retraso_proveedor'
        )
    if current_user.rol != 'ventas':
        disrupciones_activas_query = disrupciones_activas_query.filter(
            DisrupcionEmpresa.disrupcion_key != 'aumento_demanda'
        )
    if current_user.rol != 'logistica':
        disrupciones_activas_query = disrupciones_activas_query.filter(
            DisrupcionEmpresa.disrupcion_key != 'falla_flota'
        )
    disrupciones_activas = disrupciones_activas_query.all()

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
                         historico_operacion=historico_operacion,
                         ingresos_acumulados=ingresos_acumulados,
                         costos_acumulados=costos_acumulados,
                         utilidad_acumulada=utilidad_acumulada,
                         total_ventas_periodo=total_ventas_periodo,
                         ingresos_periodo=ingresos_periodo,
                         promedio_diario_periodo=promedio_diario_periodo,
                         disrupcion_pendiente=disrupcion_pendiente,
                         disrupciones_finalizadas=disrupciones_finalizadas,
                         disrupciones_activas=disrupciones_activas,
                         get_disrupcion=get_disrupcion)


@bp.route('/api/disrupcion/responder', methods=['POST'])
@login_required
@estudiante_required
def responder_disrupcion():
    """Registra la opcion elegida por el equipo ante una disrupcion."""
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
        flash('Ya se registr\u00f3 una decisi\u00f3n para esta disrupci\u00f3n.', 'warning')
        return redirect(url_for('estudiante.dashboard_general'))

    from utils.catalogo_disrupciones import get_disrupcion
    definicion = get_disrupcion(dis.disrupcion_key)
    if not definicion or opcion not in definicion['opciones']:
        flash('Opci\u00f3n inv\u00e1lida.', 'error')
        return redirect(url_for('estudiante.dashboard_general'))

    if dis.disrupcion_key == 'retraso_proveedor' and current_user.rol != 'compras':
        flash('Solo el rol de Compras puede decidir esta disrupci\u00f3n.', 'error')
        return redirect(url_for('estudiante.dashboard_general'))

    if dis.disrupcion_key == 'aumento_demanda' and current_user.rol != 'ventas':
        flash('Solo el rol de Ventas puede decidir esta disrupci\u00f3n.', 'error')
        return redirect(url_for('estudiante.dashboard_general'))

    if dis.disrupcion_key == 'falla_flota' and current_user.rol != 'logistica':
        flash('Solo el rol de Log\u00edstica puede decidir esta disrupci\u00f3n.', 'error')
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
        duracion = cat2.get('duracion_semanas', 2) if cat2 else 2
        producto_afectado = dis.producto_afectado
        compras_auto_factor = definicion['opciones']['A']['efectos'].get('compras_auto_factor', 0.40)
        cantidad_auto = round(producto_afectado.demanda_promedio * duracion * compras_auto_factor)
        orden_auto = Compra(
            empresa_id=empresa.id,
            producto_id=dis.producto_afectado_id,
            semana_orden=simulacion.dia_actual,
            semana_entrega=simulacion.dia_actual + producto_afectado.tiempo_entrega,
            cantidad=cantidad_auto,
            costo_unitario=producto_afectado.costo_unitario,
            costo_total=cantidad_auto * producto_afectado.costo_unitario,
            estado='en_transito',
        )
        db.session.add(orden_auto)
        dis.efecto_inicial_aplicado = True
        msg_extra = (
            f' Se emiti\u00f3 autom\u00e1ticamente una orden de compra de {cantidad_auto} unidades '
            f'de {producto_afectado.nombre} (entrega d\u00eda {simulacion.dia_actual + producto_afectado.tiempo_entrega}).'
        )

    # Efecto inmediato disrupcion 1 (retraso_proveedor): confirmar decisión de Compras.
    elif dis.disrupcion_key == 'retraso_proveedor' and not dis.efecto_inicial_aplicado:
        dis.efecto_inicial_aplicado = True
        if opcion == 'A':
            msg_extra = (' Se activ\u00f3 proveedor alterno: lead time 2 d\u00edas para Sangre de la Vid y Susurro Rosado '
                         'y 3 d\u00edas para Elixir Dorado y Oceano Profundo, con +$5.000 por unidad.')
        else:
            msg_extra = (' Se activ\u00f3 racionamiento de inventario: '
                         'se mantiene proveedor actual y prioridad de clientes estrat\u00e9gicos.')

    # Efecto inmediato disrupcion 3 (falla_flota): retroactivo en despachos en tránsito
    elif dis.disrupcion_key == 'falla_flota' and not dis.efecto_inicial_aplicado:
        efectos = definicion['opciones'][opcion]['efectos']
        mult_costo = efectos.get('costo_multiplicador', 1.0)
        delay_d = efectos.get('delay_semanas', 0)

        despachos_activos = DespachoRegional.query.filter_by(
            empresa_id=empresa.id,
            estado='en_transito'
        ).all()

        costos_originales = {}
        for d in despachos_activos:
            base = d.costo_transporte or 0
            costos_originales[d.id] = base
            if mult_costo != 1.0:
                d.costo_transporte = round(base * mult_costo)
            if delay_d:
                d.semana_entrega_estimado += delay_d

        dis.datos_extra = {'costos_originales': costos_originales}
        dis.efecto_inicial_aplicado = True

        if opcion == 'A':
            msg_extra = (' Se habilit\u00f3 transporte externo para cubrir faltantes de capacidad. '
                         'Los despachos podr\u00e1n usar flota tercerizada con costo por unidad de $3.000.')
        elif opcion == 'B':
            msg_extra = (' Se restringi\u00f3 la operaci\u00f3n a capacidad interna. '
                         'No se permitir\u00e1 transporte externo mientras est\u00e9 activa la disrupci\u00f3n.')
        elif delay_d:
            msg_extra = (f' {len(despachos_activos)} despachos en tr\u00e1nsito retrasados '
                         f'+{delay_d} d\u00eda(s). Sin costo adicional.')
        else:
            pct = round((mult_costo - 1) * 100)
            msg_extra = (f' El costo de transporte de los {len(despachos_activos)} despachos '
                         f'en tr\u00e1nsito aument\u00f3 un {pct}%. Los nuevos despachos tambi\u00e9n '
                         'tendr\u00e1n el costo adicional durante 2 semanas.')

    else:
        msg_extra = ''

    # Registrar en tabla de decisiones
    decision = Decision(
        usuario_id=current_user.id,
        empresa_id=empresa.id,
        semana_simulacion=simulacion.dia_actual,
        tipo_decision='disrupcion_respuesta',
        datos_decision={
            'disrupcion_key': dis.disrupcion_key,
            'opcion_elegida': opcion,
            'producto_afectado_id': dis.producto_afectado_id,
        }
    )
    db.session.add(decision)
    db.session.commit()

    flash(f'\u2705 Decisi\u00f3n registrada: Opci\u00f3n {opcion} - {definicion["opciones"][opcion]["titulo"]}.{msg_extra}', 'success')
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
@rol_required('ventas')
def dashboard_ventas():
    simulacion = Simulacion.query.filter_by(activa=True).first()
    empresa = current_user.empresa
    
    return render_template('estudiante/ventas/dashboard.html',
                         simulacion=simulacion,
                         empresa=empresa)


def _obtener_aprobaciones_ventas_dia(empresa_id, dia_simulacion):
    """Obtiene mapa de aprobaciones guardadas por Ventas para el día actual."""
    simulacion = Simulacion.query.filter_by(activa=True).first()

    query = Decision.query.filter_by(
        empresa_id=empresa_id,
        tipo_decision='ventas_aprobacion_diaria',
        semana_simulacion=dia_simulacion
    )

    # Aislar decisiones de ventas a la simulación activa (evita arrastre entre reinicios).
    if simulacion and simulacion.fecha_inicio:
        query = query.filter(Decision.created_at >= simulacion.fecha_inicio)

    decision = query.order_by(Decision.created_at.desc()).first()

    mapa = {}
    if not decision or not decision.datos_decision:
        return mapa

    for item in decision.datos_decision.get('aprobaciones', []):
        pid = int(item.get('producto_id', 0))
        region = item.get('region')
        cant = int(item.get('cantidad_aprobada', 0))
        if pid and region:
            mapa[(pid, region)] = max(0, cant)
    return mapa


def _saldo_despachable_por_ventas(empresa_id, dia_simulacion, producto_id, region):
    """Retorna (aprobado, ya_despachado, saldo_pendiente) para producto-región del día."""
    aprobaciones = _obtener_aprobaciones_ventas_dia(empresa_id, dia_simulacion)
    aprobado = int(aprobaciones.get((int(producto_id), region), 0) or 0)

    ya_despachado = db.session.query(
        db.func.coalesce(db.func.sum(DespachoRegional.cantidad), 0)
    ).filter(
        DespachoRegional.empresa_id == empresa_id,
        DespachoRegional.producto_id == int(producto_id),
        DespachoRegional.region == region,
        DespachoRegional.semana_despacho == dia_simulacion,
    ).scalar() or 0

    ya_despachado = int(round(float(ya_despachado)))
    saldo = max(0, aprobado - ya_despachado)
    return aprobado, ya_despachado, saldo


def _vehiculo_ocupado_por_ciclo(empresa_id, vehiculo_id, dia_actual):
    """Retorna día de retorno si el vehículo está ocupado por ciclo en el día actual."""
    return db.session.query(
        db.func.max(DisponibilidadVehiculo.dia_disponible_retorno)
    ).filter(
        DisponibilidadVehiculo.empresa_id == empresa_id,
        DisponibilidadVehiculo.vehiculo_id == vehiculo_id,
        DisponibilidadVehiculo.dia_disponible_retorno >= dia_actual,
    ).scalar()


@bp.route('/api/ventas/pedidos-dia')
@login_required
@estudiante_required
def api_ventas_pedidos_dia():
    """API: pedidos solicitados por región (demanda) y cantidades aprobadas por Ventas."""
    try:
        empresa = current_user.empresa
        simulacion = Simulacion.query.filter_by(activa=True).first()

        if not simulacion:
            return jsonify({'success': False, 'message': 'No hay simulación activa'}), 404

        dia = simulacion.dia_actual
        productos = Producto.query.filter_by(activo=True).all()
        inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
        inv_map = {inv.producto_id: int(round(inv.cantidad_actual or 0)) for inv in inventarios}

        filas_demanda = DemandaMercadoDiaria.query.filter_by(
            simulacion_id=simulacion.id,
            dia_simulacion=dia,
        ).all()

        demanda_map = {(f.producto_id, f.region): int(f.demanda_base or 0) for f in filas_demanda}
        aprobaciones = _obtener_aprobaciones_ventas_dia(empresa.id, dia)

        productos_data = []
        for p in productos:
            regiones = []
            total_solicitado = 0
            total_aprobado = 0
            for region in REGIONES_CANONICAS:
                solicitado = int(demanda_map.get((p.id, region), 0))
                aprobado = int(aprobaciones.get((p.id, region), 0))
                aprobado = max(0, min(aprobado, solicitado))
                regiones.append({
                    'region': region,
                    'solicitado': solicitado,
                    'aprobado': aprobado,
                })
                total_solicitado += solicitado
                total_aprobado += aprobado

            productos_data.append({
                'producto_id': p.id,
                'producto_nombre': p.nombre,
                'inventario_actual': int(inv_map.get(p.id, 0)),
                'total_solicitado': total_solicitado,
                'total_aprobado': total_aprobado,
                'regiones': regiones,
            })

        return jsonify({
            'success': True,
            'dia_actual': dia,
            'productos': productos_data,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/ventas/aprobar-pedidos', methods=['POST'])
@login_required
@estudiante_required
@rol_required('ventas')
def api_ventas_aprobar_pedidos():
    """Guarda las cantidades aprobadas por Ventas para el día actual."""
    try:
        data = request.get_json(silent=True) or {}
        aprobaciones = data.get('aprobaciones', [])

        empresa = current_user.empresa
        simulacion = Simulacion.query.filter_by(activa=True).first()
        if not simulacion:
            return jsonify({'success': False, 'message': 'No hay simulación activa'}), 404

        dia = simulacion.dia_actual
        filas_demanda = DemandaMercadoDiaria.query.filter_by(
            simulacion_id=simulacion.id,
            dia_simulacion=dia,
        ).all()

        demanda_map = {(f.producto_id, f.region): int(f.demanda_base or 0) for f in filas_demanda}
        if not demanda_map:
            return jsonify({'success': False, 'message': f'No hay base de demanda para el día {dia}.'}), 400

        inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
        inv_map = {inv.producto_id: int(round(inv.cantidad_actual or 0)) for inv in inventarios}

        validado = []
        total_por_producto = {}

        for item in aprobaciones:
            producto_id = int(item.get('producto_id', 0))
            region = (item.get('region') or '').strip()
            cantidad_aprobada = int(item.get('cantidad_aprobada', 0))

            if producto_id <= 0 or region not in REGIONES_CANONICAS:
                continue

            solicitado = int(demanda_map.get((producto_id, region), 0))
            if solicitado <= 0:
                continue

            if cantidad_aprobada < 0:
                return jsonify({'success': False, 'message': 'No se permiten aprobaciones negativas.'}), 400
            if cantidad_aprobada > solicitado:
                return jsonify({
                    'success': False,
                    'message': f'No puedes aprobar más de lo solicitado ({region}).'
                }), 400

            total_por_producto[producto_id] = total_por_producto.get(producto_id, 0) + cantidad_aprobada
            validado.append({
                'producto_id': producto_id,
                'region': region,
                'cantidad_solicitada': solicitado,
                'cantidad_aprobada': cantidad_aprobada,
            })

        for producto_id, total_aprobado in total_por_producto.items():
            stock_actual = int(inv_map.get(producto_id, 0))
            if total_aprobado > stock_actual:
                producto = Producto.query.get(producto_id)
                nombre = producto.nombre if producto else f'Producto {producto_id}'
                return jsonify({
                    'success': False,
                    'message': (
                        f'{nombre}: aprobación total ({total_aprobado}) supera inventario actual ({stock_actual}).'
                    )
                }), 400

        # Reemplazar decisión del día para mantener una sola versión activa.
        Decision.query.filter_by(
            empresa_id=empresa.id,
            tipo_decision='ventas_aprobacion_diaria',
            semana_simulacion=dia
        ).delete(synchronize_session=False)

        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=empresa.id,
            semana_simulacion=dia,
            tipo_decision='ventas_aprobacion_diaria',
            datos_decision={
                'dia': dia,
                'aprobaciones': validado,
            }
        )
        db.session.add(decision)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Aprobaciones guardadas para el día {dia}.',
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


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
            semana_simulacion=simulacion.dia_actual
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
            Venta.semana_simulacion >= max(1, simulacion.dia_actual - 7)
        ).group_by(Producto.nombre).order_by(func.sum(Venta.cantidad_vendida).desc()).limit(5).all()
        
        # Ventas por regi�n (�ltimos 7 d�as)
        ventas_region = db.session.query(
            Venta.region,
            func.sum(Venta.cantidad_vendida).label('cantidad'),
            func.sum(Venta.ingreso_total).label('ingresos')
        ).filter(
            Venta.empresa_id == empresa.id,
            Venta.semana_simulacion >= max(1, simulacion.dia_actual - 7)
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
        
        regiones = REGIONES_CANONICAS
        
        productos_data = []
        for producto in productos:
            precios = {}
            
            # Obtener precios actuales por regi�n (�ltimas ventas)
            for region in regiones:
                ultima_venta = Venta.query.filter(
                    Venta.empresa_id == empresa.id,
                    Venta.producto_id == producto.id,
                    Venta.region.in_(variantes_region(region))
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
                semana_simulacion=simulacion.dia_actual,
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
        
        regiones = REGIONES_CANONICAS
        regiones_data = []
        
        for region in regiones:
            # Ventas �ltimos 7 d�as
            ventas_recientes = Venta.query.filter(
                Venta.empresa_id == empresa.id,
                Venta.region.in_(variantes_region(region)),
                Venta.semana_simulacion >= max(1, simulacion.dia_actual - 7)
            ).all()

            ingresos_recientes = sum([v.ingreso_total for v in ventas_recientes])
            
            # Producto m�s vendido
            from sqlalchemy import func
            top = db.session.query(
                Producto.nombre
            ).join(Venta).filter(
                Venta.empresa_id == empresa.id,
                Venta.region.in_(variantes_region(region)),
                Venta.semana_simulacion >= max(1, simulacion.dia_actual - 7)
            ).group_by(Producto.nombre).order_by(func.sum(Venta.cantidad_vendida).desc()).first()
            
            regiones_data.append({
                'nombre': region,
                'ventas_totales': len(ventas_recientes),
                'ingresos': int(ingresos_recientes),
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
            semana_simulacion=simulacion.dia_actual,
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
    """Mantiene compatibilidad con el enlace legado de análisis regional."""
    return redirect(url_for('estudiante.dashboard_ventas') + '#regiones')


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
        Venta.semana_simulacion >= max(1, simulacion.dia_actual - dias)
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
            Venta.semana_simulacion >= max(1, simulacion.dia_actual - dias)
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


@bp.route('/api/ventas/demanda-mercado')
@login_required
@estudiante_required
@rol_required('ventas')
def api_ventas_demanda_mercado():
    """API: Demanda total del mercado vs asignacion vs ventas reales por dia"""
    empresa_id = current_user.empresa_id
    simulacion = Simulacion.query.filter_by(activa=True).first()
    if not simulacion:
        return jsonify({'error': 'No hay simulacion activa'}), 404

    dias = int(request.args.get('dias', 30))
    dia_hasta = simulacion.dia_actual
    desde = max(1, dia_hasta - dias + 1)
    dias_list = list(range(desde, dia_hasta + 1))

    ventas_rango = Venta.query.filter(
        Venta.empresa_id == empresa_id,
        Venta.semana_simulacion >= desde,
        Venta.semana_simulacion <= dia_hasta,
    ).all()

    demanda_rango = db.session.query(
        DemandaMercadoDiaria.dia_simulacion,
        func.sum(DemandaMercadoDiaria.demanda_base).label('total_demanda')
    ).filter(
        DemandaMercadoDiaria.simulacion_id == simulacion.id,
        DemandaMercadoDiaria.dia_simulacion >= desde,
        DemandaMercadoDiaria.dia_simulacion <= dia_hasta,
    ).group_by(DemandaMercadoDiaria.dia_simulacion).all()

    decisiones_rango = Decision.query.filter(
        Decision.empresa_id == empresa_id,
        Decision.tipo_decision == 'ventas_aprobacion_diaria',
        Decision.semana_simulacion >= desde,
        Decision.semana_simulacion <= dia_hasta,
    ).order_by(Decision.semana_simulacion.asc(), Decision.created_at.asc()).all()

    demanda_por_dia = {d: 0 for d in dias_list}
    asignada_por_dia = {d: 0 for d in dias_list}
    vendida_por_dia = {d: 0 for d in dias_list}

    for row in demanda_rango:
        demanda_por_dia[int(row.dia_simulacion)] = int(round(row.total_demanda or 0))

    ultima_decision_dia = {}
    for dec in decisiones_rango:
        ultima_decision_dia[dec.semana_simulacion] = dec

    for dia, dec in ultima_decision_dia.items():
        if not dec.datos_decision:
            continue
        asignada_por_dia[dia] = int(sum(
            int(item.get('cantidad_aprobada', 0) or 0)
            for item in dec.datos_decision.get('aprobaciones', [])
        ))

    for v in ventas_rango:
        d = int(v.semana_simulacion)
        if d in vendida_por_dia:
            vendida_por_dia[d] += int(round(v.cantidad_vendida or 0))

    return jsonify({
        'dias': dias_list,
        'demanda_mercado': [round(demanda_por_dia[d], 1) for d in dias_list],
        'cantidad_asignada': [round(asignada_por_dia[d], 1) for d in dias_list],
        'cantidad_vendida': [round(vendida_por_dia[d], 1) for d in dias_list]
    })


# ============== DASHBOARD PLANEACI�N ==============
@bp.route('/planeacion')
@login_required
@estudiante_required
@rol_required('planeacion', 'compras', ROL_PLANEACION_COMPRAS)
def dashboard_planeacion():
    """La Planeación se integró con Compras en un único módulo operativo."""
    flash('Planeación y Compras ahora están integradas en un solo módulo.', 'info')
    return redirect(url_for('estudiante.dashboard_compras'))


@bp.route('/planeacion/generar-pronostico')
@login_required
@estudiante_required
def generar_pronostico():
    """Mantiene compatibilidad con ruta legacy y redirige al panel vigente."""
    flash('La gestión de pronósticos ahora se realiza fuera de la app. Exporta ventas desde Planeación y Compras.', 'info')
    return redirect(url_for('estudiante.dashboard_compras'))


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
            semana_generacion=simulacion.dia_actual,
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
            semana_simulacion=simulacion.dia_actual,
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
    """Ruta legacy de planeación; redirige al flujo activo de requerimientos."""
    return redirect(url_for('estudiante.ver_requerimientos'))


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
            semana_generacion=simulacion.dia_actual,
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
            semana_simulacion=simulacion.dia_actual,
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
    if not _role_allowed(current_user.rol, ['planeacion', 'compras', ROL_PLANEACION_COMPRAS]):
        return jsonify({'error': 'No autorizado'}), 403
    
    empresa_id = current_user.empresa_id
    
    simulacion = Simulacion.query.filter_by(activa=True).first()
    if not simulacion:
        return jsonify({'error': 'No hay simulación activa'}), 404

    dias = list(range(-30, simulacion.dia_actual + 1))
    if 0 in dias:
        dias.remove(0)

    demanda_rows = db.session.query(
        DemandaMercadoDiaria.dia_simulacion,
        func.sum(DemandaMercadoDiaria.demanda_base).label('demanda_total')
    ).filter(
        DemandaMercadoDiaria.simulacion_id == simulacion.id,
        DemandaMercadoDiaria.producto_id == producto_id,
        DemandaMercadoDiaria.dia_simulacion >= -30,
        DemandaMercadoDiaria.dia_simulacion <= simulacion.dia_actual,
    ).group_by(DemandaMercadoDiaria.dia_simulacion).all()

    ventas_rows = db.session.query(
        Venta.semana_simulacion,
        func.sum(Venta.cantidad_vendida).label('vendido_total'),
        func.sum(Venta.cantidad_perdida).label('perdido_total')
    ).filter(
        Venta.empresa_id == empresa_id,
        Venta.producto_id == producto_id,
        Venta.semana_simulacion >= -30,
        Venta.semana_simulacion <= simulacion.dia_actual,
    ).group_by(Venta.semana_simulacion).all()

    demanda_por_dia = {d: 0 for d in dias}
    vendido_por_dia = {d: 0 for d in dias}
    perdido_por_dia = {d: 0 for d in dias}

    for row in demanda_rows:
        dia = int(row.dia_simulacion)
        if dia in demanda_por_dia:
            demanda_por_dia[dia] = int(round(row.demanda_total or 0))

    for row in ventas_rows:
        dia = int(row.semana_simulacion)
        if dia in vendido_por_dia:
            vendido_por_dia[dia] = int(round(row.vendido_total or 0))
            perdido_por_dia[dia] = int(round(row.perdido_total or 0))
    
    resultado = {
        'labels': dias,
        'datasets': [{
            'label': 'Demanda (Solicitado)',
            'data': [demanda_por_dia[dia] for dia in dias],
            'borderColor': '#3498db',
            'backgroundColor': 'rgba(52, 152, 219, 0.1)',
            'tension': 0.4
        }, {
            'label': 'Vendido',
            'data': [vendido_por_dia[dia] for dia in dias],
            'borderColor': '#2ecc71',
            'backgroundColor': 'rgba(46, 204, 113, 0.1)',
            'tension': 0.4
        }, {
            'label': 'Perdido',
            'data': [perdido_por_dia[dia] for dia in dias],
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
@rol_required('planeacion', 'compras', ROL_PLANEACION_COMPRAS)
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
    
    # �rdenes de compra recientes
    ordenes_compra = Compra.query.filter_by(empresa_id=empresa.id)\
        .order_by(Compra.semana_orden.desc())\
        .limit(15).all()
    
    # �rdenes en tr�nsito
    ordenes_transito = Compra.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).order_by(Compra.semana_entrega.asc()).all()

    # Capital en Compras: se muestra el capital actual real de la empresa.
    # Las órdenes en tránsito se informan, pero no descuentan nuevamente en este panel.
    capital_comprometido = sum([o.costo_total for o in ordenes_transito])
    capital_libre = float(empresa.capital_actual or 0)

    disrupcion_retraso_activa = _disrupcion_retraso_proveedor_activa(simulacion, empresa.id)
    
    return render_template('estudiante/compras/dashboard.html',
                         simulacion=simulacion,
                         empresa=empresa,
                         productos=productos,
                         inventarios_dict=inventarios_dict,
                         ordenes_compra=ordenes_compra,
                         ordenes_transito=ordenes_transito,
                         capital_comprometido=capital_comprometido,
                         capital_libre=capital_libre,
                         disrupcion_retraso_activa=disrupcion_retraso_activa)


@bp.route('/compras/exportar-ventas-csv')
@login_required
@estudiante_required
def exportar_ventas_csv():
    """Exporta demanda base + operación de la empresa para análisis diario."""
    empresa = current_user.empresa
    simulacion = Simulacion.query.filter_by(activa=True).first()
    if not simulacion:
        flash('No hay simulación activa para exportar datos.', 'warning')
        return redirect(url_for('estudiante.dashboard_general'))

    dia_hasta = int(simulacion.dia_actual or 1)

    demanda_rows = DemandaMercadoDiaria.query.filter(
        DemandaMercadoDiaria.simulacion_id == simulacion.id,
        DemandaMercadoDiaria.dia_simulacion >= -30,
        DemandaMercadoDiaria.dia_simulacion <= dia_hasta,
        DemandaMercadoDiaria.dia_simulacion != 0,
    ).order_by(
        DemandaMercadoDiaria.dia_simulacion.asc(),
        DemandaMercadoDiaria.producto_id.asc(),
        DemandaMercadoDiaria.region.asc(),
    ).all()

    ventas_rows = db.session.query(
        Venta.semana_simulacion,
        Venta.producto_id,
        Venta.region,
        func.sum(Venta.cantidad_solicitada).label('pedidos_demandados'),
        func.sum(Venta.cantidad_vendida).label('unidades_vendidas'),
        func.sum(Venta.cantidad_perdida).label('unidades_perdidas'),
        func.sum(Venta.ingreso_total).label('ingreso_total')
    ).filter(
        Venta.empresa_id == empresa.id,
        Venta.semana_simulacion >= -30,
        Venta.semana_simulacion <= dia_hasta,
        Venta.semana_simulacion != 0,
    ).group_by(
        Venta.semana_simulacion,
        Venta.producto_id,
        Venta.region,
    ).all()

    ventas_map = {
        (int(v.semana_simulacion), int(v.producto_id), v.region): {
            'pedidos_demandados': int(round(v.pedidos_demandados or 0)),
            'unidades_vendidas': int(round(v.unidades_vendidas or 0)),
            'unidades_perdidas': int(round(v.unidades_perdidas or 0)),
            'ingreso_total': float(v.ingreso_total or 0),
        }
        for v in ventas_rows
    }

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'dia_simulacion',
        'producto',
        'region',
        'demanda_base',
    ])

    for row in demanda_rows:
        key = (int(row.dia_simulacion), int(row.producto_id), row.region)
        v = ventas_map.get(key, {})
        producto_nombre = row.producto.nombre if row.producto else row.producto_id

        writer.writerow([
            int(row.dia_simulacion),
            producto_nombre,
            row.region,
            int(round(row.demanda_base or 0)),
        ])

    response = make_response(output.getvalue())
    output.close()
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = (
        f'attachment; filename=demanda_ventas_empresa_{empresa.id}_hasta_dia_{dia_hasta}.csv'
    )
    return response


@bp.route('/compras/requerimientos')
@login_required
@estudiante_required
def ver_requerimientos():
    """Vista de requerimientos para Planeación y Compras."""
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
        proveedor = _normalizar_proveedor(request.form.get('proveedor', 'A'))
        notas_compras = request.form.get('notas_compras', '')
        
        simulacion = Simulacion.query.filter_by(activa=True).first()
        producto = Producto.query.get(requerimiento.producto_id)
        
        condiciones = _calcular_condiciones_compra(
            producto=producto,
            cantidad=cantidad,
            simulacion=simulacion,
            empresa_id=current_user.empresa_id,
            proveedor=proveedor,
        )
        if not condiciones['ok']:
            flash(condiciones['mensaje'], 'error')
            return redirect(url_for('estudiante.ver_requerimientos'))

        costo_unitario = condiciones['costo_unitario']
        tiempo_entrega = condiciones['tiempo_entrega']
        delay_extra = condiciones['delay_extra']

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
        semana_entrega = simulacion.dia_actual + tiempo_entrega + delay_extra

        compra = Compra(
            empresa_id=current_user.empresa_id,
            producto_id=requerimiento.producto_id,
            semana_orden=simulacion.dia_actual,
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
            semana_simulacion=simulacion.dia_actual,
            tipo_decision='orden_compra_requerimiento',
            datos_decision={
                'requerimiento_id': requerimiento_id,
                'producto_id': requerimiento.producto_id,
                'proveedor': proveedor,
                'proveedor_nombre': condiciones['proveedor_nombre'],
                'cantidad_sugerida': requerimiento.cantidad_sugerida,
                'cantidad_ordenada': cantidad,
                'costo_total': costo_total,
                'lead_time_aplicado': tiempo_entrega + delay_extra,
            }
        )
        
        db.session.add(decision)
        db.session.commit()
        
        flash(f'Orden creada con proveedor {proveedor}: {cantidad:.0f} unidades de {producto.nombre}. Llegará día {semana_entrega}', 'success')
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
        proveedor = _normalizar_proveedor(request.form.get('proveedor', 'A'))
        
        simulacion = Simulacion.query.filter_by(activa=True).first()
        producto = Producto.query.get(producto_id)
        
        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('estudiante.dashboard_compras'))
        
        condiciones = _calcular_condiciones_compra(
            producto=producto,
            cantidad=cantidad,
            simulacion=simulacion,
            empresa_id=current_user.empresa_id,
            proveedor=proveedor,
        )
        if not condiciones['ok']:
            flash(condiciones['mensaje'], 'error')
            return redirect(url_for('estudiante.dashboard_compras'))

        costo_unitario = condiciones['costo_unitario']
        tiempo_entrega = condiciones['tiempo_entrega']
        delay_extra = condiciones['delay_extra']

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
        semana_entrega = simulacion.dia_actual + tiempo_entrega + delay_extra
        
        compra = Compra(
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            semana_orden=simulacion.dia_actual,
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
            semana_simulacion=simulacion.dia_actual,
            tipo_decision='orden_compra_manual',
            datos_decision={
                'producto_id': producto_id,
                'proveedor': proveedor,
                'proveedor_nombre': condiciones['proveedor_nombre'],
                'cantidad': cantidad,
                'costo_total': costo_total,
                'lead_time_aplicado': tiempo_entrega + delay_extra,
            }
        )
        
        db.session.add(compra)
        db.session.add(decision)
        db.session.commit()
        
        flash(f'Orden creada con proveedor {proveedor}: {cantidad:.0f} unidades. Llegará día {semana_entrega}', 'success')
        return redirect(url_for('estudiante.dashboard_compras'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear orden: {str(e)}', 'error')
        return redirect(url_for('estudiante.dashboard_compras'))


@bp.route('/compras/crear-pedido-general', methods=['POST'])
@login_required
@estudiante_required
@rol_required('planeacion', 'compras', ROL_PLANEACION_COMPRAS)
def crear_pedido_general():
    """Crear múltiples órdenes de compra en una sola operación."""
    try:
        simulacion = Simulacion.query.filter_by(activa=True).first()
        empresa = current_user.empresa

        productos_activos = {
            p.id: p for p in Producto.query.filter_by(activo=True).all()
        }

        solicitudes = []
        for key, value in request.form.items():
            # Procesa qty_actual_<id> y qty_externo_<id>
            if key.startswith('qty_actual_') or key.startswith('qty_externo_'):
                try:
                    if key.startswith('qty_actual_'):
                        producto_id = int(key.split('_', 2)[2])
                        proveedor = 'ACTUAL'
                    else:
                        producto_id = int(key.split('_', 2)[2])
                        proveedor = 'EXTERNO'
                    cantidad = float(value or 0)
                except (ValueError, TypeError, IndexError):
                    continue

                if cantidad > 0:
                    solicitudes.append((producto_id, cantidad, proveedor))

        if not solicitudes:
            flash('Debes ingresar al menos una cantidad mayor a 0 para crear el pedido general.', 'warning')
            return redirect(url_for('estudiante.dashboard_compras') + '#pedido-general')

        ordenes_preparadas = []
        for producto_id, cantidad, proveedor in solicitudes:
            producto = productos_activos.get(producto_id)
            if not producto:
                flash(f'Producto inválido en pedido general: {producto_id}', 'error')
                return redirect(url_for('estudiante.dashboard_compras') + '#pedido-general')

            # Validar múltiplos: 30 para 750mL, 20 para 1L
            multiplo_valido, mensaje_multiplo = _validar_multiplos_pedido(producto, cantidad)
            if not multiplo_valido:
                flash(f"{producto.nombre} ({proveedor}): {mensaje_multiplo}", 'error')
                return redirect(url_for('estudiante.dashboard_compras') + '#pedido-general')

            condiciones = _calcular_condiciones_compra(
                producto=producto,
                cantidad=cantidad,
                simulacion=simulacion,
                empresa_id=current_user.empresa_id,
                proveedor=proveedor,
            )
            if not condiciones['ok']:
                flash(f"{producto.nombre} ({proveedor}): {condiciones['mensaje']}", 'error')
                return redirect(url_for('estudiante.dashboard_compras') + '#pedido-general')

            costo_unitario = condiciones['costo_unitario']
            tiempo_entrega = condiciones['tiempo_entrega']
            delay_extra = condiciones['delay_extra']

            costo_total = cantidad * costo_unitario
            semana_entrega = simulacion.dia_actual + tiempo_entrega + delay_extra

            ordenes_preparadas.append({
                'producto': producto,
                'cantidad': cantidad,
                'proveedor': proveedor,
                'costo_unitario': costo_unitario,
                'costo_total': costo_total,
                'semana_entrega': semana_entrega
            })

        costo_total_general = sum(item['costo_total'] for item in ordenes_preparadas)
        ordenes_pendientes = Compra.query.filter_by(
            empresa_id=empresa.id,
            estado='en_transito'
        ).all()

        validacion = validar_capacidad_compra(
            empresa.capital_actual,
            costo_total_general,
            ordenes_pendientes
        )
        if not validacion['puede_comprar']:
            flash(f"Capital insuficiente para pedido general. {validacion['sugerencia']}", 'error')
            return redirect(url_for('estudiante.dashboard_compras') + '#pedido-general')

        for item in ordenes_preparadas:
            compra = Compra(
                empresa_id=current_user.empresa_id,
                producto_id=item['producto'].id,
                semana_orden=simulacion.dia_actual,
                semana_entrega=item['semana_entrega'],
                cantidad=item['cantidad'],
                costo_unitario=item['costo_unitario'],
                costo_total=item['costo_total'],
                estado='en_transito'
            )
            db.session.add(compra)

        empresa.capital_actual -= costo_total_general

        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            semana_simulacion=simulacion.dia_actual,
            tipo_decision='orden_compra_general',
            datos_decision={
                'ordenes': [
                    {
                        'producto_id': item['producto'].id,
                        'producto': item['producto'].nombre,
                        'proveedor': item['proveedor'],
                        'cantidad': item['cantidad'],
                        'costo_total': item['costo_total'],
                        'semana_entrega': item['semana_entrega']
                    }
                    for item in ordenes_preparadas
                ],
                'costo_total_general': costo_total_general
            }
        )
        db.session.add(decision)
        db.session.commit()

        flash(
            f'Pedido general creado con {len(ordenes_preparadas)} órdenes. '
            f'Costo total: ${costo_total_general:,.0f}.',
            'success'
        )
        return redirect(url_for('estudiante.dashboard_compras') + '#ordenes')

        costo_total_general = sum(item['costo_total'] for item in ordenes_preparadas)
        ordenes_pendientes = Compra.query.filter_by(
            empresa_id=empresa.id,
            estado='en_transito'
        ).all()

        validacion = validar_capacidad_compra(
            empresa.capital_actual,
            costo_total_general,
            ordenes_pendientes
        )
        if not validacion['puede_comprar']:
            flash(f"Capital insuficiente para pedido general. {validacion['sugerencia']}", 'error')
            return redirect(url_for('estudiante.dashboard_compras') + '#pedido-general')

        for item in ordenes_preparadas:
            compra = Compra(
                empresa_id=current_user.empresa_id,
                producto_id=item['producto'].id,
                semana_orden=simulacion.dia_actual,
                semana_entrega=item['semana_entrega'],
                cantidad=item['cantidad'],
                costo_unitario=item['costo_unitario'],
                costo_total=item['costo_total'],
                estado='en_transito'
            )
            db.session.add(compra)

        empresa.capital_actual -= costo_total_general

        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            semana_simulacion=simulacion.dia_actual,
            tipo_decision='orden_compra_general',
            datos_decision={
                'ordenes': [
                    {
                        'producto_id': item['producto'].id,
                        'producto': item['producto'].nombre,
                        'proveedor': item['proveedor'],
                        'cantidad': item['cantidad'],
                        'costo_total': item['costo_total'],
                        'semana_entrega': item['semana_entrega']
                    }
                    for item in ordenes_preparadas
                ],
                'costo_total_general': costo_total_general
            }
        )
        db.session.add(decision)
        db.session.commit()

        flash(
            f'Pedido general creado con {len(ordenes_preparadas)} órdenes. '
            f'Costo total: ${costo_total_general:,.0f}.',
            'success'
        )
        return redirect(url_for('estudiante.dashboard_compras') + '#ordenes')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear pedido general: {str(e)}', 'error')
        return redirect(url_for('estudiante.dashboard_compras') + '#pedido-general')


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


@bp.route('/compras/recibir-orden/<int:compra_id>', methods=['POST'])
@login_required
@estudiante_required
@rol_required('planeacion', 'compras', ROL_PLANEACION_COMPRAS)
def recibir_orden_compra_compras(compra_id):
    """Recepción movida al módulo de Logística."""
    flash('La recepción de pedidos ahora se gestiona desde Logística.', 'info')
    return redirect(url_for('estudiante.vista_recepcion'))


def _procesar_recepcion_compra_individual(compra, usuario_id, empresa_id):
    """Procesa una compra individual y retorna (éxito, mensaje)."""
    if compra.estado != 'en_transito':
        return False, 'Esta orden ya fue recibida o no está en tránsito'

    simulacion = Simulacion.query.filter_by(activa=True).first()
    if not simulacion:
        return False, 'No existe una simulación activa'

    if simulacion.dia_actual < compra.semana_entrega:
        return False, f'Esta orden llega el día {compra.semana_entrega}. Aún no puede ser recibida.'

    inventario = Inventario.query.filter_by(
        empresa_id=empresa_id,
        producto_id=compra.producto_id
    ).first()

    if not inventario:
        inventario = Inventario(
            empresa_id=empresa_id,
            producto_id=compra.producto_id,
            cantidad_actual=0,
            costo_promedio=compra.costo_unitario
        )
        db.session.add(inventario)

    resultado = procesar_recepcion_compra(compra, inventario)
    compra.estado = 'entregado'

    movimiento = MovimientoInventario(
        empresa_id=empresa_id,
        producto_id=compra.producto_id,
        usuario_id=usuario_id,
        semana_simulacion=simulacion.dia_actual,
        tipo_movimiento='entrada_compra',
        cantidad=compra.cantidad,
        saldo_anterior=resultado['cantidad_anterior'],
        saldo_nuevo=resultado['cantidad_nueva'],
        compra_id=compra.id,
        observaciones=f"Recepción de compra. Costo unitario: ${compra.costo_unitario:,.0f}"
    )

    decision = Decision(
        usuario_id=usuario_id,
        empresa_id=empresa_id,
        semana_simulacion=simulacion.dia_actual,
        tipo_decision='recepcion_compra',
        datos_decision={
            'compra_id': compra.id,
            'producto_id': compra.producto_id,
            'cantidad': compra.cantidad
        },
        resultado=resultado
    )

    db.session.add(movimiento)
    db.session.add(decision)
    db.session.commit()

    return True, f'Orden recibida: {compra.cantidad:.0f} unidades de {compra.producto.nombre}. Nuevo stock: {resultado["cantidad_nueva"]:.0f}'


@bp.route('/compras/recibir-todas-ordenes', methods=['POST'])
@login_required
@estudiante_required
@rol_required('planeacion', 'compras', ROL_PLANEACION_COMPRAS)
def recibir_todas_ordenes_compras():
    """Recepción masiva movida al módulo de Logística."""
    flash('La recepción masiva ahora se gestiona desde Logística.', 'info')
    return redirect(url_for('estudiante.vista_recepcion'))


# APIs para Compras
@bp.route('/api/compras/inventario-status')
@login_required
@estudiante_required
def api_inventario_status():
    """API: Estado del inventario para gr�ficos"""
    if not _role_allowed(current_user.rol, ['planeacion', 'compras', ROL_PLANEACION_COMPRAS]):
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
@rol_required('logistica')
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
    ordenes_hoy = [o for o in ordenes_transito if o.semana_entrega == simulacion.dia_actual]
    
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
    regiones = REGIONES_CANONICAS
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
@rol_required('logistica')
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
@rol_required('logistica')
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
        if simulacion.dia_actual < compra.semana_entrega:
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
            semana_simulacion=simulacion.dia_actual,
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
            semana_simulacion=simulacion.dia_actual,
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


@bp.route('/logistica/recibir-todas-ordenes', methods=['POST'])
@login_required
@estudiante_required
@rol_required('logistica')
def recibir_todas_ordenes_logistica():
    """Recibe todas las compras en tránsito que ya están listas para entrega."""
    try:
        simulacion = Simulacion.query.filter_by(activa=True).first()
        compras_listas = Compra.query.filter_by(
            empresa_id=current_user.empresa_id,
            estado='en_transito'
        ).filter(Compra.semana_entrega <= simulacion.dia_actual).order_by(Compra.semana_entrega.asc()).all()

        if not compras_listas:
            flash('No hay órdenes listas para recibir.', 'info')
            return redirect(url_for('estudiante.vista_recepcion'))

        recibidas = 0
        for compra in compras_listas:
            ok, _mensaje = _procesar_recepcion_compra_individual(compra, current_user.id, current_user.empresa_id)
            if ok:
                recibidas += 1

        flash(f'Se recibieron {recibidas} órdenes de compra de forma masiva.', 'success')
        return redirect(url_for('estudiante.vista_recepcion'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al recibir órdenes masivas: {str(e)}', 'error')
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
    ).filter(Venta.semana_simulacion > simulacion.dia_actual - 6)\
        .order_by(Venta.semana_simulacion.desc()).all()
    
    # An�lisis de demanda por regi�n
    regiones = REGIONES_CANONICAS
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
        
        # Restringir despacho al aprobado por Ventas en el día actual
        aprobado, ya_despachado, saldo = _saldo_despachable_por_ventas(
            current_user.empresa_id,
            simulacion.dia_actual,
            producto_id,
            region,
        )
        cantidad_int = int(round(cantidad or 0))
        if aprobado <= 0:
            flash(f'No hay venta aprobada para {region} en este producto.', 'error')
            return redirect(url_for('estudiante.vista_despacho'))
        if saldo <= 0:
            flash(f'Ya despachaste todo lo aprobado por Ventas para {region} ({aprobado} unds).', 'error')
            return redirect(url_for('estudiante.vista_despacho'))
        if cantidad_int > saldo:
            flash(
                f'Despacho excede lo aprobado por Ventas en {region}. '
                f'Aprobado: {aprobado}, ya despachado: {ya_despachado}, saldo: {saldo}.',
                'error'
            )
            return redirect(url_for('estudiante.vista_despacho'))

        # Calcular tiempo de entrega
        dias_entrega_region = calcular_tiempo_entrega_region(region)
        semana_entrega = simulacion.dia_actual + dias_entrega_region

        # Efecto disrupcion 3 (falla_flota): ajuste de costo y/o delay
        from utils.procesamiento_dias import obtener_efecto_logistico_empresa
        efecto_flota = obtener_efecto_logistico_empresa(simulacion.id, current_user.empresa_id)
        mult = 1.0
        delay_f = 0
        if efecto_flota:
            mult = efecto_flota.get('costo_multiplicador', 1.0)
            delay_f = efecto_flota.get('delay_semanas', 0)

        dias_entrega_efectivos = max(1, dias_entrega_region + delay_f)
        semana_entrega = simulacion.dia_actual + dias_entrega_efectivos
        codigos_disponibles = _codigos_propios_disponibles(simulacion, current_user.empresa_id)
        seleccion_vehiculos = seleccionar_vehiculos_optimos(cantidad, region, codigos_disponibles)

        costo_base_transporte = round(seleccion_vehiculos['costo_total'] * mult)

        vehiculos_asignados = seleccion_vehiculos['vehiculos']

        # Crear despacho
        despacho = DespachoRegional(
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            usuario_logistica_id=current_user.id,
            region=region,
            semana_despacho=simulacion.dia_actual,
            semana_entrega_estimado=semana_entrega,
            cantidad=cantidad,
            costo_transporte=costo_base_transporte,
            vehiculos_asignados=vehiculos_asignados,
            estado='en_transito'
        )
        
        # Actualizar inventario: el stock sale físicamente del almacén al despachar
        # NO se toca cantidad_reservada (eso es para stock prometido que aún no salió)
        inventario.cantidad_actual = max(0, int(round((inventario.cantidad_actual or 0) - cantidad)))
        
        # Registrar movimiento
        movimiento = MovimientoInventario(
            empresa_id=current_user.empresa_id,
            producto_id=producto_id,
            usuario_id=current_user.id,
            semana_simulacion=simulacion.dia_actual,
            tipo_movimiento='salida_despacho',
            cantidad=cantidad,
            saldo_anterior=inventario.cantidad_actual + cantidad,
            saldo_nuevo=inventario.cantidad_actual,
            observaciones=f"Despacho a regi�n {region}"
        )
        
        if 'V_EXTERNO' in vehiculos_asignados:
            despacho.costo_unitario_externo = 3000.0

        db.session.add(despacho)
        db.session.add(movimiento)
        db.session.flush()
        
        # Vincular movimiento con despacho
        movimiento.despacho_id = despacho.id
        # Registrar uso de vehículos propios hasta su día de retorno
        dia_retorno = simulacion.dia_actual + obtener_ciclo_region(region)
        for codigo_vehiculo in vehiculos_asignados:
            if codigo_vehiculo == 'V_EXTERNO':
                continue
            ocupacion_vigente = _vehiculo_ocupado_por_ciclo(
                current_user.empresa_id,
                codigo_vehiculo,
                simulacion.dia_actual,
            )
            if ocupacion_vigente:
                flash(
                    f'El vehículo {codigo_vehiculo} está fuera de servicio por ciclo. '
                    f'Disponible desde el día {int(ocupacion_vigente) + 1}.',
                    'error'
                )
                db.session.rollback()
                return redirect(url_for('estudiante.vista_despacho'))
            uso = DisponibilidadVehiculo(
                empresa_id=current_user.empresa_id,
                vehiculo_id=codigo_vehiculo,
                dia_disponible_retorno=dia_retorno,
            )
            db.session.add(uso)

        # Restar costo de transporte del capital
        empresa = current_user.empresa
        empresa.capital_actual = max(0, float(empresa.capital_actual or 0) - costo_base_transporte)
        
        # Registrar decisi�n
        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=current_user.empresa_id,
            semana_simulacion=simulacion.dia_actual,
            tipo_decision='despacho_regional',
            datos_decision={
                'producto_id': producto_id,
                'region': region,
                'cantidad': cantidad,
                'semana_entrega': semana_entrega,
                'costo_transporte': costo_base_transporte
            }
        )
        
        db.session.add(decision)
        db.session.commit()
        
        if validacion.get('alerta_stock_bajo'):
            flash(f'Despacho creado. {validacion["recomendacion"]}', 'warning')
        else:
            flash(f"Despacho a {region} creado exitosamente. Vehículos: {len(vehiculos_asignados)}. Costo: ${costo_base_transporte:,.0f}", "success")
        
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
        semana_simulacion=simulacion.dia_actual,
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
        semana_pronostico = simulacion.dia_actual + i + 1
        
        pronostico = Pronostico(
            usuario_id=current_user.id,
            empresa_id=empresa.id,
            producto_id=producto_id,
            semana_generacion=simulacion.dia_actual,
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
            Pronostico.semana_pronostico > simulacion.dia_actual,
            Pronostico.semana_pronostico <= simulacion.dia_actual + 7
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
        semana_generacion=simulacion.dia_actual,
        semana_necesidad=simulacion.dia_actual + producto.tiempo_entrega,
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
        semana_simulacion=simulacion.dia_actual,
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
                semana_generacion=simulacion.dia_actual,
                semana_necesidad=simulacion.dia_actual + producto.tiempo_entrega,
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
                semana_simulacion=simulacion.dia_actual,
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
@rol_required('logistica')
def api_logistica_stock():
    """Obtener stock disponible para despachos"""
    empresa = current_user.empresa
    simulacion = Simulacion.query.filter_by(activa=True).first()
    
    inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
    
    stock_data = []
    stock_total = 0
    stock_maximo_total = 0
    sobrestock_total = 0
    costo_sobrestock_total = 0
    valor_inventario_costo_referencia = 0.0
    valor_inventario_costo_pagado = 0.0

    for inv in inventarios:
        stock_actual = int(round(inv.cantidad_actual or 0))
        stock_seguridad = int(round(inv.stock_seguridad or 0))
        stock_maximo = int(round(inv.producto.stock_maximo or 0)) if inv.producto else 0
        costo_referencia = inv.costo_promedio or (inv.producto.costo_unitario if inv.producto else 0)
        costo_producto_referencia = inv.producto.costo_unitario if inv.producto else costo_referencia
        sobrestock = max(0, stock_actual - stock_maximo)

        stock_total += stock_actual
        stock_maximo_total += stock_maximo
        sobrestock_total += sobrestock
        costo_sobrestock_total += sobrestock * costo_referencia
        valor_inventario_costo_referencia += stock_actual * float(costo_producto_referencia or 0)
        valor_inventario_costo_pagado += stock_actual * float(costo_referencia or 0)

        stock_data.append({
            'producto_id': inv.producto_id,
            'producto_nombre': inv.producto.nombre,
            'stock_actual': stock_actual,
            'stock_seguridad': stock_seguridad,
            'stock_maximo': stock_maximo,
            'sobrestock': sobrestock,
            'costo_referencia': round(costo_referencia, 2),
            'costo_sobrestock': round(sobrestock * costo_referencia, 2)
        })

    periodo_dias = 30
    ventas_mensuales_costo = 0.0
    if simulacion:
        dia_fin = simulacion.dia_actual
        dia_inicio = max(1, dia_fin - (periodo_dias - 1))

        ventas_periodo = Venta.query.filter(
            Venta.empresa_id == empresa.id,
            Venta.semana_simulacion >= dia_inicio,
            Venta.semana_simulacion <= dia_fin,
        ).all()

        ventas_mensuales_costo = sum(
            float(v.cantidad_vendida or 0) * float(v.costo_unitario or 0)
            for v in ventas_periodo
        )

    # Indicadores en días según fórmula: (Inventario promedio mensual al costo / Ventas mensuales al costo) * 30
    # Se usa el inventario actual como proxy del inventario promedio mensual por no existir snapshot diario histórico.
    if ventas_mensuales_costo > 0:
        rotacion_total_dias = (valor_inventario_costo_referencia / ventas_mensuales_costo) * periodo_dias
        rotacion_neta_dias = (valor_inventario_costo_pagado / ventas_mensuales_costo) * periodo_dias
    else:
        rotacion_total_dias = None
        rotacion_neta_dias = None
    
    return jsonify({
        'success': True,
        'stock': stock_data,
        'resumen': {
            'stock_total': stock_total,
            'stock_maximo_total': stock_maximo_total,
            'sobrestock_total': sobrestock_total,
            'costo_sobrestock_total': round(costo_sobrestock_total, 2),
            'indicadores_rotacion': {
                'periodo_dias': periodo_dias,
                'inventario_promedio_mensual_costo_total': round(valor_inventario_costo_referencia, 2),
                'inventario_promedio_mensual_costo_pagado': round(valor_inventario_costo_pagado, 2),
                'ventas_mensuales_costo': round(ventas_mensuales_costo, 2),
                'rotacion_total_dias': round(rotacion_total_dias, 2) if rotacion_total_dias is not None else None,
                'rotacion_neta_dias': round(rotacion_neta_dias, 2) if rotacion_neta_dias is not None else None,
            }
        }
    })


@bp.route('/api/logistica/pedidos-dia')
@login_required
@estudiante_required
@rol_required('logistica')
def api_logistica_pedidos_dia():
    """Retorna pedidos del día agrupados por región según aprobaciones de Ventas."""
    empresa = current_user.empresa
    simulacion = Simulacion.query.filter_by(activa=True).first()

    if not simulacion:
        return jsonify({'success': False, 'message': 'No hay simulación activa'}), 400

    aprobaciones = _obtener_aprobaciones_ventas_dia(empresa.id, simulacion.dia_actual)
    producto_ids = sorted({pid for (pid, _region) in aprobaciones.keys()})
    productos = Producto.query.filter(Producto.id.in_(producto_ids)).all() if producto_ids else []
    productos_map = {p.id: p for p in productos}

    pedidos_region = {}
    for (producto_id, region), cantidad_aprobada in aprobaciones.items():
        cantidad_aprobada = int(round(cantidad_aprobada or 0))
        if cantidad_aprobada <= 0:
            continue
        region_info = pedidos_region.setdefault(region, {
            'region': region,
            'unidades_solicitadas': 0,
            'detalle_productos': [],
        })
        producto = productos_map.get(producto_id)
        region_info['unidades_solicitadas'] += cantidad_aprobada
        region_info['detalle_productos'].append({
            'producto_id': producto_id,
            'producto_nombre': producto.nombre if producto else f'Producto {producto_id}',
            'unidades_solicitadas': cantidad_aprobada,
        })

    pedidos = []
    for region in REGIONES_CANONICAS:
        if region in pedidos_region:
            info = pedidos_region[region]
            info['detalle_productos'] = sorted(
                info['detalle_productos'],
                key=lambda item: item['producto_nombre']
            )
            pedidos.append(info)

    catalogo_vehiculos = _obtener_capacidades_vehiculos(simulacion, empresa.id)

    return jsonify({
        'success': True,
        'dia_actual': simulacion.dia_actual,
        'pedidos': pedidos,
        'vehiculos': _serializar_vehiculos(catalogo_vehiculos),
        'falla_flota_activa': _disrupcion_falla_flota_activa(simulacion, empresa.id),
        'falla_flota_opcion': _opcion_falla_flota(simulacion, empresa.id),
    })


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

    # Restringir despacho al aprobado por Ventas en el día actual
    aprobado, ya_despachado, saldo = _saldo_despachable_por_ventas(
        empresa.id,
        simulacion.dia_actual,
        producto_id,
        region,
    )
    cantidad_int = int(round(float(cantidad or 0)))
    if aprobado <= 0:
        return jsonify({
            'success': False,
            'message': f'No hay venta aprobada para {region} en este producto.'
        }), 400
    if saldo <= 0:
        return jsonify({
            'success': False,
            'message': f'Ya despachaste todo lo aprobado por Ventas para {region} ({aprobado} unds).'
        }), 400
    if cantidad_int > saldo:
        return jsonify({
            'success': False,
            'message': (
                f'Despacho excede lo aprobado por Ventas en {region}. '
                f'Aprobado: {aprobado}, ya despachado: {ya_despachado}, saldo: {saldo}.'
            )
        }), 400
    
    # Calcular tiempo de entrega segun region
    dias_entrega_region = calcular_tiempo_entrega_region(region)
    dia_llegada = simulacion.dia_actual + dias_entrega_region

    # Efecto disrupcion 3 (falla_flota)
    from utils.procesamiento_dias import obtener_efecto_logistico_empresa
    efecto_flota = obtener_efecto_logistico_empresa(simulacion.id, empresa.id)
    mult = 1.0
    delay_f = 0
    if efecto_flota:
        mult = efecto_flota.get('costo_multiplicador', 1.0)
        delay_f = efecto_flota.get('delay_semanas', 0)

    dias_entrega_efectivos = max(1, dias_entrega_region + delay_f)
    dia_llegada = simulacion.dia_actual + dias_entrega_efectivos
    codigos_disponibles = _codigos_propios_disponibles(simulacion, empresa.id)
    seleccion_vehiculos = seleccionar_vehiculos_optimos(cantidad, region, codigos_disponibles)

    costo_base_transporte = round(seleccion_vehiculos['costo_total'] * mult)

    vehiculos_asignados = seleccion_vehiculos['vehiculos']

    # Crear despacho
    despacho = DespachoRegional(
        empresa_id=empresa.id,
        producto_id=producto_id,
        region=region,
        cantidad=cantidad,
        semana_despacho=simulacion.dia_actual,
        semana_entrega_estimado=dia_llegada,
        costo_transporte=costo_base_transporte,
        vehiculos_asignados=vehiculos_asignados,
        estado='en_transito',
        usuario_logistica_id=current_user.id
    )
    
    # Actualizar inventario
    saldo_anterior = int(round(inventario.cantidad_actual or 0))
    inventario.cantidad_actual = max(0, int(round((inventario.cantidad_actual or 0) - cantidad)))
    saldo_nuevo = int(round(inventario.cantidad_actual or 0))
    
    # Registrar movimiento
    movimiento = MovimientoInventario(
        empresa_id=empresa.id,
        producto_id=producto_id,
        tipo_movimiento='salida_despacho',
        cantidad=cantidad,
        semana_simulacion=simulacion.dia_actual,
        saldo_anterior=saldo_anterior,
        saldo_nuevo=saldo_nuevo,
        observaciones=f'Despacho a {region}',
        usuario_id=current_user.id
    )
    
    # Registrar decisi�n
    decision = Decision(
        usuario_id=current_user.id,
        empresa_id=empresa.id,
        tipo_decision='despacho_regional',
        semana_simulacion=simulacion.dia_actual,
        datos_decision={
            'producto_id': producto_id,
            'producto_nombre': producto.nombre,
            'cantidad': cantidad,
            'region': region,
            'dia_llegada': dia_llegada,
            'descripcion': f'Despacho de {cantidad} unidades de {producto.nombre} a {region}'
        }
    )
    
    if 'V_EXTERNO' in vehiculos_asignados:
        despacho.costo_unitario_externo = 3000.0

    # Restar costo de transporte del capital
    empresa.capital_actual = max(0, float(empresa.capital_actual or 0) - costo_base_transporte)

    dia_retorno = simulacion.dia_actual + obtener_ciclo_region(region)
    for codigo_vehiculo in vehiculos_asignados:
        if codigo_vehiculo == 'V_EXTERNO':
            continue
        ocupacion_vigente = _vehiculo_ocupado_por_ciclo(
            empresa.id,
            codigo_vehiculo,
            simulacion.dia_actual,
        )
        if ocupacion_vigente:
            return jsonify({
                'success': False,
                'message': (
                    f'El vehículo {codigo_vehiculo} está fuera de servicio por ciclo. '
                    f'Disponible desde el día {int(ocupacion_vigente) + 1}.'
                )
            }), 400
        uso = DisponibilidadVehiculo(
            empresa_id=empresa.id,
            vehiculo_id=codigo_vehiculo,
            dia_disponible_retorno=dia_retorno,
        )
        db.session.add(uso)
    db.session.add(despacho)
    db.session.add(movimiento)
    db.session.add(decision)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Despacho creado: {cantidad} unidades a {region}, costo transporte: ${costo_base_transporte:,.0f}'
    })


@bp.route('/api/logistica/despachar-multiple', methods=['POST'])
@login_required
@estudiante_required
@rol_required('logistica')
def api_logistica_despachar_multiple():
    """Guarda asignaciones diarias de logística por vehículo para todos los pedidos."""
    try:
        data = request.get_json()
        asignaciones = data.get('asignaciones', [])

        if not asignaciones:
            return jsonify({
                'success': False,
                'message': 'No se recibieron asignaciones para procesar.'
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

        decision_existente = Decision.query.filter_by(
            empresa_id=empresa.id,
            tipo_decision='logistica_asignacion_vehiculos',
            semana_simulacion=simulacion.dia_actual,
        ).first()
        if decision_existente:
            return jsonify({
                'success': False,
                'message': 'Las asignaciones logísticas de este día ya fueron registradas.'
            }), 400

        aprobaciones = _obtener_aprobaciones_ventas_dia(empresa.id, simulacion.dia_actual)
        demanda_por_region = {}
        demanda_por_producto_region = {}
        for (producto_id, region), cantidad_aprobada in aprobaciones.items():
            cantidad = int(round(cantidad_aprobada or 0))
            if cantidad <= 0:
                continue
            demanda_por_region[region] = demanda_por_region.get(region, 0) + cantidad
            demanda_por_producto_region[(producto_id, region)] = cantidad

        if not demanda_por_region:
            return jsonify({
                'success': False,
                'message': 'No hay aprobaciones de Ventas para el día actual.'
            }), 400

        vehiculos_catalogo = _obtener_capacidades_vehiculos(simulacion, empresa.id)
        from utils.procesamiento_dias import obtener_efecto_logistico_empresa
        efecto_flota = obtener_efecto_logistico_empresa(simulacion.id, empresa.id)
        opcion_falla_flota = _opcion_falla_flota(simulacion, empresa.id)
        uso_por_vehiculo = {codigo: 0 for codigo in vehiculos_catalogo.keys()}
        vehiculos_usados = set()
        regiones_enviadas = set()
        total_por_producto = {}

        for item in asignaciones:
            region = item.get('region')
            # Soportar array de vehículos o vehículo singular (compatibilidad hacia atrás)
            vehiculos_item = item.get('vehiculos', [])
            if isinstance(vehiculos_item, str):
                vehiculos_item = [vehiculos_item]
            if not vehiculos_item and item.get('vehiculo'):
                vehiculos_item = [item.get('vehiculo')]
            vehiculos_item = [v.strip().upper() for v in vehiculos_item if v]
            
            solicitadas = int(item.get('unidades_solicitadas', 0))
            enviar = int(item.get('unidades_enviar', 0))

            if region not in demanda_por_region:
                return jsonify({
                    'success': False,
                    'message': f'Asignación inválida para región {region}.'
                }), 400

            demanda_real = demanda_por_region[region]
            if solicitadas <= 0:
                return jsonify({
                    'success': False,
                    'message': f'Debes definir una cantidad mayor a cero para {region}.'
                }), 400

            if solicitadas != demanda_real:
                return jsonify({
                    'success': False,
                    'message': (
                        f'La asignación de {region} debe coincidir con Ventas '
                        f'({demanda_real} unidades aprobadas).'
                    )
                }), 400

            if enviar != demanda_real:
                return jsonify({
                    'success': False,
                    'message': (
                        f'El despacho de {region} debe ser exactamente {demanda_real} '
                        'unidades aprobadas por Ventas.'
                    )
                }), 400

            # Validar que se hayan asignado vehículos
            if not vehiculos_item:
                return jsonify({
                    'success': False,
                    'message': f'Debes asignar al menos un vehículo para {region}.'
                }), 400

            # Validar cada vehículo
            capacidad_total = 0
            usa_externo = False
            for vehiculo in vehiculos_item:
                if vehiculo not in vehiculos_catalogo:
                    return jsonify({
                        'success': False,
                        'message': f'Vehículo {vehiculo} no válido.'
                    }), 400

                if vehiculo == 'EXTERNO':
                    usa_externo = True
                    continue

                if vehiculo in vehiculos_usados:
                    return jsonify({
                        'success': False,
                        'message': f'El vehículo {vehiculo} ya fue asignado a otra región.'
                    }), 400

                if opcion_falla_flota == 'B' and usa_externo:
                    return jsonify({
                        'success': False,
                        'message': 'Con la opción B de falla de flota, no se permite usar vehículo externo.'
                    }), 400

                conf_vehiculo = vehiculos_catalogo[vehiculo]
                if not conf_vehiculo['disponible']:
                    dia_retorno = conf_vehiculo.get('dia_retorno')
                    if dia_retorno:
                        return jsonify({
                            'success': False,
                            'message': f'El {conf_vehiculo["nombre"]} está ocupado por ciclo de transporte. Disponible a partir del día {dia_retorno}.'
                        }), 400
                    else:
                        return jsonify({
                            'success': False,
                            'message': f'El {conf_vehiculo["nombre"]} está fuera de operación por disrupción activa.'
                        }), 400

                # Validación dura en BD: si está ocupado por ciclo hoy, no se puede reasignar.
                ocupacion_vigente = db.session.query(
                    db.func.max(DisponibilidadVehiculo.dia_disponible_retorno)
                ).filter(
                    DisponibilidadVehiculo.empresa_id == empresa.id,
                    DisponibilidadVehiculo.vehiculo_id == vehiculo,
                    DisponibilidadVehiculo.dia_disponible_retorno >= simulacion.dia_actual,
                ).scalar()
                if ocupacion_vigente:
                    return jsonify({
                        'success': False,
                        'message': (
                            f'El vehículo {vehiculo} está fuera de servicio por ciclo de transporte. '
                            f'Disponible desde el día {int(ocupacion_vigente) + 1}.'
                        )
                    }), 400
                
                vehiculos_usados.add(vehiculo)
                capacidad_total += int(conf_vehiculo.get('capacidad') or 0)

            regiones_enviadas.add(region)

        faltantes = [
            region for region in demanda_por_region.keys()
            if region not in regiones_enviadas
        ]
        if faltantes:
            return jsonify({
                'success': False,
                'message': 'Debes asignar vehículo y envío para todos los pedidos del día.'
            }), 400

        # Validación por producto: el stock debe alcanzar para cumplir todo el día.
        inventarios = Inventario.query.filter_by(empresa_id=empresa.id).all()
        inventario_map = {inv.producto_id: inv for inv in inventarios}
        productos = Producto.query.filter(Producto.id.in_([pid for (pid, _r) in demanda_por_producto_region.keys()])).all()
        productos_map = {p.id: p for p in productos}

        for (producto_id, region), cantidad in demanda_por_producto_region.items():
            inventario = inventario_map.get(producto_id)
            if not inventario or int(round(inventario.cantidad_actual or 0)) < cantidad:
                producto = Producto.query.get(producto_id)
                nombre = producto.nombre if producto else f'Producto {producto_id}'
                return jsonify({
                    'success': False,
                    'message': f'Stock insuficiente para {nombre} en {region}.'
                }), 400

        # Una asignación por región puede contener varias referencias. Se registran internamente.
        detalle_despachos = []
        movimientos_por_producto = {}
        vehiculos_bloqueados_dia = set()
        costo_total_logistica = 0.0  # Acumular costos de transporte para restar del capital

        for item in asignaciones:
            region = item.get('region')
            # Soportar array de vehículos o vehículo singular (compatibilidad hacia atrás)
            vehiculos_item = item.get('vehiculos', [])
            if isinstance(vehiculos_item, str):
                vehiculos_item = [vehiculos_item]
            if not vehiculos_item and item.get('vehiculo'):
                vehiculos_item = [item.get('vehiculo')]
            vehiculos_item = [v.strip().upper() for v in vehiculos_item if v]
            
            cantidad_total_region = int(item.get('unidades_enviar', 0))
            solicitadas = int(item.get('unidades_solicitadas', 0))

            if region not in demanda_por_region:
                continue

            demandas_region = [
                {
                    'producto_id': pid,
                    'cantidad': cant,
                }
                for (pid, reg), cant in demanda_por_producto_region.items()
                if reg == region and int(round(cant or 0)) > 0
            ]
            dias_entrega_region = calcular_tiempo_entrega_region(region)
            vehiculos_propios_region = []
            cargas_por_vehiculo = {}
            capacidad_total_propios = 0
            unidades_externo_region = 0

            # Procesar múltiples vehículos seleccionados para esta región
            for vehiculo in vehiculos_item:
                if vehiculo == 'EXTERNO':
                    unidades_externo_region = cantidad_total_region
                else:
                    if vehiculo in vehiculos_bloqueados_dia:
                        return jsonify({
                            'success': False,
                            'message': f'El vehículo {vehiculo} ya fue consumido en otra asignación del día.'
                        }), 400

                    vehiculos_propios_region.append(vehiculo)
                    vehiculos_bloqueados_dia.add(vehiculo)
                    capacidad_vehiculo = int((vehiculos_catalogo.get(vehiculo, {}) or {}).get('capacidad') or 0)
                    capacidad_total_propios += capacidad_vehiculo

            # Calcular cuánto transporta cada tipo de vehículo
            if vehiculos_propios_region:
                unidades_principal_region = min(cantidad_total_region, capacidad_total_propios)
                unidades_externo_region = max(0, cantidad_total_region - unidades_principal_region)
            else:
                unidades_principal_region = 0
                unidades_externo_region = cantidad_total_region

            restante_por_asignar = unidades_principal_region
            for codigo_prop in vehiculos_propios_region:
                capacidad_prop = int((vehiculos_catalogo.get(codigo_prop, {}) or {}).get('capacidad') or 0)
                if capacidad_prop <= 0 or restante_por_asignar <= 0:
                    cargas_por_vehiculo[codigo_prop] = 0
                    continue
                carga = min(capacidad_prop, restante_por_asignar)
                cargas_por_vehiculo[codigo_prop] = carga
                uso_por_vehiculo[codigo_prop] = uso_por_vehiculo.get(codigo_prop, 0) + carga
                restante_por_asignar -= carga

            costo_base_vehiculo_region = 0.0
            for codigo_prop in vehiculos_propios_region:
                costo_base_vehiculo_region += float(FLOTA_VEHICULOS.get(codigo_prop, {}).get('costo', 0))

            if opcion_falla_flota == 'B' and unidades_externo_region > 0:
                return jsonify({
                    'success': False,
                    'message': (
                        f'La región {region} excede la capacidad interna del vehículo asignado. '
                        'Con opción B no se permite transporte externo.'
                    )
                }), 400

            delay_f = 0
            mult = 1.0
            if efecto_flota:
                mult = efecto_flota.get('costo_multiplicador', 1.0)
                delay_f = efecto_flota.get('delay_semanas', 0)

            dias_entrega_efectivos = max(1, dias_entrega_region + delay_f)
            dia_llegada = simulacion.dia_actual + dias_entrega_efectivos

            # Bloquear vehículos propios usados hasta su retorno según ciclo de región.
            for codigo_prop in vehiculos_propios_region:
                uso_vehiculo = DisponibilidadVehiculo(
                    empresa_id=empresa.id,
                    vehiculo_id=codigo_prop,
                    dia_disponible_retorno=simulacion.dia_actual + obtener_ciclo_region(region),
                )
                db.session.add(uso_vehiculo)

            restante_externo = unidades_externo_region
            restante_principal = unidades_principal_region
            restante_costo_fijo_region = costo_base_vehiculo_region
            restante_costo_externo_region = float(unidades_externo_region * 3000)

            for idx, demanda in enumerate(demandas_region):
                cantidad = int(round(demanda.get('cantidad') or 0))
                if cantidad <= 0:
                    continue
                producto_id = int(demanda.get('producto_id'))
                producto = productos_map.get(producto_id)

                if cantidad_total_region > 0:
                    if idx == len(demandas_region) - 1:
                        cantidad_externa = restante_externo
                        cantidad_principal = cantidad - cantidad_externa
                    else:
                        cantidad_externa = int(round(cantidad * (unidades_externo_region / cantidad_total_region))) if unidades_externo_region > 0 else 0
                        cantidad_externa = min(cantidad_externa, restante_externo)
                        cantidad_principal = cantidad - cantidad_externa
                        cantidad_principal = min(cantidad_principal, restante_principal)
                        cantidad_externa = cantidad - cantidad_principal
                    restante_externo -= cantidad_externa
                    restante_principal -= cantidad_principal
                else:
                    cantidad_principal = cantidad
                    cantidad_externa = 0

                if unidades_externo_region > 0 and cantidad_principal <= 0:
                    costo_t = round(cantidad * 3000 * mult)
                else:
                    if idx == len(demandas_region) - 1:
                        costo_fijo_item = restante_costo_fijo_region
                        costo_externo_item = restante_costo_externo_region
                    else:
                        proporcion = (cantidad / cantidad_total_region) if cantidad_total_region > 0 else 0
                        costo_fijo_item = round(costo_base_vehiculo_region * proporcion, 2)
                        costo_externo_item = round((unidades_externo_region * 3000) * proporcion, 2)
                        costo_fijo_item = min(costo_fijo_item, restante_costo_fijo_region)
                        costo_externo_item = min(costo_externo_item, restante_costo_externo_region)

                    restante_costo_fijo_region -= costo_fijo_item
                    restante_costo_externo_region -= costo_externo_item
                    costo_t = round((costo_fijo_item + costo_externo_item) * mult)

                despacho = DespachoRegional(
                    empresa_id=empresa.id,
                    producto_id=producto_id,
                    region=region,
                    cantidad=cantidad,
                    semana_despacho=simulacion.dia_actual,
                    semana_entrega_estimado=dia_llegada,
                    costo_transporte=costo_t,
                    vehiculos_asignados=(vehiculos_propios_region + (['V_EXTERNO'] if unidades_externo_region > 0 else [])),
                    estado='en_transito',
                    usuario_logistica_id=current_user.id,
                    ventas_asociadas={
                        'vehiculos': vehiculos_propios_region,
                        'vehiculos_propios': vehiculos_propios_region,
                        'cargas_por_vehiculo': cargas_por_vehiculo,
                        'vehiculo_externo': 'EXTERNO' if cantidad_externa > 0 else None,
                        'region_total': cantidad_total_region,
                        'cantidad_principal': cantidad_principal,
                        'cantidad_externa': cantidad_externa,
                        'unidades_solicitadas': solicitadas,
                    },
                    observaciones=f'Asignación logística día {simulacion.dia_actual}. Región: {region}. Vehículos: {", ".join(vehiculos_propios_region)}.'
                )
                if cantidad_externa > 0:
                    despacho.costo_unitario_externo = 3000.0
                db.session.add(despacho)
                
                # Acumular costo de transporte
                costo_total_logistica += costo_t

                detalle_despachos.append({
                    'producto_id': producto_id,
                    'producto_nombre': producto.nombre if producto else f'Producto {producto_id}',
                    'region': region,
                    'vehiculos': vehiculos_propios_region,
                    'vehiculo_externo': 'EXTERNO' if cantidad_externa > 0 else None,
                    'cantidad': cantidad,
                    'cantidad_principal': cantidad_principal,
                    'cantidad_externa': cantidad_externa,
                    'dia_llegada': dia_llegada,
                })

                movimientos_por_producto[producto_id] = movimientos_por_producto.get(producto_id, 0) + cantidad

        for producto_id, total_cantidad in movimientos_por_producto.items():
            inventario = inventario_map.get(producto_id)
            saldo_anterior = int(round(inventario.cantidad_actual or 0))
            inventario.cantidad_actual = max(0, saldo_anterior - total_cantidad)
            saldo_nuevo = int(round(inventario.cantidad_actual or 0))

            movimiento = MovimientoInventario(
                empresa_id=empresa.id,
                producto_id=producto_id,
                tipo_movimiento='salida_despacho',
                cantidad=total_cantidad,
                saldo_anterior=saldo_anterior,
                saldo_nuevo=saldo_nuevo,
                semana_simulacion=simulacion.dia_actual,
                observaciones='Despacho diario por asignación de vehículos',
                usuario_id=current_user.id
            )
            db.session.add(movimiento)

        cantidad_total = sum(d['cantidad'] for d in detalle_despachos)
        
        # Restar costo total de transporte del capital de la empresa
        empresa.capital_actual = max(0, float(empresa.capital_actual or 0) - costo_total_logistica)

        decision = Decision(
            usuario_id=current_user.id,
            empresa_id=empresa.id,
            tipo_decision='logistica_asignacion_vehiculos',
            semana_simulacion=simulacion.dia_actual,
            datos_decision={
                'cantidad_total': cantidad_total,
                'costo_total_transporte': round(costo_total_logistica, 2),
                'despachos': detalle_despachos,
                'uso_vehiculos': uso_por_vehiculo,
                'descripcion': f'Asignación logística diaria: {len(detalle_despachos)} envíos, {cantidad_total} unidades, costo transporte ${costo_total_logistica:,.0f}'
            }
        )

        db.session.add(decision)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Asignación guardada: {len(detalle_despachos)} despachos creados.',
            'despachos_creados': len(detalle_despachos),
            'cantidad_total': cantidad_total,
            'despachos': detalle_despachos,
            'uso_vehiculos': uso_por_vehiculo,
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
@rol_required('logistica')
def api_logistica_transito():
    """Obtener compras y despachos en tr�nsito"""
    empresa = current_user.empresa
    simulacion = Simulacion.query.filter_by(activa=True).first()
    if not simulacion:
        return jsonify({'success': False, 'message': 'No hay simulación activa'}), 400
    
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
            'semana_orden': compra.semana_orden,
            'semana_entrega': compra.semana_entrega,
            'lista_para_recibir': compra.semana_entrega <= simulacion.dia_actual,
        })
    
    # Despachos en tr�nsito
    despachos = DespachoRegional.query.filter_by(
        empresa_id=empresa.id,
        estado='en_transito'
    ).order_by(DespachoRegional.semana_entrega_estimado).all()
    
    despachos_data = []
    for despacho in despachos:
        vehiculo = 'N/A'
        if isinstance(despacho.ventas_asociadas, dict):
            vehiculo = despacho.ventas_asociadas.get('vehiculo', vehiculo)

        despachos_data.append({
            'id': despacho.id,
            'producto_id': despacho.producto_id,
            'producto_nombre': despacho.producto.nombre,
            'cantidad': despacho.cantidad,
            'region_destino': despacho.region,
            'dia_llegada': despacho.semana_entrega_estimado,
            'semana_llegada': despacho.semana_entrega_estimado,
            'vehiculo': vehiculo,
        })
    
    return jsonify({
        'success': True,
        'compras': compras_data,
        'despachos': despachos_data
    })


@bp.route('/api/logistica/fill-rate-region')
@login_required
@estudiante_required
@rol_required('logistica')
def api_logistica_fill_rate_region():
    """API: Fill rate (nivel de servicio) acumulado desde el día 1 por región"""
    empresa_id = current_user.empresa_id
    simulacion = Simulacion.query.filter_by(activa=True).first()
    if not simulacion:
        return jsonify({'error': 'No hay simulación activa'}), 404

    regiones = REGIONES_CANONICAS
    fill_rates = []
    ventas_totales = []
    ventas_perdidas = []

    for region in regiones:
        ventas_region = Venta.query.filter_by(
            empresa_id=empresa_id,
            region=region
        ).filter(
            Venta.semana_simulacion >= 1,
            Venta.semana_simulacion <= simulacion.dia_actual,
        ).all()
        total_solicitado = sum(v.cantidad_solicitada for v in ventas_region)
        total_vendido = sum(v.cantidad_vendida for v in ventas_region)
        total_perdido = sum(v.cantidad_perdida for v in ventas_region)
        fill_rate = round(total_vendido / total_solicitado * 100, 1) if total_solicitado > 0 else 100.0
        fill_rates.append(fill_rate)
        ventas_totales.append(round(total_vendido))
        ventas_perdidas.append(round(total_perdido))

    return jsonify({
        'regiones': regiones,
        'fill_rates': fill_rates,
        'ventas_totales': ventas_totales,
        'ventas_perdidas': ventas_perdidas
    })
