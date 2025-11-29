# Roadmap de Desarrollo - ERP Educativo Supply Chain

## ✅ Completado

### Backend
- [x] Estructura base de la aplicación Flask
- [x] Modelos de base de datos completos
- [x] Sistema de autenticación diferenciado
- [x] Rutas para profesor (control de simulación)
- [x] Rutas para estudiantes (4 roles)
- [x] Motor básico de simulación
- [x] Procesamiento de días
- [x] Cálculo de métricas básicas

### Frontend
- [x] Plantilla base con Bootstrap 5
- [x] Página de login
- [x] Dashboard principal del profesor
- [x] Estilos CSS personalizados
- [x] JavaScript básico

### Configuración
- [x] Requirements.txt
- [x] .gitignore
- [x] Script de inicialización de BD
- [x] README completo
- [x] Guía de inicio

---

## 🔨 Por Implementar

### Prioridad Alta

#### 1. Plantillas HTML del Profesor

**Archivo:** `templates/profesor/empresas.html`
```html
- Vista para listar empresas
- Formulario para crear nueva empresa
- Editar capital inicial
- Activar/desactivar empresas
```

**Archivo:** `templates/profesor/estudiantes.html`
```html
- Lista de todos los estudiantes
- Formulario de creación de estudiante
- Asignación de rol y empresa
- Resetear contraseñas
- Ver actividad de cada estudiante
```

**Archivo:** `templates/profesor/escenarios.html`
```html
- Lista de escenarios disponibles
- Botones para activar/desactivar
- Crear nuevos escenarios personalizados
- Ver efectos de cada escenario
```

**Archivo:** `templates/profesor/reportes.html`
```html
- Gráficos de desempeño por empresa
- Comparativa entre equipos
- Ranking de empresas
- Métricas individuales por rol
- Exportar reportes en PDF/Excel
```

#### 2. Dashboards Completos de Estudiantes

**Carpeta:** `templates/estudiante/ventas/`
- `dashboard.html` - Vista principal
- `historico.html` - Histórico de ventas
- `productos.html` - Análisis por producto

**Carpeta:** `templates/estudiante/planeacion/`
- `dashboard.html` - Vista principal
- `pronosticos.html` - Gestión de pronósticos
- `analisis.html` - Análisis de demanda

**Carpeta:** `templates/estudiante/compras/`
- `dashboard.html` - Vista principal (YA REFERENCIADA)
- `ordenes.html` - Gestión de órdenes
- `proveedores.html` - Información de proveedores

**Carpeta:** `templates/estudiante/logistica/`
- `dashboard.html` - Vista principal (YA REFERENCIADA)
- `inventarios.html` - Control detallado
- `transito.html` - Órdenes en tránsito

#### 3. Funcionalidades del Motor de Simulación

```python
# En routes/profesor.py - mejorar procesar_dia()
- Aplicar efectos de escenarios activos
- Generar eventos aleatorios
- Calcular costos de almacenamiento
- Calcular costos de transporte
- Penalizar ventas perdidas
```

#### 4. Sistema de Notificaciones

```python
# Crear models.py → Notificacion
- Notificar a estudiantes cuando:
  * Llega una orden de compra
  * Inventario bajo punto de reorden
  * Se activa un escenario
  * El profesor avanza el día
  * Capital insuficiente
```

### Prioridad Media

#### 5. Gráficos Interactivos

```javascript
// En cada dashboard
- Gráfico de evolución de ventas
- Gráfico de rotación de inventario
- Gráfico de utilidades por día
- Gráfico comparativo entre empresas
- Gráfico de nivel de servicio
```

#### 6. Validaciones Mejoradas

```python
# Backend
- Validar que hay suficiente capital para comprar
- Validar tiempos de entrega realistas
- Validar que el inventario no sea negativo
- Validar que los precios sean coherentes
```

```javascript
// Frontend
- Validar formularios antes de enviar
- Mostrar errores en tiempo real
- Prevenir envío de formularios incompletos
```

#### 7. Sistema de Exportación

```python
# Nuevas rutas en profesor.py
@bp.route('/exportar/excel')
def exportar_excel():
    # Exportar todas las métricas a Excel
    
@bp.route('/exportar/pdf')
def exportar_pdf():
    # Generar reporte PDF
```

### Prioridad Baja

#### 8. Sistema de Gamificación

```python
# Crear models.py → Logro
- Logros por alcanzar metas
- Sistema de puntos
- Badges y recompensas
- Tabla de clasificación
```

#### 9. Chat entre Equipo

```python
# Crear sistema de mensajería
- Chat entre miembros de la misma empresa
- Notificaciones en tiempo real
- Historial de mensajes
```

#### 10. Tutorial Interactivo

```javascript
// Sistema de onboarding
- Tutorial paso a paso para cada rol
- Tooltips interactivos
- Guía contextual
```

---

## 📝 Tareas Específicas por Implementar

### Para el Rol VENTAS

**Vista actual:** Solo estructura básica

**Necesita:**
1. **Tabla de productos con análisis**
   - Producto más vendido
   - Producto con más ventas perdidas
   - Tendencias de demanda

2. **Gráfico de ventas**
   - Ventas por día
   - Ventas por producto
   - Comparativa vs otras empresas

3. **Configuración de precios** (futura funcionalidad)
   - Ajustar precios según demanda
   - Promociones especiales
   - Descuentos por volumen

### Para el Rol PLANEACIÓN

**Vista actual:** Solo estructura básica

**Necesita:**
1. **Herramienta de pronósticos**
   - Calcular promedio móvil
   - Suavizamiento exponencial
   - Visualizar tendencias

2. **Análisis ABC de inventarios**
   - Clasificar productos por importancia
   - Recomendar niveles de stock

