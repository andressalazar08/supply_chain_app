# 🚀 Guía de Instalación - Sistema de Autenticación Mejorado

## Pasos para Implementar

### 1️⃣ Instalar Dependencias

```bash
cd fullstack
pip install -r requirements.txt
```

### 2️⃣ Configurar Correo Electrónico

#### Opción A: Gmail (Recomendado para desarrollo)

1. **Activa la verificación en 2 pasos en tu cuenta de Google**
   - Ve a: https://myaccount.google.com/security
   - Busca "Verificación en dos pasos" y actívala

2. **Genera una contraseña de aplicación**
   - Ve a: https://myaccount.google.com/apppasswords
   - Selecciona "Correo" y "Otro (nombre personalizado)"
   - Escribe "ERP Educativo" y genera
   - Copia la contraseña de 16 dígitos

3. **Configura las variables de entorno**

**Windows PowerShell:**
```powershell
$env:MAIL_USERNAME="tu-correo@gmail.com"
$env:MAIL_PASSWORD="xxxx-xxxx-xxxx-xxxx"  # La contraseña generada
```

**Windows CMD:**
```cmd
set MAIL_USERNAME=tu-correo@gmail.com
set MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

**Linux/Mac:**
```bash
export MAIL_USERNAME="tu-correo@gmail.com"
export MAIL_PASSWORD="xxxx-xxxx-xxxx-xxxx"
```

O crea un archivo `.env`:
```bash
cp .env.example .env
# Edita .env con tus credenciales
```

#### Opción B: Otro proveedor de correo

Modifica en `app.py`:
```python
# Outlook
app.config['MAIL_SERVER'] = 'smtp.office365.com'

# Yahoo
app.config['MAIL_SERVER'] = 'smtp.mail.yahoo.com'
```

### 3️⃣ Migrar Base de Datos

**Si tienes base de datos existente:**
```bash
python migrate_db.py
```

**Si es instalación nueva:**
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

### 4️⃣ Personalizar Dominios Permitidos

Edita `utils/email_utils.py`:

```python
dominios_permitidos = [
    '@tuuniversidad.edu.co',
    '@est.tuuniversidad.edu.co',
    # Agrega los dominios de tu institución
]
```

**⚠️ IMPORTANTE:** Elimina `@gmail.com` en producción.

### 5️⃣ Ejecutar la Aplicación

```bash
python app.py
```

O con el script de inicio:
```bash
.\start.bat  # Windows
```

La aplicación estará disponible en: http://localhost:5000

---

## ✅ Verificación de Instalación

### Prueba el Sistema de Correo

1. **Registro de usuario:**
   - Ir a: http://localhost:5000/auth/register
   - Registrar con un correo válido
   - Verificar que llegue el correo con código

2. **Recuperación de contraseña:**
   - Ir a: http://localhost:5000/auth/forgot-password
   - Ingresar correo registrado
   - Verificar que llegue contraseña temporal

### Prueba los Usuarios de Prueba Piloto

Estos usuarios **NO necesitan** verificación de correo:

| Usuario | Rol | Empresa | Contraseña |
|---------|-----|---------|------------|
| admin | Administrador | - | admin123 |
| estudiante_1_1 | Ventas | 1 | (ninguna) |
| estudiante_2_2 | Planeación | 2 | (ninguna) |
| estudiante_3_1 | Compras | 1 | (ninguna) |
| estudiante_4_3 | Logística | 3 | (ninguna) |

---

## 🔧 Solución de Problemas

### ❌ "Error al enviar correo"

**Causa:** Credenciales incorrectas o seguridad de Gmail

**Solución:**
1. Verifica que la contraseña de aplicación esté correcta
2. Asegúrate de tener verificación en 2 pasos activa
3. Revisa que las variables de entorno estén configuradas
4. Intenta con otro correo Gmail

**Verificar configuración:**
```python
from app import app
with app.app_context():
    print(app.config['MAIL_USERNAME'])
    print(app.config['MAIL_SERVER'])
```

### ❌ "Correo ya está registrado"

**Causa:** Email duplicado en la base de datos

**Solución:**
```python
from app import app, db
from models import Usuario

with app.app_context():
    # Ver usuario con ese email
    usuario = Usuario.query.filter_by(email='correo@ejemplo.com').first()
    if usuario:
        print(f"Usuario: {usuario.username}")
        # Eliminar si es necesario
        # db.session.delete(usuario)
        # db.session.commit()
```

### ❌ Error de migración

**Causa:** Base de datos bloqueada o corrupta

**Solución:**
```bash
# Backup de la base de datos
cp instance/supply_chain.db instance/supply_chain.db.backup

# Recrear desde cero (⚠️ PERDERÁS DATOS)
python
>>> from app import app, db
>>> with app.app_context():
...     db.drop_all()
...     db.create_all()
```

### 📧 Correos no llegan

1. **Revisa spam/promociones** en tu bandeja
2. **Verifica el correo remitente** (noreply@erpeducativo.com)
3. **Consulta logs de la aplicación** para errores
4. **Prueba con otro correo** (diferentes proveedores)

---

## 🎯 Próximos Pasos

1. ✅ Sistema instalado y funcionando
2. 📝 Personalizar dominios permitidos
3. 🔐 Cambiar SECRET_KEY en producción
4. 📧 Configurar correo de producción (SendGrid, AWS SES, etc.)
5. 👥 Crear empresas y asignar estudiantes
6. 🎮 Iniciar simulación

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa el archivo `AUTENTICACION_README.md` para detalles técnicos
2. Verifica los logs de la aplicación
3. Consulta la documentación de Flask-Mail: https://pythonhosted.org/Flask-Mail/

---

## 🎉 ¡Listo!

Tu sistema de autenticación está configurado con:
- ✅ Registro de usuarios con correo institucional
- ✅ Verificación por código de 6 dígitos
- ✅ Recuperación de contraseña
- ✅ Cambio de contraseña seguro
- ✅ Usuarios de prueba piloto funcionando

**¡Disfruta de tu aplicación ERP Educativo mejorada!** 🚀
