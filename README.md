# Simulación de Cadena de Abastecimiento - ERP Educativo

Aplicación web gamificada para la enseñanza de gestión de cadena de abastecimiento en un entorno empresarial simulado.

## Características Principales

### 🎓 Sistema de Roles
- **Profesor (Admin)**: Control total de la simulación
- **Estudiantes**: 4 roles funcionales
  - Ventas
  - Planeación
  - Compras
  - Logística

### 🎮 Mecánica de Simulación
- Simulación por días controlados por el profesor
- Cada equipo representa una empresa distribuidora
- Decisiones basadas en datos reales
- Restricciones logísticas y disrupciones del entorno
- Sistema de métricas y KPIs

### 📊 Funcionalidades
- Gestión de inventarios
- Pronósticos de demanda
- Órdenes de compra
- Control logístico
- Reportes de desempeño
- Escenarios y disrupciones

## Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <url-repositorio>
cd supply_chain_app
```

2. **Crear entorno virtual**
```bash
python -m venv venv
```

3. **Activar entorno virtual**
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Inicializar base de datos**
```bash
python init_db.py
```

6. **Iniciar la aplicación**
```bash
python app.py
```

7. **Acceder a la aplicación**
Abrir navegador en: `http://localhost:5000`

## Credenciales de Acceso

### Profesor (Administrador)
- Usuario: `admin`
- Contraseña: `admin123`

### Estudiantes
Formato: `estudiante_[rol]_[empresa]`

Roles:
- 1 = Ventas
- 2 = Planeación
- 3 = Compras
- 4 = Logística

Ejemplos:
- `estudiante_1_1` → Ventas de Empresa 1
- `estudiante_2_1` → Planeación de Empresa 1
- `estudiante_3_2` → Compras de Empresa 2
- `estudiante_4_3` → Logística de Empresa 3

**Contraseña por defecto:** `estudiante123`

## Estructura del Proyecto

```
supply_chain_app/
│
├── app.py                 # Aplicación principal
├── models.py              # Modelos de base de datos
├── init_db.py             # Script de inicialización
├── requirements.txt       # Dependencias
│
├── routes/                # Rutas de la aplicación
│   ├── auth.py           # Autenticación
│   ├── profesor.py       # Rutas del profesor
│   └── estudiante.py     # Rutas de estudiantes
│
├── templates/             # Plantillas HTML
│   ├── base.html
│   ├── auth/
│   │   └── login.html
│   ├── profesor/
│   │   ├── dashboard.html
│   │   ├── empresas.html
│   │   ├── estudiantes.html
│   │   ├── escenarios.html
│   │   └── reportes.html
│   └── estudiante/
│       ├── ventas/
│       ├── planeacion/
│       ├── compras/
│       └── logistica/
│
└── static/                # Archivos estáticos (CSS, JS, imágenes)
```

## Uso del Sistema

### Como Profesor

1. **Iniciar Sesión** con credenciales de admin
2. **Crear Empresas** participantes (o usar las de ejemplo)
3. **Gestionar Estudiantes** asignándoles roles y empresas
4. **Configurar Escenarios** y disrupciones
5. **Iniciar Simulación** y controlar el avance de días
6. **Monitorear Desempeño** de cada equipo en tiempo real
7. **Generar Reportes** al finalizar

### Como Estudiante

1. **Iniciar Sesión** con usuario asignado
2. **Acceder al Dashboard** específico de tu rol
3. **Tomar Decisiones** según tu función:
   - **Ventas**: Estrategias de precios y pronósticos
   - **Planeación**: Gestión de inventarios y demanda
   - **Compras**: Órdenes a proveedores
   - **Logística**: Control de inventarios y distribución
4. **Monitorear Resultados** de tus decisiones
5. **Colaborar** con tu equipo para maximizar resultados

## Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Base de Datos**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **UI Framework**: Bootstrap 5
- **Gráficos**: Chart.js
- **Autenticación**: Flask-Login
- **ORM**: SQLAlchemy

## Próximas Funcionalidades

- [ ] Sistema de gamificación con puntos y logros
- [ ] Gráficos interactivos avanzados
- [ ] Exportación de reportes en PDF/Excel
- [ ] Integración con datos reales de demanda
- [ ] Modo multijugador en tiempo real
- [ ] Análisis predictivo con machine learning
- [ ] Chat entre miembros del equipo
- [ ] Tutorial interactivo

## Contribuciones

Este es un proyecto educativo. Las contribuciones son bienvenidas.

## Licencia

Proyecto educativo - Universidad

## Soporte

Para soporte técnico o preguntas, contactar al administrador del curso.

---

**Desarrollado con ❤️ para la educación en Supply Chain Management**