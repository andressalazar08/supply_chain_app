"""
Rutas de autenticación - Login y Logout
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models import Usuario
import re

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja el login diferenciado:
    - admin con contraseña
    - estudiante_#_# donde primer # es rol (1-4) y segundo # es empresa
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Verificar si es administrador
        if username == 'admin':
            user = Usuario.query.filter_by(username='admin').first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('¡Bienvenido Administrador!', 'success')
                return redirect(url_for('profesor.dashboard'))
            else:
                flash('Contraseña incorrecta', 'error')
                return redirect(url_for('auth.login'))
        
        # Verificar formato estudiante_#_#
        pattern = r'^estudiante_([1-4])_(\d+)$'
        match = re.match(pattern, username)
        
        if match:
            rol_num = match.group(1)
            empresa_num = match.group(2)
            
            # Mapear número de rol a nombre
            roles_map = {
                '1': 'ventas',
                '2': 'planeacion',
                '3': 'compras',
                '4': 'logistica'
            }
            
            rol = roles_map.get(rol_num)
            
            # Buscar o crear usuario
            user = Usuario.query.filter_by(username=username).first()
            
            if not user:
                flash(f'Usuario {username} no encontrado. Contacte al administrador.', 'error')
                return redirect(url_for('auth.login'))
            
            # Verificar que el rol coincida
            if user.rol != rol:
                flash('Rol no coincide con el usuario registrado', 'error')
                return redirect(url_for('auth.login'))
            
            # Verificar empresa
            if user.empresa_id != int(empresa_num):
                flash('Número de empresa no coincide', 'error')
                return redirect(url_for('auth.login'))
            
            # Login exitoso
            login_user(user)
            flash(f'¡Bienvenido {user.nombre_completo}!', 'success')
            return redirect(url_for('estudiante.dashboard'))
        
        flash('Formato de usuario incorrecto. Use: admin o estudiante_#_#', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('auth.login'))
