"""
Modelos de base de datos para la simulación de cadena de abastecimiento
"""

from flask_login import UserMixin
from datetime import datetime
from extensions import db

class Usuario(UserMixin, db.Model):
    """Modelo de usuario - Profesores y Estudiantes"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # admin, ventas, planeacion, compras, logistica
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    nombre_completo = db.Column(db.String(100))
    email = db.Column(db.String(120))
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    empresa = db.relationship('Empresa', backref='estudiantes')
    decisiones = db.relationship('Decision', backref='usuario', lazy=True)
    
    def __repr__(self):
        return f'<Usuario {self.username} - {self.rol}>'


class Empresa(db.Model):
    """Modelo de empresa - Cada equipo de estudiantes representa una empresa"""
    __tablename__ = 'empresas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    capital_inicial = db.Column(db.Float, default=1000000.0)
    capital_actual = db.Column(db.Float, default=1000000.0)
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    inventarios = db.relationship('Inventario', backref='empresa', lazy=True)
    ventas = db.relationship('Venta', backref='empresa', lazy=True)
    compras = db.relationship('Compra', backref='empresa', lazy=True)
    
    def __repr__(self):
        return f'<Empresa {self.nombre}>'


class Simulacion(db.Model):
    """Modelo de simulación - Controla el estado global del juego"""
    __tablename__ = 'simulacion'
    
    id = db.Column(db.Integer, primary_key=True)
    dia_actual = db.Column(db.Integer, default=1)
    estado = db.Column(db.String(20), default='pausado')  # pausado, en_curso, finalizado
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
    duracion_dias = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Simulacion Día {self.dia_actual} - {self.estado}>'


class Producto(db.Model):
    """Modelo de producto - Catálogo de productos disponibles"""
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50))
    precio_base = db.Column(db.Float, nullable=False)
    precio_actual = db.Column(db.Float, nullable=False)  # Precio que puede modificar Ventas
    precio_sugerido = db.Column(db.Float, nullable=False)  # Precio recomendado por el sistema
    costo_unitario = db.Column(db.Float, nullable=False)
    demanda_promedio = db.Column(db.Float, default=100)
    desviacion_demanda = db.Column(db.Float, default=20)
    elasticidad_precio = db.Column(db.Float, default=1.5)  # Factor de sensibilidad al precio
    tiempo_entrega = db.Column(db.Integer, default=3)  # días
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    inventarios = db.relationship('Inventario', backref='producto', lazy=True)
    
    def __repr__(self):
        return f'<Producto {self.codigo} - {self.nombre}>'


class Inventario(db.Model):
    """Modelo de inventario - Stock actual por empresa y producto"""
    __tablename__ = 'inventarios'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad_actual = db.Column(db.Float, default=0)
    cantidad_reservada = db.Column(db.Float, default=0)
    punto_reorden = db.Column(db.Float, default=50)
    stock_seguridad = db.Column(db.Float, default=20)
    costo_promedio = db.Column(db.Float, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Inventario Empresa {self.empresa_id} - Producto {self.producto_id}>'


class Venta(db.Model):
    """Modelo de ventas - Registro de ventas por día"""
    __tablename__ = 'ventas'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    dia_simulacion = db.Column(db.Integer, nullable=False)
    region = db.Column(db.String(50))  # Caribe, Pacifica, Orinoquia, Amazonia, Andina
    canal = db.Column(db.String(50), default='retail')  # retail, mayorista, distribuidor
    cantidad_solicitada = db.Column(db.Float, nullable=False)
    cantidad_vendida = db.Column(db.Float, nullable=False)
    cantidad_perdida = db.Column(db.Float, default=0)  # ventas perdidas por falta de stock
    precio_unitario = db.Column(db.Float, nullable=False)
    ingreso_total = db.Column(db.Float, nullable=False)
    costo_unitario = db.Column(db.Float, default=0)  # Para calcular margen
    margen = db.Column(db.Float, default=0)  # Margen de ganancia
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    producto = db.relationship('Producto', backref='ventas')
    
    def __repr__(self):
        return f'<Venta Día {self.dia_simulacion} - Empresa {self.empresa_id} - {self.region}>'


class Compra(db.Model):
    """Modelo de compras - Órdenes de compra a proveedores"""
    __tablename__ = 'compras'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    dia_orden = db.Column(db.Integer, nullable=False)
    dia_entrega = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    costo_unitario = db.Column(db.Float, nullable=False)
    costo_total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, en_transito, entregado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    producto = db.relationship('Producto', backref='compras')
    
    def __repr__(self):
        return f'<Compra Día {self.dia_orden} - Empresa {self.empresa_id}>'


class Decision(db.Model):
    """Modelo de decisiones - Registro de todas las decisiones tomadas"""
    __tablename__ = 'decisiones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    dia_simulacion = db.Column(db.Integer, nullable=False)
    tipo_decision = db.Column(db.String(50), nullable=False)  # compra, venta, precio, distribucion
    datos_decision = db.Column(db.JSON)  # Almacena detalles específicos de cada decisión
    resultado = db.Column(db.JSON)  # Resultado de la decisión
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    empresa = db.relationship('Empresa', backref='decisiones')
    
    def __repr__(self):
        return f'<Decision {self.tipo_decision} - Usuario {self.usuario_id}>'


class Escenario(db.Model):
    """Modelo de escenarios - Disrupciones y eventos especiales"""
    __tablename__ = 'escenarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(50))  # disrupcion, oportunidad, crisis
    dia_inicio = db.Column(db.Integer)
    dia_fin = db.Column(db.Integer)
    activo = db.Column(db.Boolean, default=False)
    parametros = db.Column(db.JSON)  # Efectos del escenario
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Escenario {self.nombre}>'


class Metrica(db.Model):
    """Modelo de métricas - KPIs y desempeño por empresa"""
    __tablename__ = 'metricas'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    dia_simulacion = db.Column(db.Integer, nullable=False)
    
    # Métricas financieras
    ingresos = db.Column(db.Float, default=0)
    costos = db.Column(db.Float, default=0)
    utilidad = db.Column(db.Float, default=0)
    
    # Métricas operativas
    nivel_servicio = db.Column(db.Float, default=0)  # % de ventas cumplidas
    rotacion_inventario = db.Column(db.Float, default=0)
    dias_inventario = db.Column(db.Float, default=0)
    
    # Métricas de eficiencia
    costo_almacenamiento = db.Column(db.Float, default=0)
    costo_transporte = db.Column(db.Float, default=0)
    quiebres_stock = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    empresa = db.relationship('Empresa', backref='metricas')
    
    def __repr__(self):
        return f'<Metrica Día {self.dia_simulacion} - Empresa {self.empresa_id}>'


class Pronostico(db.Model):
    """Modelo de pronósticos - Predicciones de demanda"""
    __tablename__ = 'pronosticos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    dia_generacion = db.Column(db.Integer, nullable=False)
    dia_pronostico = db.Column(db.Integer, nullable=False)  # Día para el que se pronostica
    
    # Métodos de pronóstico
    metodo_usado = db.Column(db.String(50), nullable=False)  # promedio_movil, exp_simple, holt
    parametros = db.Column(db.JSON)  # {n: 3} o {alpha: 0.3} o {alpha: 0.3, beta: 0.2}
    
    # Resultados
    demanda_pronosticada = db.Column(db.Float, nullable=False)
    error_mape = db.Column(db.Float)  # Mean Absolute Percentage Error
    error_mad = db.Column(db.Float)  # Mean Absolute Deviation
    
    # Datos históricos usados
    datos_historicos = db.Column(db.JSON)  # Array de demandas históricas
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    usuario = db.relationship('Usuario', backref='pronosticos')
    empresa = db.relationship('Empresa', backref='pronosticos')
    producto = db.relationship('Producto', backref='pronosticos')
    
    def __repr__(self):
        return f'<Pronostico {self.metodo_usado} - Producto {self.producto_id} - Día {self.dia_pronostico}>'


class RequerimientoCompra(db.Model):
    """Modelo de requerimientos - Comunicación Planeación → Compras"""
    __tablename__ = 'requerimientos_compra'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_planeacion_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    pronostico_id = db.Column(db.Integer, db.ForeignKey('pronosticos.id'))
    
    dia_generacion = db.Column(db.Integer, nullable=False)
    dia_necesidad = db.Column(db.Integer, nullable=False)  # Día en que se necesita el producto
    
    # Cálculos
    demanda_pronosticada = db.Column(db.Float, nullable=False)
    stock_actual = db.Column(db.Float, nullable=False)
    stock_seguridad = db.Column(db.Float, nullable=False)
    lead_time = db.Column(db.Integer, nullable=False)  # Días de espera
    cantidad_sugerida = db.Column(db.Float, nullable=False)  # Cuánto pedir
    
    # Estado
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, revisado, convertido_orden
    notas_planeacion = db.Column(db.Text)
    notas_compras = db.Column(db.Text)
    
    # Órden de compra asociada (si fue convertida)
    orden_compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    empresa = db.relationship('Empresa', backref='requerimientos')
    producto = db.relationship('Producto', backref='requerimientos')
    usuario_planeacion = db.relationship('Usuario', backref='requerimientos_generados')
    pronostico = db.relationship('Pronostico', backref='requerimientos')
    orden_compra = db.relationship('Compra', backref='requerimiento_origen', foreign_keys=[orden_compra_id])
    
    def __repr__(self):
        return f'<RequerimientoCompra Producto {self.producto_id} - {self.cantidad_sugerida} unidades>'


class MovimientoInventario(db.Model):
    """Modelo de movimientos de inventario - Trazabilidad completa"""
    __tablename__ = 'movimientos_inventario'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)  # NULL para procesos automáticos
    
    dia_simulacion = db.Column(db.Integer, nullable=False)
    tipo_movimiento = db.Column(db.String(30), nullable=False)  # entrada_compra, salida_venta, salida_despacho, ajuste, transferencia
    cantidad = db.Column(db.Float, nullable=False)
    saldo_anterior = db.Column(db.Float, nullable=False)
    saldo_nuevo = db.Column(db.Float, nullable=False)
    
    # Referencias opcionales
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'))
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'))
    despacho_id = db.Column(db.Integer, db.ForeignKey('despachos_regionales.id'))
    
    observaciones = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    empresa = db.relationship('Empresa', backref='movimientos_inventario')
    producto = db.relationship('Producto', backref='movimientos')
    usuario = db.relationship('Usuario', backref='movimientos_registrados')
    compra = db.relationship('Compra', backref='movimiento_inventario')
    venta = db.relationship('Venta', backref='movimiento_inventario')
    
    def __repr__(self):
        return f'<MovimientoInventario {self.tipo_movimiento} - {self.cantidad} unidades>'


class DespachoRegional(db.Model):
    """Modelo de despachos regionales - Distribución a regiones"""
    __tablename__ = 'despachos_regionales'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_logistica_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    region = db.Column(db.String(50), nullable=False)  # Andina, Caribe, Pacífica, Orinoquía, Amazonía
    dia_despacho = db.Column(db.Integer, nullable=False)
    dia_entrega_estimado = db.Column(db.Integer, nullable=False)
    dia_entrega_real = db.Column(db.Integer)
    
    cantidad = db.Column(db.Float, nullable=False)
    costo_transporte = db.Column(db.Float, default=0)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, en_transito, entregado
    
    # Relación con ventas (puede estar asociado a ventas específicas)
    ventas_asociadas = db.Column(db.JSON)  # Lista de IDs de ventas que motivaron el despacho
    
    observaciones = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    empresa = db.relationship('Empresa', backref='despachos_regionales')
    producto = db.relationship('Producto', backref='despachos')
    usuario_logistica = db.relationship('Usuario', backref='despachos_gestionados')
    
    def __repr__(self):
        return f'<DespachoRegional {self.region} - {self.cantidad} unidades - {self.estado}>'


class DisrupcionActiva(db.Model):
    """Modelo de disrupciones activas - Eventos activados por el profesor"""
    __tablename__ = 'disrupciones_activas'
    
    id = db.Column(db.Integer, primary_key=True)
    simulacion_id = db.Column(db.Integer, db.ForeignKey('simulacion.id'), nullable=False)
    profesor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Identificación de la disrupción
    nombre = db.Column(db.String(100), nullable=False)
    tipo_disrupcion = db.Column(db.String(50), nullable=False)  
    # Tipos: retraso_proveedor, aumento_demanda, reduccion_capacidad, aumento_costos, region_bloqueada
    
    descripcion = db.Column(db.Text, nullable=False)
    icono = db.Column(db.String(50))  # Icono de Font Awesome
    
    # Temporalidad
    dia_inicio = db.Column(db.Integer, nullable=False)
    dia_fin = db.Column(db.Integer, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Parámetros de impacto (JSON flexible para cada tipo)
    parametros = db.Column(db.JSON, nullable=False)
    # Ejemplos:
    # retraso_proveedor: {dias_adicionales: 5, productos_afectados: [1,2], razon: "Derrumbe vía Bogotá-Medellín"}
    # aumento_demanda: {multiplicador: 2.5, regiones: ["Andina", "Caribe"], productos: [3], razon: "Día de la Madre"}
    # reduccion_capacidad: {reduccion_porcentaje: 30, regiones: ["Pacífica"], razon: "Paro de transportadores"}
    # aumento_costos: {incremento_porcentaje: 25, productos: [1,2,3], razon: "Devaluación del dólar"}
    # region_bloqueada: {regiones: ["Orinoquía"], dias_bloqueo: 3, razon: "Bloqueos viales"}
    
    # Severidad y visibilidad
    severidad = db.Column(db.String(20), default='media')  # baja, media, alta, critica
    visible_estudiantes = db.Column(db.Boolean, default=True)  # Si los estudiantes ven la alerta
    
    # Empresas afectadas (null = todas)
    empresas_afectadas = db.Column(db.JSON)  # [1, 2] o null para todas
    
    # Notificaciones
    notificacion_enviada = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    simulacion = db.relationship('Simulacion', backref='disrupciones')
    profesor = db.relationship('Usuario', backref='disrupciones_activadas')
    
    def __repr__(self):
        return f'<DisrupcionActiva {self.tipo_disrupcion} - {self.nombre}>'
    
    def esta_activa(self, dia_actual):
        """Verifica si la disrupción está activa en el día actual"""
        return self.activo and self.dia_inicio <= dia_actual <= self.dia_fin
    
    def aplicar_efecto(self, contexto):
        """Aplica los efectos de la disrupción según su tipo"""
        if not self.activo:
            return None
            
        efectos = {}
        
        if self.tipo_disrupcion == 'retraso_proveedor':
            efectos['lead_time_adicional'] = self.parametros.get('dias_adicionales', 0)
            efectos['productos_afectados'] = self.parametros.get('productos_afectados', [])
            
        elif self.tipo_disrupcion == 'aumento_demanda':
            efectos['multiplicador_demanda'] = self.parametros.get('multiplicador', 1.0)
            efectos['regiones_afectadas'] = self.parametros.get('regiones', [])
            efectos['productos_afectados'] = self.parametros.get('productos', [])
            
        elif self.tipo_disrupcion == 'reduccion_capacidad':
            efectos['reduccion_porcentaje'] = self.parametros.get('reduccion_porcentaje', 0)
            efectos['regiones_afectadas'] = self.parametros.get('regiones', [])
            
        elif self.tipo_disrupcion == 'aumento_costos':
            efectos['incremento_porcentaje'] = self.parametros.get('incremento_porcentaje', 0)
            efectos['productos_afectados'] = self.parametros.get('productos', [])
            
        elif self.tipo_disrupcion == 'region_bloqueada':
            efectos['regiones_bloqueadas'] = self.parametros.get('regiones', [])
            efectos['dias_bloqueo_adicionales'] = self.parametros.get('dias_bloqueo', 0)
        
        return efectos
