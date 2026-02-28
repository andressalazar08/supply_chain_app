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
    rol = db.Column(db.String(20), nullable=True)  # super_admin, admin, ventas, planeacion, compras, logistica (se asigna después)
    tipo_usuario = db.Column(db.String(20), default='estudiante')  # estudiante, docente, super_admin
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    nombre_completo = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campos de información académica
    universidad = db.Column(db.String(200))
    sede = db.Column(db.String(100))
    codigo_estudiante = db.Column(db.String(20), unique=True)
    codigo_profesor = db.Column(db.String(20), unique=True)
    carrera = db.Column(db.String(200))
    foto_perfil = db.Column(db.String(255))  # Nombre del archivo de foto
    
    # Campos para verificación de correo
    email_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6))
    verification_code_expires = db.Column(db.DateTime)
    
    # Campos para recuperación de contraseña
    reset_token = db.Column(db.String(10))
    reset_token_expires = db.Column(db.DateTime)
    
    # Campos para sistema de jerarquía
    es_super_admin = db.Column(db.Boolean, default=False)  # True solo para admin maestro
    profesor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)  # Para estudiantes: qué profesor los gestiona
    
    # Relaciones
    empresa = db.relationship('Empresa', foreign_keys='[Usuario.empresa_id]', backref='estudiantes')
    decisiones = db.relationship('Decision', backref='usuario', lazy=True)
    profesor = db.relationship('Usuario', remote_side=[id], foreign_keys=[profesor_id], backref='estudiantes_asignados')
    empresas_creadas = db.relationship('Empresa', foreign_keys='[Empresa.profesor_id]', backref='profesor_creador')
    
    def __repr__(self):
        return f'<Usuario {self.username} - {self.rol if self.rol else "Sin rol"}>'


class Empresa(db.Model):
    """Modelo de empresa - Cada equipo de estudiantes representa una empresa"""
    __tablename__ = 'empresas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    capital_inicial = db.Column(db.Float, default=1000000.0)
    capital_actual = db.Column(db.Float, default=1000000.0)
    activa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profesor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)  # Profesor que creó esta empresa
    simulacion_id = db.Column(db.Integer, db.ForeignKey('simulacion.id'), nullable=True)  # Simulación a la que pertenece
    
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
    nombre = db.Column(db.String(100), default='Simulación')  # Nombre descriptivo
    semana_actual = db.Column(db.Integer, default=1)
    estado = db.Column(db.String(20), default='pausado')  # pausado, en_curso, finalizado
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
    duracion_semanas = db.Column(db.Integer, default=12)
    capital_inicial_empresas = db.Column(db.Float, default=50000000.0)  # Capital con el que empiezan todas las empresas
    activa = db.Column(db.Boolean, default=True)  # Solo una simulación activa a la vez
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    empresas = db.relationship('Empresa', backref='simulacion', lazy=True)
    
    def __repr__(self):
        return f'<Simulacion {self.nombre} - Semana {self.semana_actual} - {self.estado}>'


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
    tiempo_entrega = db.Column(db.Integer, default=1)  # semanas
    stock_maximo = db.Column(db.Float, default=500)  # Límite de inventario (sobrestock genera costos adicionales)
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
    """Modelo de ventas - Registro de ventas por semana"""
    __tablename__ = 'ventas'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    semana_simulacion = db.Column(db.Integer, nullable=False)
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
        return f'<Venta Semana {self.semana_simulacion} - Empresa {self.empresa_id} - {self.region}>'


class Compra(db.Model):
    """Modelo de compras - Órdenes de compra a proveedores"""
    __tablename__ = 'compras'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    semana_orden = db.Column(db.Integer, nullable=False)
    semana_entrega = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    costo_unitario = db.Column(db.Float, nullable=False)
    costo_total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, en_transito, entregado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    producto = db.relationship('Producto', backref='compras')
    
    def __repr__(self):
        return f'<Compra Semana {self.semana_orden} - Empresa {self.empresa_id}>'


