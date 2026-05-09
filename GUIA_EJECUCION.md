# 📋 Guía Paso a Paso: Cómo Ejecutar Supply Chain App

## 📌 Descripción General
Esta es una **aplicación Flask (Python)** que simula un sistema ERP educativo para cadena de abastecimiento. Es una aplicación fullstack con backend en Python/Flask y frontend en Jinja2 templates.

---

## 🚀 Pasos de Ejecución

### **Paso 1: Abre PowerShell**
Abre PowerShell (Windows Terminal o CMD)

---

### **Paso 2: Navega a la carpeta del proyecto**
```powershell
cd "c:\Users\ASUS\Desktop\Universidad\10mo semestre\Trabajo de grado II\Aplicación Prueba TG\supply_chain_app\fullstack"
```

**¿Qué hace?** Te lleva a la carpeta principal de la aplicación donde está el archivo `app.py`

---

### **Paso 3: Crea un entorno virtual**
```powershell
python -m venv venv
```

**¿Qué hace?** Crea una carpeta `venv` aislada donde se instalarán las dependencias de Python sin afectar tu sistema.

---

### **Paso 4: Activa el entorno virtual**
```powershell
.\venv\Scripts\Activate.ps1
```

**¿Qué hace?** Activa el entorno virtual. Verás que el prompt cambia a algo como `(venv) C:\ruta\del\proyecto>`

**Nota:** Si obtienes error de permisos, ejecuta esto primero:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### **Paso 5: Instala las dependencias**
```powershell
pip install -r requirements.txt
```

**¿Qué hace?** Instala todas las librerías Python necesarias:
- Flask (framework web)
- SQLAlchemy (base de datos)
- Flask-Login (autenticación)
- PostgreSQL driver
- NumPy (cálculos)
- Y muchas más...

**Tiempo esperado:** 2-5 minutos

---

### **Paso 6: Configura variables de entorno**
```powershell
Copy-Item ".env.example" ".env"
```

**¿Qué hace?** Copia el archivo `.env.example` como `.env`

Luego abre el archivo `.env` (con un editor de texto) y configura:
- `MAIL_USERNAME` → Tu email de Gmail
- `MAIL_PASSWORD` → Tu contraseña o app-password de Gmail
- `SECRET_KEY` → Una clave segura (puede ser cualquier string aleatorio)
- `DATABASE_URL` → Deja como está para desarrollo (usa SQLite)

---

### **Paso 7: Inicializa la base de datos (Opcional pero Recomendado)**

#### **Opción A: Con datos iniciales**
```powershell
python seed_datos_iniciales.py
```

**¿Qué hace?** 
- Crea la estructura de la base de datos
- Carga datos de ejemplo (departamentos, roles, usuarios de prueba)
- Configura parámetros de simulación

#### **Opción B: Crear usuario administrador**
```powershell
python create_admin.py
```

**¿Qué hace?** Te pide que ingreses:
- Email del admin
- Contraseña del admin

**Ejemplo:**
```
Email: admin@example.com
Contraseña: 123456
```

---

### **Paso 8: Inicia la aplicación**
```powershell
python app.py
```

**¿Qué hace?** Inicia el servidor Flask en modo desarrollo.

Verás algo como:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

---

### **Paso 9: Accede a la aplicación**
Abre tu navegador web y ve a:
```
http://localhost:5000
```

**¿Qué debería ver?**
- La página de login de la aplicación
- Si ejecutaste los scripts del paso 7, puedes entrar con el usuario admin que creaste

---

## 🛑 Para Detener la Aplicación

En PowerShell, presiona:
```
Ctrl + C
```

---

## 🔄 Próximas Veces que Ejecutes

No necesitas repetir los pasos 3-6. Solo necesitas:

1. Navega a la carpeta:
```powershell
cd "c:\Users\ASUS\Desktop\Universidad\10mo semestre\Trabajo de grado II\Aplicación Prueba TG\supply_chain_app\fullstack"
```

2. Activa el entorno virtual:
```powershell
.\venv\Scripts\Activate.ps1
```

3. Inicia la aplicación:
```powershell
python app.py
```

---

## ⚠️ Errores Comunes

| Error | Solución |
|-------|----------|
| `python: no se reconoce` | Instala Python desde python.org |
| `ExecutionPolicy` | Ejecuta: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `ModuleNotFoundError` | Verifica que el venv esté activado y ejecuta `pip install -r requirements.txt` de nuevo |
| `Port 5000 in use` | Otro programa usa el puerto. Cambia en `app.py`: `app.run(port=5001)` |
| `Database error` | Elimina la carpeta `instance/` y vuelve a ejecutar `seed_datos_iniciales.py` |

---

## 📊 Tecnologías Usadas

| Componente | Tecnología |
|-----------|-----------|
| Backend | Python 3.11.2 + Flask |
| Base de Datos | SQLite (desarrollo) / PostgreSQL (producción) |
| Frontend | HTML/CSS/JavaScript + Jinja2 Templates |
| ORM | SQLAlchemy |
| Autenticación | Flask-Login |
| Servidor | Gunicorn |

---

## 📚 Archivos Importantes

- `app.py` → Archivo principal de la aplicación
- `requirements.txt` → Dependencias Python
- `.env` → Variables de entorno (crear del `.env.example`)
- `config.py` → Configuración de la aplicación
- `seed_datos_iniciales.py` → Carga datos iniciales
- `create_admin.py` → Crea usuario admin
- `routes/` → Rutas/endpoints de la API
- `templates/` → Archivos HTML
- `static/` → CSS, JavaScript, imágenes

---

## ✅ Checklist de Verificación

- [ ] Git clonado correctamente
- [ ] Estoy en la carpeta `fullstack`
- [ ] Entorno virtual creado
- [ ] Entorno virtual activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] `.env` configurado
- [ ] Base de datos inicializada
- [ ] Aplicación ejecutándose en `http://localhost:5000`
- [ ] Puedo acceder con usuario admin

---

**¡Listo! Tu aplicación está funcionando. 🎉**
