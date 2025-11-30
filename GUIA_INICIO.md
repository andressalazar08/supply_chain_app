# Guía de Inicio Rápido - ERP Educativo Supply Chain

## 🚀 Pasos para Iniciar la Aplicación

### 1. Instalar Python
Si no tienes Python instalado:
- Descarga Python 3.8 o superior desde: https://www.python.org/downloads/
- Durante la instalación, marca la opción "Add Python to PATH"

### 2. Abrir Terminal en la Carpeta del Proyecto
- Abre PowerShell en la carpeta `supply_chain_app`
- O desde VS Code: Terminal → New Terminal

### 3. Crear y Activar Entorno Virtual

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (PowerShell)
venv\Scripts\activate

# Deberías ver (venv) al inicio de tu línea de comandos
```

### 4. Instalar Dependencias

```powershell
pip install -r requirements.txt
```

Esto instalará:
- Flask (framework web)
- Flask-SQLAlchemy (base de datos)
- Flask-Login (autenticación)
- Werkzeug (seguridad)

### 5. Inicializar Base de Datos

```powershell
python init_db.py
```

Esto creará:
- ✅ Base de datos SQLite
- ✅ Usuario administrador
- ✅ 3 empresas de ejemplo
- ✅ 12 estudiantes (4 por empresa)
- ✅ 5 productos de ejemplo
- ✅ Inventarios iniciales
- ✅ 4 escenarios de ejemplo

### 6. Iniciar la Aplicación

```powershell
python app.py
```

Deberías ver:
```
* Running on http://127.0.0.1:5000
* Running on http://0.0.0.0:5000
```

### 7. Acceder desde el Navegador

Abre tu navegador y ve a: **http://localhost:5000**

---

## 👤 Credenciales de Acceso

### 👨‍🏫 Profesor (Administrador)
```
Usuario: admin
Contraseña: admin123
```

**Funciones del Profesor:**
- ✅ Control de simulación (iniciar, pausar, avanzar días)
- ✅ Gestión de empresas
- ✅ Gestión de estudiantes
- ✅ Activación de escenarios
- ✅ Monitoreo de desempeño
- ✅ Generación de reportes

### 👨‍🎓 Estudiantes

**Formato:** `estudiante_[ROL]_[EMPRESA]`
**Contraseña:** `estudiante123`

**Roles disponibles:**
- 1 = Ventas
- 2 = Planeación
- 3 = Compras
- 4 = Logística

**Usuarios creados automáticamente:**

**Empresa 1 (Distribuidora Alpha):**
- `estudiante_1_1` → Ventas
- `estudiante_2_1` → Planeación
- `estudiante_3_1` → Compras
- `estudiante_4_1` → Logística

**Empresa 2 (Comercializadora Beta):**
- `estudiante_1_2` → Ventas
- `estudiante_2_2` → Planeación
- `estudiante_3_2` → Compras
- `estudiante_4_2` → Logística

**Empresa 3 (Logística Gamma):**
- `estudiante_1_3` → Ventas
- `estudiante_2_3` → Planeación
- `estudiante_3_3` → Compras
- `estudiante_4_3` → Logística

---

## 📋 Funcionalidades por Rol

### 🔵 ROL: VENTAS (estudiante_1_X)
**Dashboard:** Gestión de ventas y estrategias comerciales

**Podrás:**
- Ver histórico de ventas
- Analizar demanda de productos
- Monitorear ingresos del día
- Identificar ventas perdidas por falta de stock
- Tomar decisiones de precios (próximamente)

### 🟢 ROL: PLANEACIÓN (estudiante_2_X)
**Dashboard:** Pronósticos y planificación de demanda

**Podrás:**
- Ver inventarios actuales
- Analizar histórico de ventas
- Crear pronósticos de demanda
- Planificar necesidades futuras
- Coordinar con Compras y Logística

### 🟠 ROL: COMPRAS (estudiante_3_X)
**Dashboard:** Gestión de órdenes de compra

**Podrás:**
- Crear órdenes de compra a proveedores
- Ver órdenes pendientes y en tránsito
- Gestionar presupuesto de compras
- Monitorear tiempos de entrega
- Optimizar costos de adquisición

### 🟡 ROL: LOGÍSTICA (estudiante_4_X)
**Dashboard:** Control de inventarios y distribución

**Podrás:**
- Monitorear niveles de inventario
- Configurar puntos de reorden
- Definir stock de seguridad
- Recibir alertas de inventario bajo
- Coordinar entregas de proveedores

---

## 🎮 Cómo Funciona la Simulación

### 1. Estado Inicial
- La simulación inicia en **Día 1** y en estado **PAUSADO**
- Cada empresa tiene **$1,000,000** de capital inicial
- Inventario inicial de **100 unidades** por producto

### 2. Control del Profesor
Solo el profesor puede:
- **Iniciar** la simulación
- **Avanzar** al siguiente día
- **Pausar** o **Finalizar** la simulación
- **Activar** escenarios especiales

### 3. Mecánica de Juego

**Cada día que avance el profesor:**

1. **Se genera demanda aleatoria** para cada producto
2. **Se procesan las ventas:**
   - Si hay stock → se vende
   - Si no hay stock → venta perdida
3. **Se actualizan inventarios**
4. **Llegan órdenes de compra** programadas
5. **Se calculan métricas:**
   - Ingresos del día
   - Costos del día
   - Utilidad
   - Nivel de servicio (% ventas cumplidas)
6. **Se actualizan rankings**

### 4. Decisiones de los Estudiantes

**Entre avances de días, los estudiantes deben:**

**Ventas:**
- Analizar qué productos se venden más
- Identificar oportunidades de mercado

**Planeación:**
- Crear pronósticos de demanda
- Planificar necesidades de inventario

**Compras:**
- Crear órdenes de compra basadas en pronósticos
- Considerar tiempos de entrega (1-4 días según producto)
- Gestionar el capital disponible

**Logística:**
- Ajustar puntos de reorden
- Optimizar niveles de stock de seguridad
- Evitar quiebres de stock

---

## 📊 Productos Disponibles

| Código | Producto | Precio | Costo | Demanda Promedio | Tiempo Entrega |
|--------|----------|--------|-------|------------------|----------------|
| PROD001 | Laptop Empresarial | $1,200 | $800 | 50 unidades/día | 3 días |
| PROD002 | Monitor LED 24" | $300 | $200 | 80 unidades/día | 2 días |
| PROD003 | Teclado Mecánico | $150 | $100 | 100 unidades/día | 1 día |
| PROD004 | Mouse Inalámbrico | $50 | $30 | 150 unidades/día | 1 día |
| PROD005 | Impresora Multifuncional | $400 | $280 | 30 unidades/día | 4 días |

**Nota:** La demanda real varía cada día según la desviación estándar configurada.

---

## 🎯 Escenarios Disponibles

El profesor puede activar estos escenarios en cualquier momento:

1. **Pico de Demanda - Black Friday**
   - Aumenta demanda 50%
   - Oportunidad de mayores ventas

2. **Huelga de Transportadores**
   - Retrasa entregas 2 días
   - Afecta órdenes de compra

3. **Crisis de Abastecimiento**
   - Aumenta costos 30%
   - Reduce márgenes de utilidad

4. **Promoción Especial**
   - Aumenta margen 20%
   - Oportunidad temporal

---

## 🔧 Solución de Problemas

### Error: "No module named flask"
```powershell
# Asegúrate de tener el entorno virtual activado
venv\Scripts\activate