class Decision(db.Model):
    """Modelo de decisiones - Registro de todas las decisiones tomadas"""
    __tablename__ = 'decisiones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    semana_simulacion = db.Column(db.Integer, nullable=False)
    tipo_decision = db.Column(db.String(50), nullable=False)  # compra, venta, precio, distribucion
    datos_decision = db.Column(db.JSON)  # Almacena detalles específicos de cada decisión
    resultado = db.Column(db.JSON)  # Resultado de la decisión
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    empresa = db.relationship('Empresa', backref='decisiones')
    
    def __repr__(self):
        return f'<Decision {self.tipo_decision} - Usuario {self.usuario_id}>'


class Metrica(db.Model):
    """Modelo de métricas - KPIs y desempeño por empresa"""
    __tablename__ = 'metricas'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    semana_simulacion = db.Column(db.Integer, nullable=False)
    
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
        return f'<Metrica Semana {self.semana_simulacion} - Empresa {self.empresa_id}>'


class Pronostico(db.Model):
    """Modelo de pronósticos - Predicciones de demanda"""
    __tablename__ = 'pronosticos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    semana_generacion = db.Column(db.Integer, nullable=False)
    semana_pronostico = db.Column(db.Integer, nullable=False)  # Semana para la que se pronostica
    
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
        return f'<Pronostico {self.metodo_usado} - Producto {self.producto_id} - Semana {self.semana_pronostico}>'


class RequerimientoCompra(db.Model):
    """Modelo de requerimientos - Comunicación Planeación → Compras"""
    __tablename__ = 'requerimientos_compra'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_planeacion_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    pronostico_id = db.Column(db.Integer, db.ForeignKey('pronosticos.id'))
    
    semana_generacion = db.Column(db.Integer, nullable=False)
    semana_necesidad = db.Column(db.Integer, nullable=False)  # Semana en que se necesita el producto
    
    # Cálculos
    demanda_pronosticada = db.Column(db.Float, nullable=False)
    stock_actual = db.Column(db.Float, nullable=False)
    stock_seguridad = db.Column(db.Float, nullable=False)
    lead_time = db.Column(db.Integer, nullable=False)  # Semanas de espera
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
    
    semana_simulacion = db.Column(db.Integer, nullable=False)
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
    semana_despacho = db.Column(db.Integer, nullable=False)
    semana_entrega_estimado = db.Column(db.Integer, nullable=False)
    semana_entrega_real = db.Column(db.Integer)
    
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


class DisrupcionEmpresa(db.Model):
    """
    Instancia de una disrupción activa para una empresa específica.
    Se crea automáticamente cuando la simulación alcanza la semana_trigger del catálogo.
    """
    __tablename__ = 'disrupciones_empresa'

    id = db.Column(db.Integer, primary_key=True)
    simulacion_id = db.Column(db.Integer, db.ForeignKey('simulacion.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)

    # Key del catálogo (ej: 'retraso_proveedor')
    disrupcion_key = db.Column(db.String(50), nullable=False)

    # Producto más demandado al momento de activación
    producto_afectado_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=True)

    semana_inicio = db.Column(db.Integer, nullable=False)
    semana_fin = db.Column(db.Integer, nullable=False)

    # Decisión del equipo: 'A', 'B' o 'C' — None = pendiente de respuesta
    opcion_elegida = db.Column(db.String(1), nullable=True)
    usuario_decision_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    fecha_decision = db.Column(db.DateTime, nullable=True)

    # Control interno
    activa = db.Column(db.Boolean, default=True)
    # Para opción C: marca si ya se aplicó el delay a compras pendientes
    efecto_inicial_aplicado = db.Column(db.Boolean, default=False)
    # Para notificación de cierre: ¿ya la vio el equipo estudiante?
    notificacion_fin_vista = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    empresa = db.relationship('Empresa', backref='disrupciones')
    simulacion = db.relationship('Simulacion', backref='disrupciones')
    producto_afectado = db.relationship('Producto', backref='disrupciones')
    usuario_decision = db.relationship('Usuario', backref='decisiones_disrupcion')

    def __repr__(self):
        return f'<DisrupcionEmpresa {self.disrupcion_key} - Empresa {self.empresa_id} - Opción {self.opcion_elegida}>'
