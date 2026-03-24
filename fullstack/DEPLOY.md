# Supply Chain App - ERP Educativo

Sistema gamificado de simulación de cadena de abastecimiento para estudiantes de administración.

## 📋 Requisitos

- Python 3.11+
- Flask 3.0.0+
- PostgreSQL (para producción)

## 🚀 Ejecución Local

### 1. Preparar el entorno

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Mac/Linux)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus valores
# - PASSWORD: debe ser una contraseña segura
# - MAIL_USERNAME y MAIL_PASSWORD: datos de tu cuenta Gmail
```

### 3. Inicializar base de datos

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Base de datos creada')"
```

### 4. Crear usuario administrador (opcional)

```bash
python create_admin.py
```

### 5. Ejecutar la aplicación

```bash
python app.py
```

Accede a: **http://localhost:5000**

Credenciales por defecto:
- Usuario: `admin`
- Contraseña: `admin123`

## 🌐 Deploy en Railway

### Pasos:

1. **Instalar CLI de Railway**
   ```bash
   npm install -g @railway/cli
   ```

2. **Hacer push del código a GitHub**
   ```bash
   git add .
   git commit -m "Preparar para deploy"
   git push origin main
   ```

3. **Crear proyecto en Railway**
   - Ir a [railway.app](https://railway.app)
   - Click en "New Project"
   - Seleccionar "Deploy from GitHub"
   - Conectar tu repositorio

4. **Agregar PostgreSQL**
   - En el panel de Railway, click en "Add Service"
   - Seleccionar "PostgreSQL"
   - Railway generará automáticamente `DATABASE_URL`

5. **Configurar variables de entorno**
   
   En Railway dashboard, agregar:
   ```
   FLASK_ENV=production
   SECRET_KEY=[generar con: python -c "import secrets; print(secrets.token_hex(32))"]
   MAIL_USERNAME=[tu email Gmail]
   MAIL_PASSWORD=[tu contraseña de app de Gmail]
   MAIL_DEFAULT_SENDER=noreply@erpeducativo.com
   ```

6. **Deploy automático**
   
   Railway automáticamente deployará cuando hagas push a tu rama principal.

## 📧 Configurar Gmail (SMTP)

Para usar Flask-Mail con Gmail:

1. Habilitar autenticación de dos factores en tu account de Google
2. Generar contraseña de aplicación: https://myaccount.google.com/apppasswords
3. Usar esa contraseña en `MAIL_PASSWORD`

## 📁 Estructura del Proyecto

```
.
├── app.py                 # Aplicación principal
├── config.py              # Configuración (dev/prod)
├── models.py              # Modelos de base de datos
├── extensions.py          # Extensiones Flask
├── requirements.txt       # Dependencias Python
├── Procfile              # Configuración para Heroku/Railway
├── runtime.txt           # Versión Python
├── create_admin.py       # Script para crear admin
│
├── routes/               # Rutas de la aplicación
│   ├── auth.py          # Autenticación
│   ├── profesor.py      # Panel profesor
│   └── estudiante.py    # Panel estudiante
│
├── templates/            # Plantillas HTML
│   ├── base.html
│   ├── auth/
│   ├── profesor/
│   └── estudiante/
│
├── static/              # Assets estáticos
│   ├── css/
│   ├── js/
│   └── uploads/
│
└── utils/              # Utilidades
    ├── pronosticos.py
    ├── inventario.py
    ├── logistica.py
    └── ...
```

## 🔐 Seguridad en Producción

Antes de hacer deploy:

1. ✅ Cambiar `SECRET_KEY`
2. ✅ Usar PostgreSQL en lugar de SQLite
3. ✅ Configurar `SESSION_COOKIE_SECURE=true`
4. ✅ No hacer commit de `.env` (usa `.env.example`)
5. ✅ Usar variables de entorno para secrets

## 📞 Soporte

Para más información sobre Flask: https://flask.palletsprojects.com/
Para Railway: https://docs.railway.app/
