# 📊 MÓDULO DE VENTAS - DOCUMENTACIÓN COMPLETA

## 🎯 Descripción General

El **Módulo de Ventas** permite al rol de estudiante encargado de ventas administrar precios, analizar la demanda por regiones de Colombia y observar resultados comerciales.

---

## ✨ Funcionalidades Implementadas

### 1️⃣ Ajuste de Precios
- **Visualización de productos** con:
  - Código del producto
  - Precio actual
  - Precio sugerido por el sistema
  - Costo unitario (límite mínimo)
  - Margen de ganancia calculado
  
- **Modificación de precios**:
  - Input numérico con validación (no puede ser menor al costo)
  - Aplicación inmediata del cambio
  - Registro en tabla `decisiones`
  - Efecto inmediato en la demanda del siguiente día (elasticidad del precio)

**Elasticidad**: Cada producto tiene un factor de elasticidad que determina cómo cambia la demanda cuando se modifica el precio:
```
demanda_ajustada = demanda_base * (1 - (variacion_precio * elasticidad))
```

### 2️⃣ Panel de Análisis Comercial

#### **Métricas Principales** (Dashboard)
- 💰 **Ingresos Hoy**: Total de ingresos del día actual
- 📦 **Unidades Vendidas**: Total de productos vendidos hoy
- 📈 **Nivel de Servicio**: Porcentaje de demanda satisfecha (cumplimiento)
- ⚠️ **Ventas Perdidas**: Unidades no vendidas por falta de inventario

#### **Gráficos Interactivos** (Chart.js)

1. **Ventas por Región** (Gráfico de Líneas)
   - Muestra ingresos de los últimos 14 días
   - 5 líneas (una por región)
   - Colores distintivos por región
   - Actualización en tiempo real vía API

2. **Ingresos por Producto** (Gráfico de Barras)
   - Últimos 7 días
   - Comparación visual de productos más rentables
   - Colores diferenciados

3. **Precio vs Demanda** (Gráfico de Doble Eje)
   - Selector de producto
   - Eje Y izquierdo: Precio ($)
   - Eje Y derecho: Demanda (unidades)
   - Permite ver correlación precio-demanda

### 3️⃣ Análisis por Regiones de Colombia

**5 Regiones Geográficas**:
- 🌊 **Caribe** (factor 0.9)
- 🚢 **Pacífica** (factor 0.85)
- 🐴 **Orinoquía** (factor 0.7)
- 🌳 **Amazonía** (factor 0.6)
- ⛰️ **Andina** (factor 1.2) - Mayor densidad poblacional

#### **Datos por Región**:
- Ingresos totales (últimos 14 días)
- Unidades vendidas
- Ventas perdidas
- Promedio diario de ingresos
- **Nivel de cumplimiento** (barra de progreso)

#### **Vista de Análisis Regional**:
- Cards detalladas por región con iconos distintivos
- Gráfico comparativo de barras (ingresos, unidades, pérdidas)
- **Insights automáticos**:
  - Mejor región (mayor ingreso)
  - Región con oportunidad de mejora
  - Alertas de coordinación con Logística

### 4️⃣ Historial de Ventas
- Tabla con últimas 20 transacciones
- Filtros por:
  - Día de simulación
  - Producto
  - Región
  - Cantidad solicitada vs vendida
  - Precio unitario
  - Ingreso total

---

## 🔗 Relación con Otros Módulos

### **Logística** 📦
- **Dependencia**: Ventas necesita inventario disponible para satisfacer demanda
- **Coordinación**: Cuando hay ventas perdidas, se genera alerta para que Logística ajuste:
  - Punto de reorden
  - Stock de seguridad
  - Distribución regional
  
**Flujo de coordinación**:
```
Ventas detecta demanda insatisfecha → 
Alerta visible en dashboard → 
Logística aumenta inventario en región → 
Ventas captura más demanda
```

### **Compras** 🛒
- **Indirecta**: Los precios fijados por Ventas determinan la rentabilidad
- Si Ventas baja precios → menor margen → Compras debe negociar mejor con proveedores

### **Planeación** 📊
- **Datos compartidos**: El historial de ventas por región sirve para pronósticos de demanda
- Planeación puede usar tendencias de ventas para planificar producción/abastecimiento

