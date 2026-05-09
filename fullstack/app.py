"""
Aplicación Web Gamificada - Simulación de Cadena de Abastecimiento
Sistema ERP Educativo para estudiantes
"""

from routes import auth, profesor, estudiante
from models import Usuario
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from werkzeug.security import generate_password_hash
from extensions import db, mail, migrate
import os
from dotenv import load_dotenv
from config import DevelopmentConfig, ProductionConfig

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de la aplicación según el entorno
app = Flask(__name__)
if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

# Inicializar extensiones
db.init_app(app)
mail.init_app(app)
migrate.init_app(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Agregar funciones globales a Jinja2
app.jinja_env.globals.update(abs=abs)

# Importar modelos después de inicializar db

# Importar rutas

# Registrar blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(profesor.bp)
app.register_blueprint(estudiante.bp)


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


@app.route('/')
def index():
    """Página principal - redirige según el tipo de usuario"""
    if current_user.is_authenticated:
        if current_user.rol == 'admin':
            return redirect(url_for('profesor.dashboard'))
        else:
            return redirect(url_for('estudiante.dashboard'))
    return redirect(url_for('auth.login'))


@app.context_processor
def inject_roles():
    """Hace disponibles las constantes de roles en todas las plantillas"""
    return {
        'ROLES': {
            'ADMIN': 'admin',
            'VENTAS': 'ventas',
            'PLANEACION': 'planeacion',
            'COMPRAS': 'compras',
            'LOGISTICA': 'logistica'
        }
    }


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Crear usuario administrador por defecto si no existe
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            admin = Usuario(
                username='admin',
                password=generate_password_hash('admin123'),
                rol='admin',
                tipo_usuario='profesor',
                es_super_admin=True,
                nombre_completo='Administrador del Sistema'
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuario administrador creado: admin / admin123")

    app.run(debug=True, host='0.0.0.0', port=5000)
