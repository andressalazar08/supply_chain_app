"""
Script para resetear manualmente la contraseña de un usuario
"""

from app import app
from models import Usuario
from extensions import db
from werkzeug.security import generate_password_hash

def resetear_password(email, nueva_password):
    with app.app_context():
        user = Usuario.query.filter_by(email=email).first()
        
        if user:
            user.password = generate_password_hash(nueva_password)
            db.session.commit()
            print(f"✓ Contraseña actualizada para: {user.nombre_completo}")
            print(f"  Email: {email}")
            print(f"  Nueva contraseña: {nueva_password}")
            print(f"\nYa puedes hacer login con:")
            print(f"  Usuario: {email}")
            print(f"  Contraseña: {nueva_password}")
            return True
        else:
            print(f"✗ Usuario no encontrado con email: {email}")
            return False

if __name__ == '__main__':
    # Cambiar estos valores según sea necesario
    email_usuario = 'herreratorresluisalejandro@gmail.com'
    nueva_password = 'Luis123456'
    
    print("="*60)
    print("RESETEO MANUAL DE CONTRASEÑA")
    print("="*60)
    resetear_password(email_usuario, nueva_password)
    print("="*60)