# Reinstala las dependencias
pip install -r requirements.txt
```

### Error: "Port 5000 already in use"
```powershell
# Cierra otros procesos o cambia el puerto en app.py
# Línea final: app.run(debug=True, host='0.0.0.0', port=5001)
```

### Error: "Unable to open database file"
```powershell
# Reinicia la base de datos
python init_db.py
```

### La página no carga
```powershell
# Verifica que la aplicación esté corriendo
# Deberías ver: "Running on http://127.0.0.1:5000"
# Si no, ejecuta: python app.py
```

---

## 📝 Próximos Pasos de Desarrollo

### Pendiente por Implementar:

1. **Plantillas HTML faltantes:**
   - `templates/profesor/empresas.html`
   - `templates/profesor/estudiantes.html`
   - `templates/profesor/escenarios.html`
   - `templates/profesor/reportes.html`
   - Dashboards completos de estudiantes

2. **Funcionalidades adicionales:**
   - Sistema de notificaciones en tiempo real
   - Gráficos interactivos (Chart.js)
   - Exportación de reportes
   - Chat entre equipo
   - Sistema de logros/gamificación

3. **Mejoras de UX:**
   - Tutoriales interactivos
   - Tooltips explicativos
   - Validaciones de formularios
   - Confirmaciones de acciones críticas

---

## 💡 Consejos para Estudiantes

1. **Trabajen en equipo** - Cada rol es importante
2. **Comuníquense** - Compras debe saber los pronósticos de Planeación
3. **Planifiquen con anticipación** - Los productos tardan en llegar
4. **No se queden sin stock** - Ventas perdidas = menos utilidad
5. **Cuiden el capital** - No gasten todo el dinero de golpe
6. **Analicen los datos** - Usen el histórico para tomar decisiones

---

## 📞 Soporte

Si tienes problemas técnicos:
1. Revisa esta guía primero
2. Verifica que seguiste todos los pasos
3. Consulta al profesor/administrador

---

**¡Buena suerte con la simulación! 🚀📦**
