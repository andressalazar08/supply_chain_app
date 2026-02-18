# Sistema de Autenticación Mejorado - ERP Educativo

## Cambios Implementados

### ✅ Nuevas Funcionalidades

#### 1. **Registro de Usuarios**
- Los estudiantes pueden crear su propia cuenta usando su correo institucional
- Validación de correos institucionales permitidos
- Los usuarios de prueba piloto (estudiante_1_1, etc.) se mantienen sin cambios

#### 2. **Verificación de Correo**
- Envío automático de código de verificación de 6 dígitos al registrarse
- Código válido por 15 minutos
- Opción de reenviar código si expira o no llega
- Los usuarios deben verificar su correo antes de poder iniciar sesión

#### 3. **Recuperación de Contraseña**
- Sistema de "Olvidé mi contraseña"
- Genera contraseña temporal de 10 caracteres
- Envío por correo electrónico
- Contraseña temporal válida por 24 horas
- El usuario puede cambiarla después de iniciar sesión

#### 4. **Cambio de Contraseña**
- Opción para que usuarios autenticados cambien su contraseña
- Validación de contraseña actual
- Nueva ruta: `/auth/change-password`

---

## 📋 Requisitos

### Nuevas Dependencias
```
Flask-Mail>=0.9.1
```

### Variables de Entorno
Crear archivo `.env` con:
```env
MAIL_USERNAME=tu-correo@gmail.com
MAIL_PASSWORD=tu-contraseña-de-aplicacion
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

---

## 🚀 Configuración Rápida

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar Gmail
Para usar Gmail como servidor de correo:

1. Ve a tu cuenta de Google
2. Activa la verificación en 2 pasos
3. Ve a [Contraseñas de aplicaciones](https://myaccount.google.com/apppasswords)
4. Genera una contraseña para "Correo"
5. Copia el archivo `.env.example` a `.env` y completa:

```env
MAIL_USERNAME=tu-correo@gmail.com
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx  # La contraseña de 16 dígitos generada
```

### 3. Actualizar base de datos
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.drop_all()  # Solo si quieres empezar de cero
...     db.create_all()
```

---

## 🎨 Nuevas Rutas

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/auth/login` | GET, POST | Login (actualizado con 3 métodos) |
| `/auth/register` | GET, POST | Registro de nuevo usuario |
| `/auth/verify-email` | GET, POST | Verificar código de correo |
| `/auth/resend-verification` | POST | Reenviar código de verificación |
| `/auth/forgot-password` | GET, POST | Solicitar recuperación de contraseña |
| `/auth/change-password` | GET, POST | Cambiar contraseña (autenticado) |

---

## 📝 Flujos de Usuario

### Registro Nuevo Usuario
1. Click en "Crear Cuenta" en login
2. Llenar formulario con correo institucional
3. Recibir código de 6 dígitos por correo
4. Ingresar código en pantalla de verificación
5. Cuenta activada → Puede iniciar sesión

### Recuperación de Contraseña
1. Click en "Recuperar" en login
2. Ingresar correo electrónico
3. Recibir contraseña temporal por correo
4. Iniciar sesión con contraseña temporal
5. Sistema redirige a cambiar contraseña
6. Establecer nueva contraseña segura

### Usuarios de Prueba (Sin Cambios)
- `admin` / `admin123` → Acceso profesor
- `estudiante_1_1` → Ventas Empresa 1 (sin contraseña)
- `estudiante_2_2` → Planeación Empresa 2
- etc.

---

## 🔧 Archivos Modificados

### Nuevos
- `utils/email_utils.py` - Utilidades de correo
- `templates/auth/register.html` - Formulario de registro
- `templates/auth/verify_email.html` - Verificación de correo
- `templates/auth/forgot_password.html` - Recuperar contraseña
- `templates/auth/change_password.html` - Cambiar contraseña
- `.env.example` - Ejemplo de configuración

### Modificados
- `requirements.txt` - Agregada Flask-Mail
- `models.py` - Campos de verificación en Usuario
- `config.py` - Configuración de correo
- `app.py` - Inicialización de Flask-Mail
- `routes/auth.py` - Nuevas rutas de autenticación
- `templates/auth/login.html` - Botones de registro y recuperación

---

## 🎯 Dominios de Correo Permitidos

Por defecto en `utils/email_utils.py`:
```python
dominios_permitidos = [
    '@universidad.edu.co',
    '@unal.edu.co',
    '@unbosque.edu.co',
    '@javeriana.edu.co',
    '@uniandes.edu.co',
    '@gmail.com',  # Solo para pruebas - REMOVER EN PRODUCCIÓN
]
```

**⚠️ IMPORTANTE**: Personaliza esta lista con los dominios de tu institución.

---

## 🧪 Pruebas Recomendadas

1. **Registro básico**: Crear cuenta con correo válido
2. **Verificación**: Recibir y usar código de verificación
3. **Reenvío**: Probar reenvío de código
4. **Recuperación**: Solicitar contraseña temporal
5. **Cambio**: Cambiar contraseña desde perfil
6. **Login prueba**: Verificar que estudiante_X_X sigue funcionando

---

## 📧 Plantillas de Correo

Los correos incluyen:
- **Diseño HTML responsive**
- **Branding del sistema**
- **Instrucciones claras**
- **Códigos destacados visualmente**
- **Avisos de seguridad**

---

## 🔒 Seguridad Implementada

- ✅ Hash de contraseñas con Werkzeug
- ✅ Códigos de verificación temporales (15 min)
- ✅ Contraseñas temporales expiran en 24h
- ✅ Validación de correos institucionales
- ✅ Verificación de contraseña actual al cambiar
- ✅ Longitud mínima de contraseña (6 caracteres)
- ✅ No se revela si un email existe en el sistema

---

## 🎉 Listo para Usar

El sistema está completamente funcional. Solo necesitas:
1. Configurar las credenciales de correo
2. Personalizar los dominios permitidos
3. Reiniciar la aplicación

```bash
python app.py
```

---

## 💡 Notas Adicionales

- Los usuarios de prueba piloto NO requieren verificación de correo
- Los nuevos usuarios SÍ deben verificar su correo
- Los correos se envían en formato HTML con diseño profesional
- Si el envío de correo falla, el usuario aún se crea (se muestra advertencia)