---

## 🗄️ Estructura de Datos

### **Modelo `Venta` (Actualizado)**
```python
class Venta(db.Model):
    id: int
    empresa_id: int
    producto_id: int
    dia_simulacion: int
    region: str  # NUEVO: Caribe, Pacifica, Orinoquia, Amazonia, Andina
    canal: str  # NUEVO: retail, mayorista, distribuidor
    cantidad_solicitada: float
    cantidad_vendida: float
    cantidad_perdida: float
    precio_unitario: float
    ingreso_total: float
    costo_unitario: float  # NUEVO
    margen: float  # NUEVO
    created_at: datetime
```

### **Modelo `Producto` (Actualizado)**
```python
class Producto(db.Model):
    id: int
    codigo: str
    nombre: str
    categoria: str
    precio_base: float
    precio_actual: float  # NUEVO: Modificable por Ventas
    precio_sugerido: float  # NUEVO: Recomendación del sistema
    costo_unitario: float
    demanda_promedio: float
    desviacion_demanda: float
    elasticidad_precio: float  # NUEVO: Factor de sensibilidad (1.2-1.8)
    tiempo_entrega: int
    activo: bool
```

---

## 🛣️ Rutas Implementadas

### **Vistas**
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/estudiante/ventas` | GET | Dashboard principal de ventas |
| `/estudiante/ventas/analisis-regional` | GET | Vista detallada por regiones |

### **Acciones**
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/estudiante/ventas/ajustar-precio` | POST | Modificar precio de un producto |

### **APIs (JSON)**
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/estudiante/api/ventas/historico-region` | GET | Datos históricos por región (Chart.js) |
| `/estudiante/api/ventas/precio-demanda/<id>` | GET | Relación precio-demanda de un producto |
| `/estudiante/api/ventas/por-producto` | GET | Ingresos totales por producto |

**Parámetros de API**:
- `dias`: Número de días históricos (default: 7 o 14)
- Retorno: JSON con formato compatible con Chart.js

---

## 🎨 Interfaz de Usuario

### **Colores por Región**
```css
Caribe:    #3498db (Azul)
Pacífica:  #2ecc71 (Verde)
Orinoquía: #f39c12 (Naranja)
Amazonía:  #27ae60 (Verde oscuro)
Andina:    #9b59b6 (Púrpura)
```

### **Sidebar**
- Gradiente: `#667eea → #764ba2`
- Iconos FontAwesome
- Links:
  - Dashboard
  - Análisis Regional
  - Ajuste de Precios (anchor)
  - Historial (anchor)

### **Cards de Métricas**
- Fondo blanco con sombra
- Hover: elevación de card
- Iconos grandes semi-transparentes
- Valores numéricos destacados

---

## 🔧 Configuración de Inicialización

### **init_db.py - Datos de Ejemplo**
```python
# Productos con elasticidad
elasticidad_precio: 1.2 - 1.8

# Ventas históricas (7 días)
- 2-4 regiones por día
- Factor regional aplicado a demanda
- 85-100% de cumplimiento simulado
- 3 canales: retail, mayorista, distribuidor
- Precios con variación ±5%
```

### **procesar_dia() - Generación Automática**
Cada vez que el profesor avanza un día:
1. Se generan ventas en 2-4 regiones aleatorias
2. Demanda calculada con:
   - Factor regional (0.6 a 1.2)
   - Elasticidad del precio
   - Desviación estándar del producto
3. Se compara con inventario disponible
4. Se registran ventas realizadas y perdidas
5. Se actualiza inventario
6. Se calculan métricas del día

---

## 📋 Casos de Uso

### **Caso 1: Aumentar Precio**
1. Estudiante ve que producto tiene margen bajo (15%)
2. Aumenta precio de $50 a $55 (+10%)
3. Sistema registra decisión
4. Al avanzar día: demanda baja por elasticidad
5. Pero ingreso total puede subir si elasticidad < 1

### **Caso 2: Detectar Región con Problema**
1. Dashboard muestra ventas perdidas en Caribe: 120 unidades
2. Estudiante abre Análisis Regional
3. Ve que Caribe tiene nivel cumplimiento 75%
4. Alerta sugiere coordinar con Logística
5. Comunica a compañero de Logística para aumentar stock

