# Manual del Simulador de Cadena de Abastecimiento

**Versión 1.0**  
**Fecha:** Enero 2026  
**Universidad:** Universidad del Rosario (Colores institucionales aplicados)

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Roles y Permisos](#roles-y-permisos)
4. [Módulos Funcionales](#módulos-funcionales)
5. [Sistema Económico](#sistema-económico)
6. [Motor de Simulación](#motor-de-simulación)
7. [Sistema de Disrupciones](#sistema-de-disrupciones)
8. [Métricas y KPIs](#métricas-y-kpis)
9. [Flujos de Trabajo](#flujos-de-trabajo)
10. [Configuración y Administración](#configuración-y-administración)
11. [Casos de Uso](#casos-de-uso)
12. [Resolución de Problemas](#resolución-de-problemas)

---

## 1. Introducción

### 1.1 Objetivo del Simulador

El Simulador de Cadena de Abastecimiento es una plataforma educativa diseñada para:

- **Simular operaciones reales** de una empresa de distribución en Colombia
- **Enseñar toma de decisiones** en entornos de mercado competitivo
- **Desarrollar competencias** en gestión de inventarios, ventas, compras y logística
- **Evaluar desempeño** mediante métricas financieras y operativas realistas

### 1.2 Conceptos Básicos

- **Simulación**: Escenario de juego con duración definida (típicamente 30 días simulados)
- **Empresa**: Equipo de estudiantes que compite en el mercado
- **Día de Simulación**: Unidad temporal donde se procesan ventas, compras y operaciones
- **Disrupción**: Evento externo que afecta las operaciones (retrasos, aumentos de demanda, etc.)
- **Capital**: Recursos financieros disponibles para la empresa

### 1.3 Características Principales

- ✅ **Mercado competitivo multiempresa** con precios dinámicos
- ✅ **Distribución geográfica** por 5 regiones de Colombia
- ✅ **Sistema de costos realista** (mantenimiento, sobrestock, oportunidad)
- ✅ **Disrupciones configurables** por el profesor
- ✅ **Procesamiento automático** día a día
- ✅ **Dashboards en tiempo real** para estudiantes y profesores
- ✅ **Nivel de servicio acumulativo** basado en desempeño histórico

---

## 2. Arquitectura del Sistema

### 2.1 Stack Tecnológico

```
Frontend:
- HTML5 + Bootstrap 5.3
- JavaScript Vanilla + Chart.js 4.3
- Font Awesome 6.4 (iconografía)
- CSS3 con variables custom (tema rojo universitario)

Backend:
- Flask 3.0 (Python)
- SQLAlchemy ORM
- Flask-Login (autenticación)
- Flask-Mail (notificaciones)

Base de Datos:
- SQLite (desarrollo)
- Estructura relacional normalizada
```

### 2.2 Estructura de Carpetas

```
fullstack/
├── app.py                    # Aplicación principal Flask
├── config.py                 # Configuración de la app
├── extensions.py             # Extensiones (db, login_manager)
├── models.py                 # Modelos de base de datos
├── init_db.py               # Inicialización de BD
├── routes/
│   ├── auth.py              # Autenticación
│   ├── estudiante.py        # Rutas de estudiantes
│   └── profesor.py          # Rutas de profesores
├── utils/
│   ├── procesamiento_dias.py  # Motor de simulación
│   ├── disrupciones.py        # Gestión de eventos
│   ├── inventario.py          # Cálculos de inventario
│   ├── logistica.py           # Despachos y movimientos
│   └── pronosticos.py         # Predicciones de demanda
├── templates/               # Plantillas HTML
└── static/                  # Archivos estáticos (CSS, JS)
```

### 2.3 Modelo de Datos

#### Entidades Principales

**Usuario**
- Estudiantes y profesores
- Roles: ventas, compras, planeación, logística, admin, super_admin
- Vinculación a empresa (estudiantes) o gestión (profesores)

**Empresa**
- Representa un equipo de estudiantes
- Capital inicial: $50,000,000 (configurable)
- Vinculada a una simulación específica

**Simulación**
- Controla el estado global del juego
- Estados: pausado, en_curso, finalizado
- Día actual (1-30 típicamente)
- Solo una simulación activa a la vez

**Producto**
- 3 productos por defecto: Producto A, B, C
- Atributos: precio_base, costo_compra, demanda_promedio, stock_inicial
- stock_maximo = demanda_promedio × 7 días

**Inventario**
- Cantidad actual y reservada por empresa/producto
- Costo unitario promedio (weighted average)
- Actualización en tiempo real

**Venta**
- Registro de cada transacción de venta
- Región, cantidad solicitada vs vendida
- Precio de venta, ganancia/pérdida
- Nivel de servicio individual

**Compra**
- Órdenes a proveedores
- Lead time (3-5 días típicamente)
- Estado: pendiente, en_transito, recibida
- Tracking de fecha esperada vs real

**DespachoRegional**
- Envíos de inventario central a regiones
- Estado: preparacion, en_transito, entregado
- Tracking de fechas

**DisrupcionActiva**
- Eventos aplicados por el profesor
- Tipos: retraso_proveedor, aumento_demanda, caida_demanda, region_bloqueada, aumento_costos
- Severidad: baja, media, alta, crítica
- Duración y efectos específicos

**Metrica**
- Registro diario de KPIs por empresa
- Capital, ventas totales, nivel de servicio, rotación inventario
- ROI, margen bruto, etc.

---

## 3. Roles y Permisos

### 3.1 Super Administrador

**Capacidades:**
- Crear y gestionar profesores
- Acceso total al sistema
- Configuración global

**Acceso:** Panel de super administración

### 3.2 Profesor

**Capacidades:**
- Crear escenarios de simulación
- Configurar parámetros iniciales (capital, duración, productos)
- Aplicar disrupciones
- Avanzar días de simulación
- Monitorear todas las empresas
- Ver rankings y comparativas
- Generar reportes

**Dashboard:**
- Vista de todas las empresas
- Control de avance de días
- Panel de disrupciones activas
- Gráficos comparativos

### 3.3 Estudiante - Rol Administrador (Admin)

**Capacidades:**
- Configurar precios de productos
- Asignar roles a compañeros de equipo
- Ver todos los módulos de la empresa
- Tomar decisiones estratégicas

**Limitaciones:**
- No puede avanzar días de simulación
- No puede crear disrupciones

### 3.4 Estudiante - Rol Ventas

**Capacidades:**
- Ver dashboard de ventas
- Analizar demanda por región
- Consultar análisis regional
- Ver histórico de ventas
- Visualizar nivel de servicio

**Limitaciones:**
- No puede modificar precios (solo Admin)
- No puede hacer compras ni despachos

### 3.5 Estudiante - Rol Compras

**Capacidades:**
- Crear órdenes de compra
- Ver dashboard de compras
- Consultar requerimientos de inventario
- Tracking de órdenes pendientes
- Ver proveedores y lead times

**Limitaciones:**
- No puede modificar inventario directamente
- No puede despachar a regiones

### 3.6 Estudiante - Rol Logística

**Capacidades:**
- Gestionar despachos a regiones
- Realizar movimientos de inventario (ajustes)
- Ver recepción de compras
- Monitorear stock por ubicación

**Limitaciones:**
- No puede crear compras
- No puede ver márgenes de ventas (confidencial)

### 3.7 Estudiante - Rol Planeación

**Capacidades:**
- Ver dashboard general
- Consultar métricas financieras
- Analizar pronósticos de demanda
- Visualizar tendencias

**Limitaciones:**
- No puede ejecutar acciones operativas
- Rol de análisis y recomendación

---

## 4. Módulos Funcionales

### 4.1 Módulo de Ventas

#### Dashboard de Ventas
- **Ventas Totales del Día**: Suma de ingresos del día actual
- **Demanda del Día**: Cantidad total solicitada
- **Nivel de Servicio Acumulativo**: % de demanda satisfecha desde el inicio
- **Gráfico de Ventas**: Histórico de últimos 7 días
- **Top Productos**: Ranking por ingresos

#### Análisis Regional
Muestra para cada región de Colombia:
- **Región Caribe**: Color distintivo en el mapa
- **Región Andina**: Mayor concentración de demanda
- **Región Pacífica**: Puerto de entrada de importaciones
- **Región Orinoquía**: Color rojo (#c41e3a)
- **Región Amazonía**: Menor demanda, mayor lead time
- **Región Insular**: Restricciones logísticas

**Información por Región:**
- Demanda promedio diaria
- Ventas acumuladas
- Nivel de servicio regional
- Stock disponible en la región

#### Fórmulas Clave

**Nivel de Servicio Acumulativo:**
```
Nivel_Servicio = (Suma_Cantidad_Vendida / Suma_Cantidad_Solicitada) × 100
```
Donde:
- Suma sobre TODAS las ventas desde el día 1
- Refleja el desempeño histórico real
- Se actualiza cada día

**Demanda Mínima Garantizada por Empresa:**
```
Demanda_Base = Demanda_Promedio_Producto × 0.6
```
- Cada empresa recibe al menos el 60% de la demanda promedio
- El 40% restante se distribuye competitivamente según precio y stock

### 4.2 Módulo de Compras

#### Dashboard de Compras
- **Órdenes Activas**: Compras pendientes y en tránsito
- **Valor en Tránsito**: Capital comprometido en compras
- **Próximas Recepciones**: Alertas de llegadas
- **Gráfico de Compras**: Histórico de órdenes

#### Creación de Órdenes
**Campos:**
- Producto (A, B, o C)
- Cantidad a ordenar
- Proveedor (afecta lead time y costo)

**Validaciones:**
- Capital suficiente disponible
- Cantidad > 0
- Proveedor válido

**Proceso:**
1. Se crea la orden con estado "pendiente"
2. Se descuenta el capital inmediatamente
3. Se calcula fecha_esperada = día_actual + lead_time
4. Al llegar el día esperado, se recibe automáticamente
5. Estado cambia a "recibida" y se actualiza inventario

#### Lead Time

**Por Proveedor:**
- Proveedor Local: 3 días
- Proveedor Nacional: 5 días
- Proveedor Internacional: 7 días

**Con Disrupción "Retraso de Proveedores":**
- Baja: +2 días adicionales
- Media: +5 días adicionales
- Alta: +10 días adicionales
- Crítica: +15 días adicionales

#### Requerimientos de Inventario
Muestra sugerencias de compra basadas en:
- Stock actual vs stock_maximo (demanda × 7)
- Tasa de rotación
- Ventas recientes
- Stock de seguridad

### 4.3 Módulo de Logística

#### Dashboard Logística
- **Inventario Central**: Stock en bodega principal
- **Inventario Regional**: Distribución por regiones
- **Despachos Activos**: Envíos en tránsito
- **Alertas de Stock Bajo**: Regiones con < 20% stock

#### Despacho a Regiones
**Flujo:**
1. Seleccionar región destino
2. Seleccionar productos y cantidades
3. Validar stock disponible en central
4. Crear despacho con estado "preparacion"
5. Automáticamente pasa a "en_transito" (1 día de preparación)
6. Llega a región en fecha_entrega estimada
7. Estado cambia a "entregado"

**Lead Time de Despacho:**
- Región cercana (Andina): 1 día
- Región media (Caribe, Pacífica): 2 días
- Región lejana (Orinoquía, Amazonía): 3-4 días
- Región Insular: 5 días (transporte marítimo)

#### Movimientos de Inventario
Permite ajustes manuales:
- **Tipo Ajuste**: Incremento / Decremento / Corrección / Devolución
- **Razón**: Campo de texto obligatorio
- **Cantidad**: Positiva o negativa
- **Ubicación**: Central o Regional

**Casos de Uso:**
- Corrección de errores
- Producto dañado
- Devoluciones de clientes
- Mermas

#### Recepción de Compras
Vista de solo lectura:
- Compras que llegaron hoy
- Compras en tránsito con fecha estimada
- Histórico de recepciones

### 4.4 Módulo de Planeación

#### Dashboard General (Planeación)
- **Capital Actual**: Recursos financieros disponibles
- **Inventario Total Valorizado**: Suma (cantidad × costo_unitario)
- **ROI Acumulado**: Retorno sobre inversión
- **Margen Bruto**: (Ventas - Costos) / Ventas × 100

#### Gráficos Analíticos
- **Evolución del Capital**: Tendencia día a día
- **Composición de Costos**: Pie chart (fijos, mantenimiento, sobrestock, oportunidad)
- **Pronóstico de Demanda**: Predicción para próximos 7 días
- **Rotación de Inventario**: Días de cobertura por producto

#### Pronósticos
El sistema genera pronósticos usando:
- **Media móvil simple** (últimos 7 días)
- **Tendencia lineal** (regresión simple)
- **Ajuste por estacionalidad** (día de la semana)
- **Factor de disrupciones activas**

---

## 5. Sistema Económico

### 5.1 Capital Inicial

**Configuración por Defecto:**
- Capital inicial: **$50,000,000** (cincuenta millones de pesos)
- Configurable por el profesor al crear la simulación

**Uso del Capital:**
- Compra de inventario inicial
- Reposición de stock
- Absorción de costos operativos
- Cobertura de penalizaciones

### 5.2 Costos Operativos

El sistema calcula automáticamente cada día:

#### 5.2.1 Costos Fijos
```
Costo_Fijo_Diario = $800,000
```
- Aplica todos los días automáticamente
- Representa: salarios, alquiler, servicios, etc.
- No depende del volumen de operaciones

#### 5.2.2 Costos de Mantenimiento de Inventario
```
Costo_Mantenimiento = Valor_Inventario_Total × 0.003 (0.3%)
```
- Se calcula sobre el inventario valorizado al final del día
- Incluye: almacenamiento, seguros, depreciación
- Incentiva mantener inventarios óptimos

**Ejemplo:**
- Inventario valorizado: $10,000,000
- Costo diario: $10,000,000 × 0.003 = $30,000

#### 5.2.3 Penalización por Sobrestock
```
Sobrestock = MAX(0, Cantidad_Actual - Stock_Maximo)
Penalizacion = Sobrestock × Costo_Unitario × 0.005 (0.5%)
```
- Aplica solo cuando inventario > stock_maximo
- stock_maximo = demanda_promedio × 7 días
- Penaliza tener inventario excesivo

**Ejemplo:**
- Producto A: demanda_promedio = 100, stock_maximo = 700
- Inventario actual: 1,000 unidades
- Sobrestock: 1,000 - 700 = 300 unidades
- Costo unitario: $10,000
- Penalización: 300 × $10,000 × 0.005 = $15,000

#### 5.2.4 Penalización por Ventas Perdidas
```
Ventas_Perdidas = Cantidad_Solicitada - Cantidad_Vendida
Costo_Oportunidad = Ventas_Perdidas × Precio_Venta × 0.30 (30%)
```
- Penaliza no tener stock suficiente para satisfacer demanda
- Representa pérdida de margen y daño reputacional
- Incentiva mantener stock adecuado

**Ejemplo:**
- Demanda: 200 unidades a $50,000
- Stock disponible: 150 unidades
- Ventas perdidas: 50 unidades
- Penalización: 50 × $50,000 × 0.30 = $750,000

#### 5.2.5 Costo Total Diario
```
Costo_Total = Costo_Fijo 
            + Costo_Mantenimiento 
            + Penalizacion_Sobrestock 
            + Costo_Oportunidad
```

**Se descuenta automáticamente del capital cada día.**

### 5.3 Ingresos

#### Ventas
```
Ingreso_Venta = Cantidad_Vendida × Precio_Venta
Ganancia_Venta = Ingreso_Venta - (Cantidad_Vendida × Costo_Unitario)
```

**Se suma al capital inmediatamente al procesar el día.**

### 5.4 Flujo de Efectivo Diario

**Secuencia de Procesamiento:**
1. **Inicio del Día**: Capital = Capital_Dia_Anterior
2. **Procesar Ventas**: Capital += Ingresos_Ventas
3. **Procesar Compras**: Capital -= Valor_Compras_Recibidas (ya descontado al ordenar)
4. **Calcular Costos**: Capital -= Costos_Operativos
5. **Actualizar Métricas**: Guardar estado final

### 5.5 Indicadores Financieros

#### ROI (Return on Investment)
```
ROI = ((Capital_Actual - Capital_Inicial) / Capital_Inicial) × 100
```

#### Margen Bruto
```
Margen_Bruto = ((Ventas_Totales - Costos_Variables) / Ventas_Totales) × 100
```

#### Rotación de Inventario
```
Rotacion = Ventas_Ultimos_7_Dias / Stock_Promedio
Dias_Cobertura = 7 / Rotacion
```

---

## 6. Motor de Simulación

### 6.1 Procesamiento de Día

**Archivo:** `utils/procesamiento_dias.py`

**Función Principal:** `procesar_dia_simulacion(simulacion_id)`

#### Secuencia de Operación

```python
# 1. Validar estado de simulación
if simulacion.estado != 'en_curso':
    return Error

# 2. Avanzar día
simulacion.dia_actual += 1

# 3. Procesar recepciones de compras
for compra in compras_que_llegan_hoy:
    - Cambiar estado a "recibida"
    - Actualizar inventario
    - Crear MovimientoInventario

# 4. Procesar entregas de despachos regionales
for despacho in despachos_que_llegan_hoy:
    - Cambiar estado a "entregado"
    - Actualizar inventario regional

# 5. Generar demanda del día
for cada empresa:
    for cada producto:
        for cada region:
            - Calcular demanda_base (60% garantizada)
            - Aplicar disrupciones activas
            - Distribuir demanda competitiva (40% restante)

# 6. Procesar ventas
for cada venta_generada:
    - Verificar stock disponible
    - Reservar inventario
    - Crear registro Venta
    - Actualizar capital (ingresos)
    - Calcular ganancia/pérdida

# 7. Calcular costos operativos
for cada empresa:
    - costos_fijos
    - costos_mantenimiento
    - penalizacion_sobrestock
    - costo_oportunidad
    - Descontar del capital

# 8. Calcular métricas del día
for cada empresa:
    - nivel_servicio_acumulativo
    - ROI
    - margen_bruto
    - rotacion_inventario
    - Guardar en tabla Metrica

# 9. Verificar fin de simulación
if dia_actual >= duracion_dias:
    simulacion.estado = 'finalizado'

# 10. Commit a base de datos
db.session.commit()
```

### 6.2 Distribución de Demanda Competitiva

**Algoritmo de Market Share:**

```python
def calcular_market_share(precio_empresa, precio_promedio, stock, elasticidad):
    """
    Calcula la participación de mercado de una empresa
    basado en su competitividad de precio y disponibilidad
    """
    if stock <= 0:
        return 0  # Sin stock = sin ventas
    
    # Factor de precio (más competitivo = mayor share)
    if precio_empresa <= precio_promedio:
        factor_precio = 1 + ((precio_promedio - precio_empresa) / precio_promedio) * elasticidad
    else:
        factor_precio = 1 / (1 + ((precio_empresa - precio_promedio) / precio_promedio) * elasticidad)
    
    # Factor de stock (más stock = más confiabilidad)
    factor_stock = min(stock / 100, 1.5)  # Cap en 1.5x
    
    market_share = factor_precio * factor_stock
    return max(0, market_share)
```

**Elasticidad de Precio por Producto:**
- Producto A (Básico): 1.2 (más sensible a precio)
- Producto B (Estándar): 1.0
- Producto C (Premium): 0.8 (menos sensible a precio)

**Distribución:**
1. Calcular market_share para cada empresa
2. Normalizar (suma = 1.0)
3. Asignar demanda proporcional
4. Limitar por stock disponible
5. Redistribuir demanda no satisfecha

### 6.3 Gestión de Disrupciones Activas

**Tipos de Impacto:**

#### Retraso de Proveedores
- Afecta: Lead time de compras
- Severidad → días adicionales
- Duración: temporal (días configurables)

#### Aumento de Demanda
- Afecta: Multiplicador de demanda
- Baja: ×1.3, Media: ×1.6, Alta: ×2.0, Crítica: ×3.0
- Todas las regiones o región específica

#### Caída de Demanda
- Afecta: Multiplicador de demanda (reduce)
- Baja: ×0.8, Media: ×0.6, Alta: ×0.4, Crítica: ×0.2

#### Región Bloqueada
- Afecta: Demanda de una región específica → 0
- Impide despachos a esa región
- Duración temporal

#### Aumento de Costos
- Afecta: Costo de compra de productos
- Incremento porcentual configurable
- Todas las compras durante la duración

**Procesamiento:**
```python
def calcular_impacto_demanda(producto_id, region, empresa_id):
    disrupciones = obtener_disrupciones_activas(empresa_id)
    multiplicador_total = 1.0
    
    for disrupcion in disrupciones:
        if disrupcion.tipo == 'aumento_demanda':
            multiplicador_total *= disrupcion.multiplicador
        elif disrupcion.tipo == 'caida_demanda':
            multiplicador_total *= disrupcion.multiplicador
        elif disrupcion.tipo == 'region_bloqueada' and disrupcion.region == region:
            multiplicador_total = 0
    
    return multiplicador_total
```

---

## 7. Sistema de Disrupciones

### 7.1 Catálogo de Disrupciones

#### Retraso en Proveedores
**Icono:** 🚚 (fa-truck-loading)

**Severidades:**

| Severidad | Nombre | Descripción | Días Extra | Duración |
|-----------|--------|-------------|------------|----------|
| Baja | Tráfico | Congestión vehicular menor | +2 días | 3 días |
| Media | Vía en Mantenimiento | Obras requieren desvíos | +5 días | 7 días |
| Alta | Derrumbe | Bloqueo de vía principal | +10 días | 10 días |
| Crítica | Paro Nacional | Paralización de transporte | +15 días | 14 días |

#### Aumento en Demanda
**Icono:** 📈 (fa-chart-line)

| Severidad | Nombre | Multiplicador | Duración |
|-----------|--------|---------------|----------|
| Baja | Incremento Estacional | ×1.3 | 5 días |
| Media | Campaña Publicitaria | ×1.6 | 10 días |
| Alta | Boom de Mercado | ×2.0 | 7 días |
| Crítica | Monopolio Temporal | ×3.0 | 5 días |

#### Caída en Demanda
**Icono:** 📉 (fa-chart-line-down)

| Severidad | Nombre | Multiplicador | Duración |
|-----------|--------|---------------|----------|
| Baja | Temporada Baja | ×0.8 | 7 días |
| Media | Recesión | ×0.6 | 10 días |
| Alta | Crisis Económica | ×0.4 | 14 días |
| Crítica | Colapso de Mercado | ×0.2 | 7 días |

#### Región Bloqueada
**Icono:** 🚫 (fa-ban)

| Severidad | Efecto | Duración |
|-----------|--------|----------|
| Alta | Demanda = 0, No despachos | 7 días |
| Crítica | Demanda = 0, Pérdida de stock regional | 10 días |

#### Aumento de Costos
**Icono:** 💰 (fa-money-bill-trend-up)

| Severidad | Incremento | Duración |
|-----------|------------|----------|
| Baja | +20% costo compras | 5 días |
| Media | +40% costo compras | 7 días |
| Alta | +70% costo compras | 10 días |
| Crítica | +100% costo compras | 5 días |

### 7.2 Aplicación de Disrupciones (Profesor)

**Ruta:** `/profesor/aplicar_disrupcion`

**Parámetros:**
- `tipo`: Tipo de disrupción del catálogo
- `severidad`: baja, media, alta, critica
- `empresas[]`: IDs de empresas afectadas (puede ser "todas")
- `region`: (opcional) Para disrupciones regionales
- `duracion_dias`: (opcional) Sobrescribe duración por defecto

**Proceso:**
1. Validar que simulación esté activa
2. Crear registro DisrupcionActiva por cada empresa
3. Calcular día_fin = dia_actual + duracion
4. Guardar parámetros específicos (multiplicador, días_extra, etc.)
5. Mostrar confirmación al profesor

**Visualización:**
- Panel de "Disrupciones Activas" en dashboard profesor
- Contador de días restantes
- Empresas afectadas
- Opción de cancelar disrupción anticipadamente

### 7.3 Estrategias de Mitigación (Estudiantes)

**Para Retrasos de Proveedores:**
- Mantener stock de seguridad más alto
- Diversificar proveedores
- Anticipar órdenes de compra

**Para Aumentos de Demanda:**
- Incrementar stock previo
- Ajustar precios (aprovechar demanda)
- Priorizar productos de alto margen

**Para Caídas de Demanda:**
- Reducir precios para captar market share
- Evitar compras nuevas
- Minimizar costos de mantenimiento

**Para Región Bloqueada:**
- Redistribuir inventario a otras regiones
- No despachar a región afectada
- Esperar fin de bloqueo

**Para Aumento de Costos:**
- Ajustar precios de venta
- Reducir volumen de compras
- Usar inventario existente

---

## 8. Métricas y KPIs

### 8.1 Métricas Operativas

#### Nivel de Servicio
```
Nivel_Servicio = (Total_Vendido / Total_Solicitado) × 100
```
- **Objetivo:** ≥ 95%
- **Cálculo:** Acumulativo desde día 1
- **Impacto:** Afecta reputación y futuras ventas

#### Rotación de Inventario
```
Rotacion = Ventas_Periodo / Stock_Promedio_Periodo
Dias_Cobertura = Periodo / Rotacion
```
- **Objetivo:** 7-14 días de cobertura
- **Alerta:** > 20 días (sobrestock) o < 3 días (riesgo de quiebre)

#### Tasa de Stockout
```
Tasa_Stockout = (Dias_Con_Stockout / Total_Dias) × 100
```
- **Objetivo:** < 5%
- **Medición:** Por producto y por región

### 8.2 Métricas Financieras

#### ROI (Return on Investment)
```
ROI = ((Capital_Final - Capital_Inicial) / Capital_Inicial) × 100
```
- **Objetivo:** > 20% al final de simulación
- **Interpretación:**
  - ROI > 30%: Excelente desempeño
  - ROI 10-30%: Buen desempeño
  - ROI 0-10%: Desempeño aceptable
  - ROI < 0%: Pérdidas

#### Margen Bruto
```
Margen_Bruto = ((Ventas - Costo_Ventas) / Ventas) × 100
```
- **Objetivo:** 25-40%
- **Por Producto:**
  - Producto A (Básico): 15-25%
  - Producto B (Estándar): 25-35%
  - Producto C (Premium): 35-50%

#### EBITDA Simulado
```
EBITDA = Ventas - Costos_Variables - Costos_Fijos
```

#### Capital Circulante
```
Capital_Circulante = Capital_Efectivo + Valor_Inventario
```

### 8.3 Métricas Comparativas (Ranking)

**Dashboard Profesor muestra:**

| Empresa | Capital | ROI | Nivel Servicio | Ventas Totales | Posición |
|---------|---------|-----|----------------|----------------|----------|
| Empresa A | $65M | 30% | 96% | $85M | 1° |
| Empresa B | $58M | 16% | 92% | $72M | 2° |
| Empresa C | $52M | 4% | 88% | $65M | 3° |

**Criterios de Ranking:**
1. **Principal:** Capital actual (refleja éxito global)
2. **Secundario:** ROI (eficiencia de gestión)
3. **Terciario:** Nivel de servicio (calidad operativa)

### 8.4 Alertas Automáticas

**El sistema genera alertas cuando:**
- Capital < $5,000,000 (riesgo financiero)
- Nivel de servicio < 85% (bajo desempeño)
- Stock de producto = 0 (quiebre de stock)
- Días de cobertura > 20 (sobrestock)
- ROI < -10% (pérdidas significativas)

---

## 9. Flujos de Trabajo

### 9.1 Inicio de Simulación (Profesor)

```mermaid
1. Profesor crea nueva simulación
   ├─> Define nombre y duración (ej: 30 días)
   ├─> Configura capital inicial ($50M)
   └─> Define productos y parámetros

2. Profesor crea empresas
   ├─> Empresa A, B, C, etc.
   └─> Cada empresa inicia con capital configurado

3. Estudiantes se registran
   ├─> Completan datos académicos
   ├─> Verifican email
   └─> Se asignan a una empresa

4. Admin de empresa asigna roles
   ├─> Rol Ventas → Estudiante 1
   ├─> Rol Compras → Estudiante 2
   ├─> Rol Logística → Estudiante 3
   └─> Rol Planeación → Estudiante 4

5. Profesor inicia simulación
   └─> Estado: "en_curso"
```

### 9.2 Ciclo Diario Típico (Estudiantes)

**Día N:**

```
08:00 - ROL PLANEACIÓN analiza métricas
   ├─> Revisa capital actual
   ├─> Verifica nivel de servicio
   └─> Analiza pronósticos

09:00 - ROL VENTAS analiza demanda
   ├─> Revisa ventas del día anterior
   ├─> Identifica productos con baja rotación
   └─> Sugiere ajustes de precio (al Admin)

10:00 - ROL COMPRAS verifica inventario
   ├─> Consulta requerimientos
   ├─> Revisa compras en tránsito
   ├─> Crea órdenes si es necesario
   └─> Considera lead time y disrupciones

11:00 - ROL LOGÍSTICA gestiona distribución
   ├─> Verifica stock central vs regional
   ├─> Crea despachos a regiones con bajo stock
   └─> Confirma recepciones esperadas

12:00 - ROL ADMIN toma decisiones estratégicas
   ├─> Ajusta precios si es necesario
   ├─> Aprueba compras grandes
   └─> Coordina con el equipo

NOCHE - PROFESOR avanza el día
   └─> Sistema procesa automáticamente:
       ├─> Ventas
       ├─> Recepciones
       ├─> Costos
       └─> Métricas
```

### 9.3 Respuesta a Disrupción

**Escenario: Profesor aplica "Aumento de Demanda - Severidad Alta"**

```
DÍA 15 - DISRUPCIÓN APLICADA
├─> Sistema notifica a empresas afectadas
├─> Multiplicador de demanda: ×2.0
└─> Duración: 7 días

RESPUESTA ESTUDIANTES:

ROL PLANEACIÓN:
├─> Alerta al equipo sobre aumento
└─> Calcula inventario necesario

ROL COMPRAS:
├─> Crea órdenes urgentes de productos
├─> Prioriza proveedores con menor lead time
└─> Reserva capital para la oportunidad

ROL LOGÍSTICA:
├─> Distribuye stock a regiones estratégicas
└─> Prepara despachos adicionales

ROL VENTAS:
├─> Considera aumentar precios (demanda alta)
└─> Monitorea competencia

ROL ADMIN:
├─> Decide: ¿Subir precios o captar volumen?
└─> Ajusta estrategia según capital disponible

DÍAS 16-21 - EJECUCIÓN
├─> Ventas superiores al promedio
├─> Posible agotamiento de stock (si no compraron)
├─> Incremento de ingresos
└─> Competencia por market share

DÍA 22 - FIN DE DISRUPCIÓN
└─> Demanda vuelve a la normalidad
```

### 9.4 Fin de Simulación

```
DÍA 30 (o día configurado)
├─> Sistema procesa día final
├─> Cambia estado a "finalizado"
└─> Bloquea nuevas acciones

PROFESOR genera reporte final:
├─> Ranking de empresas por capital
├─> Análisis comparativo de métricas
├─> Gráficos de evolución
├─> Identificación de mejores prácticas
└─> Retroalimentación por equipo

ESTUDIANTES acceden a:
├─> Dashboard completo (solo lectura)
├─> Histórico de decisiones
├─> Comparativa con otras empresas
└─> Aprendizajes y áreas de mejora
```

---

## 10. Configuración y Administración

### 10.1 Configuración Inicial del Sistema

**Archivo:** `config.py`

```python
# Base de datos
SQLALCHEMY_DATABASE_URI = 'sqlite:///supply_chain.db'

# Seguridad
SECRET_KEY = 'clave-secreta-aleatoria'

# Email (para verificación)
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'correo@universidad.edu'
MAIL_PASSWORD = 'contraseña-aplicacion'

# Parámetros de simulación por defecto
CAPITAL_INICIAL_DEFAULT = 50000000
DURACION_DIAS_DEFAULT = 30
```

### 10.2 Inicialización de Base de Datos

**Comando:**
```bash
python init_db.py
```

**Crea:**
- Tablas de la base de datos
- Usuario super_admin inicial
- Productos por defecto (A, B, C)
- Configuración inicial

**Productos Iniciales:**

| Producto | Precio Base | Costo Compra | Demanda Promedio | Stock Inicial |
|----------|-------------|--------------|------------------|---------------|
| Producto A | $45,000 | $30,000 | 100 unid/día | 1000 |
| Producto B | $75,000 | $50,000 | 80 unid/día | 800 |
| Producto C | $120,000 | $80,000 | 50 unid/día | 500 |

### 10.3 Gestión de Usuarios

#### Crear Profesor
```
1. Super Admin → Panel de Administración
2. "Crear Nuevo Profesor"
3. Completar datos:
   - Nombre completo
   - Email (@universidad.edu)
   - Código de profesor
   - Universidad y sede
4. Sistema genera contraseña temporal
5. Envía email de bienvenida
```

#### Registro de Estudiante
```
1. Página pública de registro
2. Seleccionar tipo: "Estudiante"
3. Completar formulario:
   - Datos personales
   - Datos académicos (código, carrera)
   - Email institucional
4. Sistema envía código de verificación (6 dígitos)
5. Estudiante verifica email
6. Profesor asigna a empresa
7. Admin de empresa asigna rol específico
```

### 10.4 Mantenimiento

#### Backup de Base de Datos
```bash
# Copiar archivo de BD
copy instance\supply_chain.db backups\supply_chain_backup_YYYYMMDD.db
```

#### Resetear Simulación
```python
# En consola Python
from app import app, db
from models import *

with app.app_context():
    # Eliminar datos de simulación actual
    Venta.query.delete()
    Compra.query.delete()
    Inventario.query.delete()
    Metrica.query.delete()
    DisrupcionActiva.query.delete()
    
    # Resetear simulación
    sim = Simulacion.query.first()
    sim.dia_actual = 1
    sim.estado = 'pausado'
    
    # Resetear empresas
    for empresa in Empresa.query.all():
        empresa.capital_actual = empresa.capital_inicial
    
    db.session.commit()
```

### 10.5 Logs y Monitoreo

**El sistema registra:**
- Acciones de usuarios (login, decisiones)
- Procesamiento de días (timestamp, duración)
- Errores y excepciones
- Cambios en configuración

**Archivo:** `logs/application.log`

---

## 11. Casos de Uso

### 11.1 Caso 1: Gestión Conservadora

**Perfil:** Equipo que prioriza estabilidad

**Estrategia:**
- Precios competitivos (ligeramente bajo el promedio)
- Stock de seguridad alto (stock_maximo × 1.2)
- Compras frecuentes y pequeñas
- Distribución equitativa entre regiones

**Resultados Esperados:**
- Nivel de servicio: 95-98%
- ROI: 10-15% (conservador pero sólido)
- Capital final: +$5-8M sobre inicial
- Baja volatilidad

**Riesgos:**
- Altos costos de mantenimiento
- Penalizaciones por sobrestock
- Menor rentabilidad vs competencia agresiva

### 11.2 Caso 2: Gestión Agresiva

**Perfil:** Equipo que busca maximizar ganancias

**Estrategia:**
- Precios premium (10-20% sobre promedio)
- Stock ajustado (minimizar mantenimiento)
- Compras grandes aprovechando economías de escala
- Concentración en regiones rentables (Andina)

**Resultados Esperados:**
- Nivel de servicio: 85-90% (aceptan pérdidas)
- ROI: 25-40% (alto riesgo, alto retorno)
- Capital final: +$12-20M sobre inicial
- Alta volatilidad

**Riesgos:**
- Quiebres de stock frecuentes
- Pérdida de market share
- Vulnerabilidad a disrupciones

### 11.3 Caso 3: Respuesta a Crisis

**Escenario:** Disrupción "Paro Nacional - Crítica" (día 15)

**Situación:**
- Lead time: +15 días adicionales
- Compras en tránsito: retrasadas hasta día 30
- Stock actual: 60% de lo normal

**Respuesta Efectiva:**
1. **Inmediato (Día 15):**
   - Pausar nuevas compras
   - Racionar inventario existente
   - Priorizar productos de alto margen

2. **Corto Plazo (Días 16-18):**
   - Aumentar precios gradualmente (10-15%)
   - Redistribuir stock de regiones secundarias a primarias
   - Comunicar escasez al profesor (realismo)

3. **Medio Plazo (Días 19-25):**
   - Mantener precios altos (demanda supera oferta)
   - Evitar penalizaciones por sobrestock
   - Maximizar margen por unidad vendida

4. **Recuperación (Días 26-30):**
   - Esperar llegada de compras retrasadas
   - Volver a precios normales gradualmente
   - Reconstruir inventario

**Resultado:** Menor volumen de ventas, pero mayor margen → ROI protegido

### 11.4 Caso 4: Coordinación Multi-Rol

**Desafío:** Mantener coherencia entre decisiones de 4 roles

**Día 10 - Problema Identificado:**
- Planeación: "ROI cayendo, capital bajo"
- Ventas: "Nivel de servicio en 88%, perdiendo clientes"
- Compras: "Necesitamos ordenar más, pero sin capital"
- Logística: "Regiones Caribe y Pacífica sin stock"

**Reunión de Equipo:**
1. **Diagnóstico:**
   - Demasiado inventario en región Andina
   - Subutilización de regiones secundarias
   - Precios demasiado bajos (no genera suficiente margen)

2. **Plan de Acción:**
   - **Admin:** Aumenta precio Producto C en 15%
   - **Logística:** Despacha exceso de Andina a Caribe/Pacífica
   - **Compras:** Pausa órdenes nuevas por 3 días
   - **Ventas:** Monitorea impacto de cambio de precio

3. **Ejecución (Días 11-14):**
   - Redistribución de inventario
   - Ingresos aumentan por mejor precio
   - Costos de mantenimiento bajan

4. **Resultados (Día 15):**
   - Capital recuperado: +$2M
   - Nivel de servicio: 93%
   - ROI vuelve a positivo

---

## 12. Resolución de Problemas

### 12.1 Problemas Comunes

#### Problema: "No puedo crear órdenes de compra"

**Causas posibles:**
1. Capital insuficiente
2. Rol incorrecto (no eres Compras o Admin)
3. Simulación no está en estado "en_curso"

**Solución:**
- Verificar capital en dashboard
- Confirmar rol asignado
- Revisar estado de simulación con profesor

#### Problema: "Mi nivel de servicio es muy bajo"

**Causas:**
- Stock insuficiente
- Mala distribución regional
- Precios no competitivos

**Solución:**
1. Aumentar órdenes de compra
2. Revisar inventario regional (logística)
3. Ajustar precios vs competencia
4. Considerar lead time en planificación

#### Problema: "Estoy perdiendo dinero (ROI negativo)"

**Causas:**
- Costos de mantenimiento altos (sobrestock)
- Ventas perdidas (sub-stock)
- Precios de venta muy bajos

**Solución:**
1. Calcular stock óptimo (demanda × 7)
2. Ajustar precios para mejor margen
3. Reducir compras si hay sobrestock
4. Analizar composición de costos

#### Problema: "Las compras no llegan"

**Causas:**
- Lead time no cumplido aún
- Disrupción de retrasos activa
- Error en fecha estimada

**Solución:**
- Revisar "Compras en Tránsito" en dashboard
- Verificar disrupciones activas
- Considerar días adicionales por disrupciones
- Esperar hasta día indicado

### 12.2 Errores Técnicos

#### Error: "Capital negativo no permitido"

**Causa:** Intentar compra que excede capital disponible

**Solución:**
- Reducir cantidad de la orden
- Esperar ingresos de ventas
- Liquidar inventario excesivo

#### Error: "Stock insuficiente para despacho"

**Causa:** Intentar despachar más de lo disponible en central

**Solución:**
- Verificar inventario central actual
- Reducir cantidad del despacho
- Esperar recepción de compras

#### Error: "No se puede avanzar día"

**Causa:** Error en procesamiento automático

**Solución (Profesor):**
- Revisar logs de error
- Verificar integridad de datos
- Reintentar procesamiento
- Contactar soporte si persiste

### 12.3 FAQ

**P: ¿Puedo cambiar mi rol después de asignado?**  
R: Sí, el Admin de la empresa puede reasignar roles en cualquier momento.

**P: ¿Qué pasa si mi equipo no toma decisiones un día?**  
R: El sistema procesará el día con las configuraciones actuales (precios y stock existentes). No hay penalización directa, pero perderás oportunidades de optimización.

**P: ¿Puedo ver las decisiones de otras empresas?**  
R: No, cada empresa solo ve su información. El profesor ve todas las empresas.

**P: ¿El sistema considera inflación?**  
R: No, los precios y costos son nominales y estables (excepto disrupciones de aumento de costos).

**P: ¿Puedo cancelar una compra ya creada?**  
R: No, una vez creada la orden el capital se descuenta inmediatamente. Representa un compromiso real.

**P: ¿Qué pasa si mi capital llega a cero?**  
R: No puedes realizar nuevas compras, pero el sistema sigue funcionando. Debes generar ingresos por ventas para recuperarte.

**P: ¿Los días se avanzan automáticamente?**  
R: No, el profesor controla cuándo avanzar cada día. Esto permite sincronización con clases presenciales.

**P: ¿Puedo exportar mis datos?**  
R: Actualmente no hay exportación directa. El profesor puede generar reportes al final.

---

## 13. Anexos

### 13.1 Glosario de Términos

- **Capital Circulante**: Efectivo + Inventario valorizado
- **COGS (Cost of Goods Sold)**: Costo de productos vendidos
- **Elasticidad de Precio**: Sensibilidad de la demanda a cambios de precio
- **KPI**: Key Performance Indicator (indicador clave de desempeño)
- **Lead Time**: Tiempo entre orden y recepción de compra
- **Market Share**: Participación de mercado
- **ROI**: Return on Investment (retorno sobre inversión)
- **SKU**: Stock Keeping Unit (unidad de inventario)
- **Stockout**: Quiebre de stock (inventario = 0)
- **Sobrestock**: Exceso de inventario sobre nivel óptimo

### 13.2 Fórmulas Rápidas

```
Nivel de Servicio = (Vendido / Solicitado) × 100

ROI = ((Capital Final - Capital Inicial) / Capital Inicial) × 100

Margen Bruto = ((Ventas - Costos) / Ventas) × 100

Rotación = Ventas / Stock Promedio

Días Cobertura = Stock Actual / Demanda Promedio Diaria

Costo Mantenimiento Diario = Valor Inventario × 0.003

Penalización Sobrestock = Exceso × Costo Unitario × 0.005

Costo Oportunidad = Ventas Perdidas × Precio × 0.30

Market Share = (Ventas Empresa / Ventas Totales Mercado) × 100
```

### 13.3 Valores de Referencia

**Stock Óptimo:**
- Stock Mínimo: Demanda × 3 días
- Stock Objetivo: Demanda × 7 días
- Stock Máximo: Demanda × 10 días

**Rangos de Desempeño:**

| Métrica | Excelente | Bueno | Aceptable | Deficiente |
|---------|-----------|-------|-----------|------------|
| Nivel de Servicio | ≥95% | 90-95% | 85-90% | <85% |
| ROI Final | ≥30% | 20-30% | 10-20% | <10% |
| Margen Bruto | ≥35% | 25-35% | 15-25% | <15% |
| Rotación | 14-20 | 10-14 | 7-10 | <7 o >20 |

### 13.4 Atajos de Teclado (Navegación)

- **Alt + D**: Ir a Dashboard
- **Alt + V**: Módulo Ventas
- **Alt + C**: Módulo Compras
- **Alt + L**: Módulo Logística
- **Alt + P**: Módulo Planeación
- **Ctrl + S**: Guardar cambios (en formularios)
- **Esc**: Cerrar modal

---

## 14. Contacto y Soporte

**Desarrollador:** Equipo de Trabajo de Grado  
**Universidad:** Universidad del Rosario  
**Versión del Sistema:** 1.0  
**Última Actualización:** Enero 2026  

**Soporte Técnico:**  
- Email: soporte@universidad.edu  
- Horario: Lunes a Viernes, 8:00 AM - 6:00 PM  

**Documentación Adicional:**  
- Repositorio de código: (URL del repositorio)  
- Video tutoriales: (URL de videos)  
- Foro de discusión: (URL del foro)  

---

## 15. Notas de Versión

**v1.0 (Enero 2026)**
- ✅ Sistema económico completo con costos realistas
- ✅ Capital inicial ajustado a $50,000,000
- ✅ Sistema de sobrestock con stock_maximo dinámico
- ✅ Nivel de servicio acumulativo implementado
- ✅ Demanda mínima garantizada (60%) por empresa
- ✅ Tema visual rojo universitario aplicado
- ✅ 6 regiones de Colombia configuradas
- ✅ 5 tipos de disrupciones con 4 severidades
- ✅ 4 roles de estudiante + Admin + Profesor
- ✅ Procesamiento automático de días
- ✅ Dashboards interactivos con Chart.js

**Características Pendientes (Futuras Versiones):**
- [ ] Exportación de reportes a PDF/Excel
- [ ] Sistema de notificaciones push
- [ ] Modo multijugador en tiempo real
- [ ] Integración con API de datos reales de mercado
- [ ] Machine learning para pronósticos avanzados
- [ ] Modo tutorial interactivo para nuevos usuarios

---

**Fin del Manual**

*Este documento es propiedad de la Universidad del Valle y está protegido por derechos de autor. Se permite su uso exclusivamente con fines educativos.*
