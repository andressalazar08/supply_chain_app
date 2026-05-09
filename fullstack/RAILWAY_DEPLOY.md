# 🚀 GUÍA RÁPIDA DE DEPLOY EN RAILWAY

## Pasos para deploy en Railway (10 minutos)

### 1️⃣ Preparar GitHub

```bash
# Si no has hecho pull del código actualizado
cd tu-repositorio-local
git pull origin main

# Confirmar cambios locales
git add .
git commit -m "Preparar para deploy en Railway"
git push origin main
```

### 2️⃣ Crear Proyecto en Railway

1. Ve a https://railway.app
2. Inicia sesión con GitHub
3. Click en **"New Project"**
4. Selecciona **"Deploy from GitHub"**
5. Conecta tu repositorio `supply_chain_app`
6. Selecciona la rama `main`
7. Click en **"Deploy"**

Railway detectará automáticamente que es un proyecto Python/Flask y usará el `Procfile`.

### 3️⃣ Agregar PostgreSQL

1. En el dashboard de Railway, click en **"+ New"**
2. Selecciona **"PostgreSQL"**
3. Railway creará automáticamente la variable `DATABASE_URL`

### 4️⃣ Configurar Variables de Entorno

En Railway, ve a **Variables**:

```
FLASK_ENV=production
SECRET_KEY=[VER INSTRUCCIÓN ABAJO]
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-contraseña-app
MAIL_DEFAULT_SENDER=noreply@erpeducativo.com
```

#### 🔐 Generar SECRET_KEY seguro

En tu terminal local:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copia el resultado y pégalo en `SECRET_KEY` en Railway.

#### 📧 Configurar Gmail

1. Ve a https://myaccount.google.com/ y login
2. Busca "App passwords" en la búsqueda
3. Selecciona **Mail** y **Windows Computer** (o tu dispositivo)
4. Google generará una contraseña de 16 caracteres
5. Copia esa contraseña a `MAIL_PASSWORD` en Railway

### 5️⃣ Deploy Automático

- Una vez configuradas las variables, Railway automáticamente hará deploy
- Si necesitas redeploy, ve a **Deployments** y click en **Redeploy**

### ✅ Verificar que está funcionando

1. En Railway, copia la URL de tu aplicación
2. Abre en navegador: `https://tu-url-railway.up.railway.app`
3. Deberías ver la página de login
4. Intenta login con `admin` / `admin123`

Si te sale error de base de datos vacía, ejecuta:

```bash
# Desde tu terminal local
python create_admin.py
```

## 🆘 Troubleshooting

### "Internal Server Error"

1. Ve a **Logs** en Railway
2. Busca el error exacto
3. Problemas comunes:
   - `DATABASE_URL` mal configurada
   - `SECRET_KEY` no configurada
   - `MAIL_USERNAME` / `MAIL_PASSWORD` incorrectos

### "Connection refused to database"

- Espera 2-3 minutos después de agregar PostgreSQL
- Railway necesita tiempo para crear la base de datos
- Luego haz **Redeploy**

### "Email no se envía"

- Verifica que `MAIL_USERNAME` es un email Gmail válido
- Verifica que `MAIL_PASSWORD` es una contraseña de app (no la contraseña normal)
- Habilita autenticación de 2 factores en Google

## 📊 Monitoreo en Railway

En el dashboard puedes ver:
- **Logs**: Errores y eventos
- **Metrics**: CPU, memoria, requests
- **Settings**: Variables y configuración

## 🔄 Actualizar el deploy

Cada vez que hagas push a GitHub, Railway automáticamente:
1. Detecta los cambios
2. Reconstruye la image Docker
3. Hace auto-deploy

No necesitas hacer nada más. ✨

## 💾 Respaldar la base de datos

Railway mantiene automáticamente backups. Para reducir la base de datos:

```bash
# En PostgreSQL admin panel de Railway
psql [tu-database-url]
```

## 🎯 Próximos pasos

- Configurar dominio personalizado (primium)
- Añadir email service proper (SendGrid, etc)
- Configurar CI/CD avanzado
- Monitorear performance

---

**¿Preguntas?** Ver documentación oficial: https://docs.railway.app/
