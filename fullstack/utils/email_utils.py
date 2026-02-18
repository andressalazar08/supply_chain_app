"""
Utilidades para envío de correos electrónicos
"""

import random
import string
from datetime import datetime, timedelta
from flask import current_app, render_template_string


def generar_codigo_verificacion():
    """Genera un código de verificación de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))


def generar_password_temporal():
    """Genera una contraseña temporal de 10 caracteres"""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choices(caracteres, k=10))


def validar_correo_institucional(email):
    """
    Valida que el correo sea institucional
    Puedes personalizar los dominios permitidos según tu institución
    """
    dominios_permitidos = [
        '@universidad.edu.co',
        '@est.universidad.edu.co', 
        '@estudiantes.universidad.edu.co',
        '@unal.edu.co',
        '@unbosque.edu.co',
        '@javeriana.edu.co',
        '@uniandes.edu.co',
        # Agregar más dominios según necesidad
        '@gmail.com',  # Temporal para pruebas - REMOVER EN PRODUCCIÓN
    ]
    
    email_lower = email.lower()
    return any(email_lower.endswith(dominio) for dominio in dominios_permitidos)


def enviar_correo_verificacion(mail, email, codigo):
    """
    Envía correo con código de verificación
    
    Args:
        mail: Instancia de Flask-Mail
        email: Correo destino
        codigo: Código de verificación
    """
    from flask_mail import Message
    
    asunto = "Verifica tu cuenta - ERP Educativo"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                color: #8e44ad;
                margin-bottom: 30px;
            }}
            .code-box {{
                background-color: #f8f9fa;
                border: 2px dashed #8e44ad;
                padding: 20px;
                text-align: center;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 5px;
                margin: 20px 0;
                color: #8e44ad;
            }}
            .footer {{
                text-align: center;
                color: #666;
                font-size: 12px;
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 Bienvenido al ERP Educativo</h1>
                <p>Simulación de Cadena de Abastecimiento</p>
            </div>
            
            <h2>Verifica tu cuenta</h2>
            <p>Hola,</p>
            <p>Gracias por registrarte en nuestro sistema de simulación. Para activar tu cuenta, ingresa el siguiente código de verificación:</p>
            
            <div class="code-box">
                {codigo}
            </div>
            
            <p><strong>Este código expirará en 15 minutos.</strong></p>
            
            <p>Si no solicitaste este registro, puedes ignorar este correo.</p>
            
            <div class="footer">
                <p>© 2026 ERP Educativo - Sistema de Simulación de Supply Chain</p>
                <p>Este es un correo automático, por favor no respondas.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = Message(
            subject=asunto,
            recipients=[email],
            html=html_body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@erpeducativo.com')
        )
        mail.send(msg)
        return True, "Correo enviado exitosamente"
    except Exception as e:
        print(f"Error al enviar correo: {str(e)}")
        return False, f"Error al enviar correo: {str(e)}"


def enviar_correo_recuperacion(mail, email, password_temporal):
    """
    Envía correo con contraseña temporal para recuperación
    
    Args:
        mail: Instancia de Flask-Mail
        email: Correo destino
        password_temporal: Contraseña temporal generada
    """
    from flask_mail import Message
    
    asunto = "Recuperación de Contraseña - ERP Educativo"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                color: #e74c3c;
                margin-bottom: 30px;
            }}
            .password-box {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 20px;
                margin: 20px 0;
            }}
            .password {{
                font-size: 20px;
                font-weight: bold;
                color: #856404;
                font-family: monospace;
                letter-spacing: 2px;
            }}
            .alert {{
                background-color: #f8d7da;
                border-left: 4px solid #e74c3c;
                padding: 15px;
                margin: 20px 0;
                color: #721c24;
            }}
            .footer {{
                text-align: center;
                color: #666;
                font-size: 12px;
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Recuperación de Contraseña</h1>
            </div>
            
            <h2>Contraseña Temporal</h2>
            <p>Hola,</p>
            <p>Has solicitado recuperar tu contraseña. Hemos generado una contraseña temporal para ti:</p>
            
            <div class="password-box">
                <p><strong>Tu contraseña temporal es:</strong></p>
                <p class="password">{password_temporal}</p>
            </div>
            
            <div class="alert">
                <strong>⚠️ Importante:</strong>
                <ul>
                    <li>Usa esta contraseña para iniciar sesión</li>
                    <li>Una vez dentro, dirígete a tu perfil y cámbiala por una nueva contraseña segura</li>
                    <li>Esta contraseña expirará en 24 horas</li>
                </ul>
            </div>
            
            <p>Si no solicitaste este cambio, contacta inmediatamente con el administrador del sistema.</p>
            
            <div class="footer">
                <p>© 2026 ERP Educativo - Sistema de Simulación de Supply Chain</p>
                <p>Este es un correo automático, por favor no respondas.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = Message(
            subject=asunto,
            recipients=[email],
            html=html_body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@erpeducativo.com')
        )
        mail.send(msg)
        return True, "Correo enviado exitosamente"
    except Exception as e:
        print(f"Error al enviar correo: {str(e)}")
        return False, f"Error al enviar correo: {str(e)}"
