"""
Rutas de autenticación - Login, Logout, Registro y Recuperación
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from models import Usuario
from extensions import db
import re
import os
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Configuración para subir fotos
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'perfiles')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja el login con email/username y contraseña
    """
    if request.method == 'POST':
        login_input = request.form.get('username')  # Puede ser email o username
        password = request.form.get('password')
        
        if not login_input or not password:
            flash('Por favor ingresa tu email/usuario y contraseña', 'error')
            return redirect(url_for('auth.login'))
        
        # Buscar usuario por email o username
        user = Usuario.query.filter(
            (Usuario.email == login_input) | (Usuario.username == login_input)
        ).first()
        
        if not user:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('auth.login'))
        
        # Verificar contraseña
        if not check_password_hash(user.password, password):
            flash('Contraseña incorrecta', 'error')
            return redirect(url_for('auth.login'))
        
        # Login exitoso
        login_user(user)
        flash(f'¡Bienvenido {user.nombre_completo or user.username}!', 'success')
        
        # Redirigir según tipo de usuario
        if user.tipo_usuario == 'profesor' or user.rol == 'admin' or user.es_super_admin:
            return redirect(url_for('profesor.home'))
        else:
            return redirect(url_for('estudiante.home'))
    
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registro de nuevos usuarios (estudiantes y profesores)
    """
    if request.method == 'POST':
        # Obtener datos del formulario
        tipo_usuario = request.form.get('tipo_usuario')  # 'estudiante' o 'docente'
        nombre_completo = request.form.get('nombre_completo')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        universidad = request.form.get('universidad')
        if universidad == 'otro':
            universidad = request.form.get('universidad_otro')
        sede = request.form.get('sede')
        if sede == 'otro':
            sede = request.form.get('sede_otro')
        carrera = request.form.get('carrera')
        if carrera == 'otro':
            carrera = request.form.get('carrera_otro')
        
        # Validaciones básicas
        if not all([tipo_usuario, nombre_completo, email, password, confirm_password]):
            flash('Los campos básicos (nombre, email, contraseñas) son obligatorios', 'error')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('auth.register'))
        
        # Validar formato de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('El formato del email no es válido', 'error')
            return redirect(url_for('auth.register'))
        
        # Generar username desde el email
        username = email.split('@')[0]
        # Si el username ya existe, agregar un número
        base_username = username
        counter = 1
        while Usuario.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Verificar si el email ya existe
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'error')
            return redirect(url_for('auth.register'))
        
        # Obtener códigos específicos según tipo de usuario
        if tipo_usuario == 'estudiante':
            codigo_estudiante = request.form.get('codigo_estudiante')
            
            # Crear nuevo estudiante
            nuevo_usuario = Usuario(
                username=username,
                password=generate_password_hash(password),
                nombre_completo=nombre_completo,
                email=email,
                tipo_usuario='estudiante',
                universidad=universidad or 'No especificada',
                sede=sede or 'No especificada',
                carrera=carrera or 'No especificada',
                codigo_estudiante=codigo_estudiante,
                rol=None,  # Se asignará cuando el profesor lo agregue a una empresa
                empresa_id=None
            )
        
        elif tipo_usuario == 'docente':
            codigo_profesor = request.form.get('codigo_profesor')
            if not codigo_profesor:
                flash('El código de profesor es obligatorio', 'error')
                return redirect(url_for('auth.register'))
            
            # Crear nuevo profesor
            nuevo_usuario = Usuario(
                username=username,
                password=generate_password_hash(password),
                nombre_completo=nombre_completo,
                email=email,
                tipo_usuario='profesor',
                universidad=universidad or 'No especificada',
                sede=sede or 'No especificada',
                carrera=carrera,
                codigo_profesor=codigo_profesor,
                rol='admin'
            )
        else:
            flash('Tipo de usuario no válido', 'error')
            return redirect(url_for('auth.register'))
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('¡Registro exitoso! Ya puedes iniciar sesión', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar usuario: {str(e)}', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Solicitud de recuperación de contraseña
    """
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Por favor ingrese su email', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        user = Usuario.query.filter_by(email=email).first()
        
        if not user:
            flash('No existe un usuario con ese email', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # Generar código de verificación de 6 dígitos
        import random
        codigo_verificacion = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Guardar código y email en sesión (expira cuando se cierra el navegador)
        session['reset_email'] = email
        session['reset_code'] = codigo_verificacion
        session['reset_attempts'] = 0
        
        # Intentar enviar email
        try:
            from extensions import mail
            from flask_mail import Message
            
            msg = Message(
                subject='Recuperación de Contraseña - ERP Educativo',
                recipients=[email],
                html=f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #8e44ad;">Recuperación de Contraseña</h2>
                    <p>Hola {user.nombre_completo},</p>
                    <p>Has solicitado recuperar tu contraseña. Usa el siguiente código de verificación:</p>
                    <div style="background-color: #f5f5f5; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #8e44ad; margin: 20px 0;">
                        {codigo_verificacion}
                    </div>
                    <p>Este código es válido por 15 minutos.</p>
                    <p>Si no solicitaste este cambio, ignora este correo.</p>
                    <hr style="border: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #666; font-size: 12px;">Sistema ERP Educativo - Simulación de Cadena de Abastecimiento</p>
                </div>
                """
            )
            mail.send(msg)
            flash(f'Se ha enviado un código de verificación a {email}', 'success')
        except Exception as e:
            # Si falla el envío de email, mostrar el código en pantalla (solo para desarrollo)
            print(f"Error al enviar email: {e}")
            flash(f'⚠️ No se pudo enviar el email. Código de recuperación: {codigo_verificacion}', 'warning')
        
        return redirect(url_for('auth.reset_password'))
    
    return render_template('auth/forgot_password.html')


@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """
    Cambio de contraseña después de la recuperación con código de verificación
    """
    # Verificar que haya un email en sesión
    if 'reset_email' not in session or 'reset_code' not in session:
        flash('Solicitud de recuperación inválida. Por favor inicia el proceso de nuevo.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        codigo_ingresado = request.form.get('verification_code')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not codigo_ingresado:
            flash('Debes ingresar el código de verificación', 'error')
            return redirect(url_for('auth.reset_password'))
        
        # Verificar código
        if codigo_ingresado != session.get('reset_code'):
            attempts = session.get('reset_attempts', 0) + 1
            session['reset_attempts'] = attempts
            
            if attempts >= 3:
                # Limpiar sesión después de 3 intentos fallidos
                session.pop('reset_email', None)
                session.pop('reset_code', None)
                session.pop('reset_attempts', None)
                flash('Demasiados intentos fallidos. Por favor solicita un nuevo código.', 'error')
                return redirect(url_for('auth.forgot_password'))
            
            flash(f'Código incorrecto. Te quedan {3 - attempts} intentos.', 'error')
            return redirect(url_for('auth.reset_password'))
        
        if not new_password or not confirm_password:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('auth.reset_password'))
        
        if new_password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('auth.reset_password'))
        
        if len(new_password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('auth.reset_password'))
        
        # Actualizar contraseña
        user = Usuario.query.filter_by(email=session['reset_email']).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            
            # Limpiar sesión
            session.pop('reset_email', None)
            session.pop('reset_code', None)
            session.pop('reset_attempts', None)
            
            flash('¡Contraseña actualizada exitosamente! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Error al actualizar la contraseña', 'error')
            return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/reset_password.html', email=session.get('reset_email'))


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Cambio de contraseña para usuarios autenticados
    """
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('auth.change_password'))
        
        # Verificar contraseña actual
        if not check_password_hash(current_user.password, current_password):
            flash('La contraseña actual es incorrecta', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('Las nuevas contraseñas no coinciden', 'error')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('auth.change_password'))
        
        # Actualizar contraseña
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Contraseña actualizada exitosamente', 'success')
        
        # Redirigir según tipo de usuario
        if current_user.tipo_usuario == 'profesor' or current_user.rol == 'admin':
            return redirect(url_for('profesor.home'))
        else:
            return redirect(url_for('estudiante.home'))
    
    return render_template('auth/change_password.html')


@bp.route('/subir-foto-perfil', methods=['POST'])
@login_required
def subir_foto_perfil():
    """
    Subir o actualizar foto de perfil del usuario
    """
    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo'}), 400
    
    file = request.files['foto']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Formato de archivo no permitido. Use: png, jpg, jpeg, gif'}), 400
    
    try:
        # Crear nombre único para el archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"user_{current_user.id}_{timestamp}.{file.filename.rsplit('.', 1)[1].lower()}")
        
        # Crear directorio si no existe
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Guardar archivo
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Eliminar foto anterior si existe
        if current_user.foto_perfil:
            old_path = os.path.join(UPLOAD_FOLDER, current_user.foto_perfil)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Actualizar base de datos
        current_user.foto_perfil = filename
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Foto actualizada exitosamente',
            'foto_url': url_for('static', filename=f'uploads/perfiles/{filename}')
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al subir archivo: {str(e)}'}), 500
