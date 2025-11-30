"""
Archivo de configuración centralizado
"""
import os
from datetime import timedelta

class Config:
    """Configuración base"""
    # Secret key para sesiones (cambiar en producción)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///supply_chain.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # Simulación
    DIAS_MAXIMOS_SIMULACION = 90
    CAPITAL_INICIAL_DEFAULT = 1000000.0
    
    # Parámetros de inventario por defecto
    INVENTARIO_INICIAL_DEFAULT = 100
    PUNTO_REORDEN_DEFAULT = 50
    STOCK_SEGURIDAD_DEFAULT = 20
    
    # Costos
    COSTO_ALMACENAMIENTO_POR_UNIDAD = 0.5  # Por día por unidad
    COSTO_FALTANTE_POR_UNIDAD = 10.0  # Penalización por venta perdida
    
    # Paginación
    ITEMS_POR_PAGINA = 20


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    # En producción, usar PostgreSQL
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


# Roles disponibles
ROLES = {
    'ADMIN': 'admin',
    'VENTAS': 'ventas',
    'PLANEACION': 'planeacion',
    'COMPRAS': 'compras',
    'LOGISTICA': 'logistica'
}

# Mapeo de número a rol
ROLES_NUM_MAP = {
    '1': 'ventas',
    '2': 'planeacion',
    '3': 'compras',
    '4': 'logistica'
}

# Mapeo de rol a número
ROLES_NAME_MAP = {v: k for k, v in ROLES_NUM_MAP.items()}

# Estados de simulación
ESTADOS_SIMULACION = {
    'PAUSADO': 'pausado',
    'EN_CURSO': 'en_curso',
    'FINALIZADO': 'finalizado'
}

# Estados de órdenes de compra
ESTADOS_COMPRA = {
    'PENDIENTE': 'pendiente',
    'EN_TRANSITO': 'en_transito',
    'ENTREGADO': 'entregado',
    'CANCELADO': 'cancelado'
}

# Tipos de escenarios
TIPOS_ESCENARIO = {
    'DISRUPCION': 'disrupcion',
    'OPORTUNIDAD': 'oportunidad',
    'CRISIS': 'crisis'
}

# Tipos de decisiones
TIPOS_DECISION = {
    'COMPRA': 'compra',
    'VENTA': 'venta',
    'PRECIO': 'precio',
    'DISTRIBUCION': 'distribucion',
    'PRONOSTICO': 'pronostico_demanda',
    'INVENTARIO': 'parametros_inventario'
}