### **Caso 3: Analizar Tendencia Precio-Demanda**
1. Selecciona "Laptop Empresarial" en gráfico
2. Ve que días 3-5 tenía precio $1200 y demanda 50
3. Día 6 bajó precio a $1100 y demanda subió a 68
4. Confirma elasticidad alta (1.8)
5. Decide mantener precio bajo para volumen

---

## 🚀 Ejecución y Pruebas

### **Reinicializar Base de Datos**
```bash
cd supply_chain_app
python init_db.py
```

### **Iniciar Servidor**
```bash
python app.py
```

### **Login como Ventas**
```
Usuario: estudiante_1_1
Contraseña: estudiante123
```

### **Verificar Funcionalidades**
1. ✅ Ver métricas del día actual
2. ✅ Visualizar gráficos de regiones
3. ✅ Cambiar precio de un producto
4. ✅ Verificar que se guarda en Decisiones
5. ✅ Ver análisis regional
6. ✅ Identificar mejor y peor región
7. ✅ Revisar historial de ventas

---

## 🐛 Solución de Problemas

### **Los gráficos no cargan**
- Verificar que Chart.js se carga: `https://cdn.jsdelivr.net/npm/chart.js@4.4.0`
- Abrir consola del navegador (F12) y revisar errores
- Verificar que las APIs retornan JSON válido

### **No hay datos de ventas**
- Ejecutar `python init_db.py` para generar datos históricos
- Verificar que la simulación esté en día > 1
- Avanzar días con el profesor

### **Error "No autorizado"**
- Verificar que el usuario tenga `rol='ventas'`
- Limpiar cookies y volver a hacer login

### **Precios no se actualizan**
- Verificar que precio_nuevo >= costo_unitario
- Revisar tabla `decisiones` para confirmar registro
- Verificar campo `precio_actual` en tabla `productos`

---

## 📈 Próximas Mejoras (Futuras)

- [ ] Predicción de demanda con Machine Learning
- [ ] Simulación de competencia (precios de mercado)
- [ ] Descuentos por volumen automáticos
- [ ] Campaña de marketing por región
- [ ] Estacionalidad en la demanda
- [ ] Exportar reportes a PDF/Excel
- [ ] Notificaciones en tiempo real
- [ ] Comparación con otras empresas (ranking)

---

## 👥 Coordinación entre Roles

```
┌─────────────┐     Ajusta Precios      ┌──────────────┐
│   VENTAS    │────────────────────────▶│  Demanda     │
│             │                         │  Elasticidad │
└─────────────┘                         └──────────────┘
       │                                        │
       │ Reporta                                │
       │ Ventas                                 │ Requiere
       │ Perdidas                               │ Inventario
       │                                        │
       ▼                                        ▼
┌─────────────┐     Coordina Stock     ┌──────────────┐
│  LOGÍSTICA  │◀───────────────────────│   COMPRAS    │
│ (Distribuc.)│                        │  (Órdenes)   │
└─────────────┘                        └──────────────┘
       │                                        ▲
       │                                        │
       │ Informa                                │ Planea
       │ Niveles                                │ Reorden
       │                                        │
       ▼                                        │
┌─────────────┐     Pronostica         │
│ PLANEACIÓN  │────────────────────────┘
│  (Análisis) │
└─────────────┘
```

---

## 📝 Resumen de Archivos Modificados/Creados

### **Modelos**
- ✅ `models.py` - Agregados campos: `region`, `canal`, `margen`, `precio_actual`, `precio_sugerido`, `elasticidad_precio`

### **Backend**
- ✅ `routes/estudiante.py` - Nuevas rutas y APIs para Ventas
- ✅ `routes/profesor.py` - Actualizado `procesar_dia()` con regiones

### **Frontend**
- ✅ `templates/estudiante/ventas/dashboard.html` - Dashboard principal
- ✅ `templates/estudiante/ventas/analisis_regional.html` - Vista regional

### **Datos**
- ✅ `init_db.py` - Generación de ventas históricas con regiones

---

**Autor**: GitHub Copilot  
**Fecha**: Noviembre 2025  
**Versión**: 1.0  
**Estado**: ✅ COMPLETADO Y FUNCIONAL