3. **Dashboard de KPIs**
   - Exactitud de pronósticos
   - Rotación de inventario
   - Días de inventario

### Para el Rol COMPRAS

**Vista actual:** Básica implementada

**Necesita mejorar:**
1. **Calculadora de EOQ** (Cantidad Económica de Pedido)
   - Calcular cantidad óptima
   - Minimizar costos totales

2. **Gestión de proveedores**
   - Comparar precios
   - Evaluar tiempos de entrega
   - Calificar proveedores

3. **Presupuesto de compras**
   - Ver capital disponible
   - Proyectar gastos futuros
   - Alertas de presupuesto

### Para el Rol LOGÍSTICA

**Vista actual:** Básica implementada

**Necesita mejorar:**
1. **Mapa de inventarios**
   - Visualización gráfica de niveles
   - Códigos de color según estado

2. **Simulador de políticas**
   - Probar diferentes puntos de reorden
   - Ver impacto en costos

3. **Análisis de costos**
   - Costo de almacenamiento
   - Costo de faltantes
   - Optimización de costos totales

---

## 🎨 Mejoras de UI/UX

### Dashboards
- [ ] Agregar widgets interactivos
- [ ] Implementar drag & drop para personalizar
- [ ] Modo oscuro/claro
- [ ] Responsive design mejorado

### Navegación
- [ ] Breadcrumbs en todas las páginas
- [ ] Menú lateral colapsable
- [ ] Búsqueda global
- [ ] Accesos rápidos

### Feedback Visual
- [ ] Loading states
- [ ] Progress bars
- [ ] Animaciones suaves
- [ ] Confirmaciones visuales

---

## 🔐 Seguridad y Optimización

### Seguridad
- [ ] Hash de contraseñas (ya implementado)
- [ ] CSRF protection
- [ ] Rate limiting
- [ ] Validación de inputs
- [ ] Sanitización de datos

### Optimización
- [ ] Caché de consultas frecuentes
- [ ] Paginación de tablas grandes
- [ ] Lazy loading de imágenes
- [ ] Minificación de CSS/JS
- [ ] Compresión de respuestas

---

## 🧪 Testing

### Tests Unitarios
```python
# Crear tests/test_models.py
- Test creación de usuarios
- Test cálculos de métricas
- Test procesamiento de días

# Crear tests/test_routes.py
- Test login
- Test autorización por roles
- Test endpoints de API
```

### Tests de Integración
```python
# Crear tests/test_simulation.py
- Test flujo completo de simulación
- Test interacción entre roles
- Test escenarios
```

---

## 📦 Deployment

### Preparación para Producción
- [ ] Configurar variables de entorno
- [ ] Usar base de datos PostgreSQL
- [ ] Configurar servidor WSGI (Gunicorn)
- [ ] Configurar reverse proxy (Nginx)
- [ ] SSL/HTTPS
- [ ] Backups automáticos

### Opciones de Hosting
- [ ] Heroku (fácil, gratis para empezar)
- [ ] PythonAnywhere (Python-specific)
- [ ] DigitalOcean (más control)
- [ ] AWS/Azure (enterprise)

---

## 📊 Métricas a Implementar

### Métricas Financieras
- [x] Ingresos por día (básico)
- [x] Costos por día (básico)
- [x] Utilidad (básico)
- [ ] ROI (Return on Investment)
- [ ] Margen de contribución
- [ ] Punto de equilibrio

### Métricas Operativas
- [x] Nivel de servicio (básico)
- [ ] Fill rate
- [ ] OTIF (On Time In Full)
- [ ] Lead time promedio
- [ ] Tiempo de ciclo

### Métricas de Inventario
- [ ] Rotación de inventario (implementar fórmula)
- [ ] Días de inventario
- [ ] Valor del inventario
- [ ] Exactitud de inventario
- [ ] Costo de mantenimiento

---

## 🎯 Objetivos de Aprendizaje

### Para Estudiantes
Los estudiantes deberán aprender a:
- ✅ Trabajar en equipo
- ✅ Tomar decisiones basadas en datos
- ✅ Entender interdependencia de roles
- [ ] Calcular métricas de desempeño
- [ ] Crear pronósticos de demanda
- [ ] Optimizar inventarios
- [ ] Gestionar restricciones
- [ ] Responder a disrupciones

### Para Profesores
Los profesores podrán:
- ✅ Monitorear desempeño en tiempo real
- ✅ Controlar el ritmo de la simulación
- ✅ Activar escenarios
- [ ] Exportar resultados
- [ ] Personalizar parámetros
- [ ] Evaluar competencias
- [ ] Identificar áreas de mejora

---

## 🚀 Próximos Pasos Recomendados

1. **Completar dashboards de estudiantes** (más urgente)
2. **Mejorar motor de simulación** (agregar escenarios)
3. **Implementar gráficos** (visualización de datos)
4. **Agregar notificaciones** (mejor UX)
5. **Crear sistema de reportes** (evaluación)

---

## 💡 Ideas Futuras

- **Modo competitivo**: Empresas compiten entre sí
- **Mercado dinámico**: Precios varían según oferta/demanda
- **Proveedores múltiples**: Negociar con diferentes proveedores
- **Clientes diferenciados**: B2B vs B2C
- **Eventos climáticos**: Afectan logística
- **Cambios regulatorios**: Nuevas normas/impuestos
- **Innovación tecnológica**: Mejoras de procesos
- **Modo campaña**: Escenarios progresivos
- **Integración con ERP real**: SAP, Oracle
- **ML para pronósticos**: Machine Learning avanzado

---

**Última actualización:** Noviembre 2025
**Estado:** Versión Alpha - Funcional pero incompleta
**Prioridad:** Completar dashboards de estudiantes
