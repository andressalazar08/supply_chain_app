# COMANDOS RÁPIDOS - ERP Educativo

## 🚀 Inicio Rápido

### Opción 1: Script Automático (Windows)
```powershell
.\start.bat
```

### Opción 2: Manual
```powershell
# 1. Activar entorno virtual
venv\Scripts\activate

# 2. Iniciar aplicación
python app.py
```

---

## 📦 Instalación

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (PowerShell)
venv\Scripts\activate

# Activar entorno virtual (CMD)
venv\Scripts\activate.bat

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos
python init_db.py
```

---

## 🗄️ Base de Datos

```powershell
# Crear/Recrear base de datos
python init_db.py

# Backup de base de datos
copy supply_chain.db supply_chain_backup.db

# Restaurar backup
copy supply_chain_backup.db supply_chain.db
```

---

## 🔧 Desarrollo

```powershell
# Ver logs en tiempo real
python app.py
# La aplicación mostrará logs en consola

# Instalar nueva dependencia
pip install nombre-paquete
pip freeze > requirements.txt

# Ver estructura de tablas
# Usar SQLite Browser o:
python
>>> from app import db
>>> db.metadata.tables.keys()
```

---

## 🧪 Testing

```powershell
# Ejecutar tests (cuando estén implementados)
python -m pytest

# Con cobertura
python -m pytest --cov=.

# Test específico
python -m pytest tests/test_models.py
```

---

## 🐛 Debug

```powershell
# Modo debug (ya está activado por defecto)
# En app.py: app.run(debug=True)

# Ver variables de entorno
python
>>> import os
>>> print(os.environ)

# Verificar conexión a BD
python
>>> from app import app, db
>>> with app.app_context():
...     print(db.engine)
```

---

## 📊 Consultas SQL Útiles

```sql
-- Ver todos los usuarios
SELECT * FROM usuarios;

-- Ver empresas
SELECT * FROM empresas;

-- Ver estado de simulación
SELECT * FROM simulacion;

-- Ver inventarios
SELECT e.nombre, p.nombre, i.cantidad_actual 
FROM inventarios i
JOIN empresas e ON i.empresa_id = e.id
JOIN productos p ON i.producto_id = p.id;

-- Ver ventas del día
SELECT * FROM ventas WHERE dia_simulacion = 1;
```

---

## 🔐 Gestión de Usuarios

```powershell
# Crear usuario admin manualmente
python
>>> from app import app, db
>>> from models import Usuario
>>> from werkzeug.security import generate_password_hash
>>> with app.app_context():
...     admin = Usuario(
...         username='admin',
...         password=generate_password_hash('nueva_password'),
...         rol='admin',
...         nombre_completo='Admin'
...     )
...     db.session.add(admin)
...     db.session.commit()
```

---

## 📈 Monitoreo

```powershell
# Ver procesos Python
Get-Process python

# Ver puerto en uso
netstat -ano | findstr :5000

# Matar proceso en puerto 5000
# 1. Encontrar PID:
netstat -ano | findstr :5000
# 2. Matar proceso:
taskkill /PID <número> /F
```

---

## 🔄 Git

```powershell
# Inicializar repositorio (si no existe)
git init

# Ver estado
git status

# Agregar archivos
git add .

# Commit
git commit -m "Mensaje descriptivo"

# Push a GitHub
git remote add origin https://github.com/usuario/repo.git
git push -u origin main

# Ver historial
git log --oneline
```

---

## 📦 Actualizar Dependencias

```powershell
# Ver dependencias desactualizadas
pip list --outdated

# Actualizar paquete específico
pip install --upgrade nombre-paquete

# Actualizar todas
pip install --upgrade -r requirements.txt

# Exportar dependencias actualizadas
pip freeze > requirements.txt
```

---

## 🧹 Limpieza

```powershell
# Eliminar archivos Python compilados
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse

# Eliminar base de datos
Remove-Item supply_chain.db

# Eliminar entorno virtual
Remove-Item -Recurse venv
```

---

## 🚀 Deployment

### Preparar para producción

```powershell
# 1. Crear requirements de producción
pip freeze > requirements.txt

# 2. Configurar variables de entorno
# Crear archivo .env:
SECRET_KEY=tu-clave-secreta-produccion
DATABASE_URL=postgresql://user:pass@localhost/dbname
FLASK_ENV=production

# 3. Usar Gunicorn (Linux/Mac)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 4. Para Windows, usar waitress
pip install waitress
waitress-serve --port=5000 app:app
```

---

## 📝 Backups Automáticos

```powershell
# Script de backup (crear backup.bat)
@echo off
set timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%
copy supply_chain.db backups\supply_chain_%timestamp%.db
echo Backup creado: supply_chain_%timestamp%.db
```

---

## 🔍 Troubleshooting Común

```powershell
# Error: "venv no es reconocido"
python -m venv venv
# Si persiste, reinstalar Python

# Error: "pip no es reconocido"
python -m pip install --upgrade pip

# Error: "Puerto en uso"
# Cambiar puerto en app.py o matar proceso

# Error: "ImportError"
venv\Scripts\activate
pip install -r requirements.txt

# Error: "Base de datos bloqueada"
# Cerrar todas las conexiones
python init_db.py
```

---

## 📊 Exportar Datos

```powershell
# Exportar base de datos a CSV (crear script)
python
>>> import sqlite3
>>> import csv
>>> conn = sqlite3.connect('supply_chain.db')
>>> cursor = conn.cursor()
>>> cursor.execute("SELECT * FROM ventas")
>>> with open('ventas.csv', 'w', newline='') as f:
...     writer = csv.writer(f)
...     writer.writerow([i[0] for i in cursor.description])
...     writer.writerows(cursor.fetchall())
```

---

## 🎯 Atajos de Desarrollo

```powershell
# Reinicio completo
python init_db.py && python app.py

# Ver logs de Flask
$env:FLASK_ENV="development"
$env:FLASK_DEBUG=1
python app.py

# Ejecutar shell interactivo
python
>>> from app import app, db
>>> from models import *
>>> app.app_context().push()
# Ahora puedes hacer consultas
>>> Usuario.query.all()
```

---

## 📞 Comandos de Ayuda

```powershell
# Ayuda de Flask
flask --help

# Ayuda de pip
pip --help

# Versión de Python
python --version

# Versión de pip
pip --version

# Lista de paquetes instalados
pip list
```

---

## 🔗 URLs Importantes

- **Aplicación Local:** http://localhost:5000
- **Login:** http://localhost:5000/auth/login
- **Dashboard Profesor:** http://localhost:5000/profesor/dashboard
- **Dashboard Estudiantes:** http://localhost:5000/estudiante/dashboard

---

## 📚 Documentación

- **Flask:** https://flask.palletsprojects.com/
- **SQLAlchemy:** https://www.sqlalchemy.org/
- **Bootstrap:** https://getbootstrap.com/
- **Chart.js:** https://www.chartjs.org/

---

**Última actualización:** Noviembre 2025
