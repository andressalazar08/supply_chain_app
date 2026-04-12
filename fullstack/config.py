"""
Archivo de configuración centralizado
"""
import os
from datetime import timedelta


class Config:
    """Configuración base"""
    # Secret key para sesiones
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Base de datos - Soporta SQLite (desarrollo) y PostgreSQL (producción)
    # Si DATABASE_URL no está definida, usa SQLite
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        # Railway y otros servicios usan postgres://, pero SQLAlchemy requiere postgresql://
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///supply_chain.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = os.environ.get(
        'SESSION_COOKIE_SECURE', 'false').lower() in ['true', 'on', '1']
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    # Configuración de correo (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in [
        'true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in [
        'true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get(
        'MAIL_DEFAULT_SENDER') or 'noreply@erpeducativo.com'

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

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """En producción, DATABASE_URL es requerida"""
        if not os.environ.get('DATABASE_URL'):
            raise ValueError(
                'DATABASE_URL no está configurada en variables de entorno')
        db_url = os.environ.get('DATABASE_URL')
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url


class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


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
    'PLANEACION_COMPRAS': 'compras',
    'LOGISTICA': 'logistica'
}

# Mapeo de número a rol
ROLES_NUM_MAP = {
    '1': 'ventas',
    '2': 'compras',
    '3': 'logistica'
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
