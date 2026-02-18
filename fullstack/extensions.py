"""
Extensiones de Flask - Base de datos y correo
"""
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()
