# 📊 Manual de Datos Iniciales del Simulador de Cadena de Abastecimiento

**Versión:** 1.0  
**Última actualización:** Abril 2026  
**Diseñado para:** Administradores y Docentes que configuren la simulación

---

## 📌 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [¿Todas las Empresas Empiezan Igual?](#todas-las-empresas-empiezan-igual)
3. [Datos Iniciales Configurables por el Admin](#datos-iniciales-configurables-por-el-admin)
4. [Datos Iniciales Fijos del Sistema](#datos-iniciales-fijos-del-sistema)
5. [Catálogo de Productos](#catálogo-de-productos)
6. [Estructura de Inventarios Iniciales](#estructura-de-inventarios-iniciales)
7. [Parámetros de Demanda y Oferta](#parámetros-de-demanda-y-oferta)
8. [Regiones de Distribución](#regiones-de-distribución)
9. [Costos Operativos Iniciales](#costos-operativos-iniciales)
10. [Cheklist de Verificación Antes de Iniciar](#checklist-de-verificación-antes-de-iniciar)

---

## 📋 Descripción General

El simulador de cadena de abastecimiento es un juego de negocio educativo donde los estudiantes toman decisiones sobre:

- **Gestión de ventas:** Precios y estrategias comerciales
- **Planeación:** Pronósticos y requerimientos de compra
- **Compras:** Órdenes a proveedores
- **Logística:** Inventario y distribución regional

Todos comienzan con **datos iniciales idénticos** (excepto el capital individual, si se configura así), creando un entorno competitivo justo.

---

## ✅ ¿Todas las Empresas Empiezan Igual?

### 🎯 RESPUESTA CORTA: **SÍ, CASI TOTALMENTE**

**Lo que SÍ es igual para TODAS las empresas:**
- ✅ Inventario inicial (mismo número de unidades de cada producto)
- ✅ Costo unitario de los productos
- ✅ Precio base de los productos
- ✅ Demanda del mercado (misma distribución probabilística)
- ✅ Parámetros de punto de reorden y stock de seguridad
- ✅ Tiempos de entrega
- ✅ Costos operativos
- ✅ Estructura regional de demanda (5 regiones)
- ✅ Duración de la simulación

**Lo que PUEDE variar:**
- ⚠️ **Capital inicial:** El admin puede asignar capital diferente a cada empresa si lo desea
  - *Valor por defecto:* $50,000,000 por empresa
  - *Mínimo permitido:* $1,000,000
  - *Configuración:* Puede ser igual para todos o diferenciado

---

## 🎛️ Datos Iniciales Configurables por el Admin

### 1. **Capital Inicial por Empresa**

| Parámetro | Valor por Defecto | Rango | Notas |
|-----------|-------------------|-------|-------|
| Capital inicial | $50,000,000 | $1,000,000 - ∞ | Configurable por cada empresa |
| Aplicado a | TODAS las empresas | - | Se asigna al momento de crear/reiniciar simulación |

**Dónde se configura:**
- Ruta: `Profesor → Dashboard → Crear Nueva Simulación`
- Campo: "Capital Inicial por Empresa"
- Acción: El admin ingresa el valor **una vez** y se aplica a TODAS

---

### 2. **Inventario Inicial de Productos**

| Parámetro | Valor por Defecto | Rango | Notas |
|-----------|-------------------|-------|-------|
| Productos 750ml | 120 unidades | 0 - ∞ | Vinos en botellas de 750ml |
| Productos 1L | 80 unidades | 0 - ∞ | Vinos en botellas de 1 litro |
| Aplicado a | TODAS las empresas | - | Igual para todos los equipos |

**Dónde se configura:**
- Ruta: `Profesor → Dashboard → Crear Nueva Simulación`
- Campos: "Inventario inicial — Productos 750ml" y "Productos 1L"
- Acción: Ingresa valores **una sola vez**, se replica en TODAS las empresas

**¿Por qué dos valores?**
- El sistema maneja **dos tipos de productos:** vinos de 750ml y vinos de 1 litro
- Ambos tipos empiezan con su propio inventario inicial
- Esto crea diversidad de portafolio desde el inicio

---

### 3. **Nombre de la Simulación (Opcional)**

| Parámetro | Valor por Defecto | Notas |
|-----------|-------------------|-------|
| Nombre | "Simulación N" | Autogenerado si se deja vacío |
| Ejemplo | "Simulación 1", "Prueba Q1 2026" | Solo con fines administrativos |

---

## 🔒 Datos Iniciales Fijos del Sistema

Estos parámetros **NO se pueden cambiar** sin modificar el código:

### **Duración de la Simulación**

| Parámetro | Valor |
|-----------|-------|
| Duración estándar | 30 semanas (≈ 210 días) |
| Día inicial | 1 |
| Semana inicial | 1 |
| Estado inicial | "pausado" (no avanza hasta que el admin lo inicie) |

---

### **Estructura de Empresas**

| Parámetro | Valor | Detalle |
|-----------|-------|--------|
| Número de empresas | Configurable | Profesor crea las que necesite |
| Asignación de roles | 4 roles mínimo por empresa | Ventas, Planeación, Compras, Logística |
| Estudiantes por rol | 1 o más | Flexible según grupo |
| Visibilidad de datos | Solo tu empresa | Cada equipo ve solo sus propios datos |

---

## 📦 Catálogo de Productos

El sistema incluye **2 tipos de productos** (vinos):

### **Producto 1: Vino 750ml**

| Atributo | Valor Inicial | Descripción |
|----------|---------------|-------------|
| Código | VIN-750 | Identificador único |
| Nombre | "Vino [nombre específico] 750ml" | Nombre comercial |
| Precio Base | $45,000 - $55,000 | Precio de referencia (aprox.) |
| Precio Actual | Igual al base | Puede ser modificado por Ventas |
| Costo Unitario | $15,000 - $20,000 | Costo de adquisición (aprox.) |
| Categoría | Vinos | Por tipo de producto |
| Stock Inicial | 120 unidades | Configurable (véase arriba) |
| Tiempo de Entrega | 1 día | Lead time de proveedores |

### **Producto 2: Vino 1L**

| Atributo | Valor Inicial | Descripción |
|----------|---------------|-------------|
| Código | VIN-1L | Identificador único |
| Nombre | "Vino [nombre específico] 1L" | Nombre comercial |
| Precio Base | $58,000 - $70,000 | Precio de referencia (aprox.) |
| Precio Actual | Igual al base | Puede ser modificado por Ventas |
| Costo Unitario | $18,000 - $25,000 | Costo de adquisición (aprox.) |
| Categoría | Vinos | Por tipo de producto |
| Stock Inicial | 80 unidades | Configurable (véase arriba) |
| Tiempo de Entrega | 1 día | Lead time de proveedores |

**Nota:** Los precios y costos exactos se obtienen de la base de datos. Estos son rangos aproximados.

---

## 📦 Estructura de Inventarios Iniciales

### **Para CADA Empresa:**

Cuando se crea/reinicia la simulación, se inicializa automáticamente:

```
Inventario Empresa X
├── Producto 750ml
│   ├── Cantidad Actual: 120 und (configurable)
│   ├── Cantidad Reservada: 0 und (sin pedidos pendientes)
│   ├── Punto de Reorden: Calculado automáticamente
│   ├── Stock Seguridad: Calculado automáticamente
│   └── Costo Promedio: = Costo Unitario del producto
│
└── Producto 1L
    ├── Cantidad Actual: 80 und (configurable)
    ├── Cantidad Reservada: 0 und
    ├── Punto de Reorden: Calculado automáticamente
    ├── Stock Seguridad: Calculado automáticamente
    └── Costo Promedio: = Costo Unitario del producto
```

### **Cálculo Automático de Parámetros de Inventario**

El sistema calcula automáticamente para optimizar presión competitiva:

| Parámetro | Fórmula | Lógica |
|-----------|---------|--------|
| **Demanda Promedio Semanal** | `inv_inicial × 7 / (5 días × 5 regiones)` | Se ajusta para consumir stock en 5 días |
| **Consumo Diario (empresa)** | `(demanda_promedio / 7) × 5 regiones` | Compra debe reaccionar rápidamente |
| **Punto de Reorden** | `consumo_diario × 3 días` | Reordenar cuando quedan 3 días |
| **Stock de Seguridad** | `consumo_diario × 1 día` | Colchón contra volatilidad |
| **Stock Máximo** | `inventario_inicial × 3` | Techo de almacenamiento (evita sobrestock) |

**Ejemplo con inv_750ml = 120:**
- Demanda semanal inicial ≈ 33-34 unidades/semana por región
- Consumo diario ≈ 24 unidades/día
- Punto reorden ≈ 72 unidades
- Stock seguridad ≈ 24 unidades

---

## 📊 Parámetros de Demanda y Oferta

### **Demanda del Mercado**

| Parámetro | Valor | Características |
|-----------|-------|-----------------|
| Distribución | Probabilística normal (Gaussiana) | `demanda = μ + σ × rand()` |
| Volatilidad de demanda | ±20% | Desviación estándar del 20% |
| Competencia | 100% - Entre todas las empresas | No hay demanda garantizada |
| Elasticidad | Factor 1.5 | Sensibilidad al precio |

### **Puntos Críticos**

- **Si no hay stock:** Venta perdida (cliente compra en otro lado)
- **Si hay sobrestock:** Costo de almacenamiento extra ($0.50/unidad/día)
- **Si hay quiebre:** Penalización de $10.00/unidad no vendida

---

## 🗺️ Regiones de Distribución

El mercado está dividido en **5 regiones Colombia**, cada una con demanda independiente:

| Región | Características |
|--------|-----------------|
| **Andina** | Centro geográfico, demanda equilibrada |
| **Caribe** | Zona costera norte |
| **Pacífica** | Zona costera oeste |
| **Orinoquia** | Zona oriental |
| **Amazonia** | Zona sur-oriental |

**Puntos importantes:**
- Cada región demanda productos **simultáneamente**
- La demanda de cada región es **independiente** y **probabilística**
- Despachos a regiones toman **varios días** en llegar
- El nivel de servicio se calcula sobre la **capacidad de satisfacer** cada región

---

## 💰 Costos Operativos Iniciales

### **Costos Fijos del Sistema**

| Concepto | Costo | Cálculo | Notas |
|----------|-------|---------|-------|
| Almacenamiento | $0.50/unidad/día | Por unidad en inventario | Si excede stock máximo: 2x |
| Venta Perdida (Faltante) | $10.00/unidad | Por unidad no entregada | Penalización por quiebre de stock |
| Transporte | % variable | Según distancia región | Incluido en costo de despacho |
| Precio de Compra | Costo unitario del producto | Base = precio costo | Puede variar si hay disrupciones |

### **Ejemplo de Flujo Financiero Día 1:**

Para una empresa con:
- Capital inicial: $50,000,000
- Inventario: 120 und × $18,000 (costo 750ml) = $2,160,000

```
Capital Inicial:           $50,000,000
- Valor de Inventario:     $2,160,000
= Capital Libre para Compras: $47,840,000

Durante la simulación:
+ Ingresos (ventas):       Depende de decisiones
- Costo de Compras:        Depende de órdenes
- Costo de Almacenamiento: $0.50 × unidades × días
- Costo de Faltantes:      $10.00 × unidades no vendidas
= Capital Disponible (Día N)
```

---

## 📈 Métricas Iniciales

Desde el **Día 1**, el sistema calcula automáticamente:

### **Métricas por Empresa**

| Métrica | Inicial | Tipo |
|---------|---------|------|
| **Ingresos Totales** | $0 | Acumulativo |
| **Costos Totales** | Costo almacenamiento | Acumulativo |
| **Utilidad Neta** | Negativa (por almacenamiento) | Acumulativo |
| **Nivel de Servicio** | % de demanda satisfecha | Porcentaje |
| **Rotación de Inventario** | Veces que se vende el stock | Ratio |
| **Market Share** | % de ingresos totales del mercado | Porcentaje |
| **Días de Inventario** | Días que durará el stock | Días |

**Nivel de Servicio Inicial (Día 1):**
- Se calcula como: `(unidades_vendidas / unidades_demandadas) × 100%`
- Inicialmente es variable (depende de la demanda aleatoria)
- Puede ser 100% si la demanda es baja, o menor si es alta

---

## 📝 Checklist de Verificación Antes de Iniciar

Antes de que los estudiantes vean los datos iniciales, verifica:

### **Paso 1: Configuración de Simulación**
- [ ] ¿Se creó la simulación con los parámetros correctos?
- [ ] Capital inicial por empresa: **$____________**
- [ ] Inventario 750ml: **______ unidades**
- [ ] Inventario 1L: **______ unidades**
- [ ] Nombre de simulación: **_____________________________**

### **Paso 2: Verificar Empresas Creadas**
- [ ] ¿Cuántas empresas se crearon? **______ empresas**
- [ ] ¿Cada empresa tiene exactamente 4 roles? (Ventas, Planeación, Compras, Logística)
- [ ] ¿Cada estudiante está asignado a su rol?

### **Paso 3: Consultar Datos en la BD**
Para verificar que los datos son correctos, ejecuta en el shell de Python:

```python
from app import app
from models import Empresa, Simulacion, Inventario, Producto
from extensions import db

with app.app_context():
    sim = Simulacion.query.filter_by(activa=True).first()
    print(f"Simulación: {sim.nombre}")
    print(f"Capital inicial empresas: ${sim.capital_inicial_empresas:,.0f}")
    print(f"Duración: {sim.duracion_semanas} semanas")
    
    for emp in sim.empresas:
        print(f"\n✓ Empresa: {emp.nombre}")
        print(f"  Capital: ${emp.capital_inicial:,.0f}")
        for inv in emp.inventarios:
            print(f"  - {inv.producto.nombre}: {inv.cantidad_actual:.0f} und")
```

### **Paso 4: Puntos Clave**
- [ ] ¿El capital es suficiente para hacer compras? (Mínimo recomendado: $10M)
- [ ] ¿El inventario inicial es realista? (Recomendado: 80-200 unidades)
- [ ] ¿Las empresas están en estado "pausado" antes de avanzar?
- [ ] ¿La duración es 30 semanas (90 días)?

---

## 🚀 Vista de Estudiantes: ¿Qué Ven?

Cuando los estudiantes acceden al sistema, ven:

### **En la Página de Inicio**
```
Tu Empresa: [Nombre Empresa]
├── Capital Actual: $50,000,000
├── Rol: [Tu Rol Asignado]
├── Día Simulación: 1
└── Estado: Simulación Pausada / En Curso
```

### **En el Dashboard de Logística**
```
Inventario Actual:
├── Vino 750ml: 120 unidades
│   ├── Punto Reorden: 72 unidades
│   ├── Stock Seguridad: 24 unidades
│   └── Stock Máximo: 360 unidades
│
└── Vino 1L: 80 unidades
    ├── Punto Reorden: 48 unidades
    ├── Stock Seguridad: 16 unidades
    └── Stock Máximo: 240 unidades
```

### **En el Dashboard de Ventas**
```
Precios Disponibles:
├── Vino 750ml: $45,000 (Precio Base)
├── Vino 1L: $60,000 (Precio Base)
└── Rango permitido: [Costo Unitario, ∞)
```

### **En el Dashboard de Compras**
```
Costo de Proveedores:
├── Vino 750ml: $18,000/unidad
├── Vino 1L: $21,000/unidad
└── Tiempo Entrega: 1 día
```

---

## ❓ Preguntas Frecuentes

### **P: ¿Puedo cambiar el capital de una empresa después de empezar?**
**R:** Sí, en la sección "Gestionar Empresas" del dashboard del profesor. Pero se recomienda hacerlo antes de que comience la simulación.

### **P: ¿Qué pasa si creo una simulación con capital muy bajo?**
**R:** Las empresas no podrán hacer pedidos significativos. Para pruebas educativas, recomendamos mínimo $20M.

### **P: ¿Puedo cambiar el inventario inicial después de crear la simulación?**
**R:** Solo mediante reinicio de simulación (borraría todo progreso). Es mejor usar "Calibrar Demanda" para ajustes.

### **P: ¿Qué pasa si dos empresas tienen exactamente los mismos datos iniciales?**
**R:** El juego es completamente justo. Las diferencias en resultados provienen 100% de las decisiones de cada equipo.

### **P: ¿Se puede extender la simulación más de 30 semanas?**
**R:** Sí, modificando el campo `duracion_semanas` en la tabla `simulacion` directamente en la BD.

### **P: ¿Cómo explico a los estudiantes por qué tienen demanda aleatoria?**
**R:** "En la realidad, la demanda no es perfecta ni predecible. El mercado varía basado en factores externos que ustedes no controlamos. La desviación de ±20% representa esa incertidumbre real."

---

## 📚 Documentos Relacionados

- [`REPORTE_FUNCIONAMIENTO_SIMULADOR.md`](./REPORTE_FUNCIONAMIENTO_SIMULADOR.md) - Cómo funciona el motor simulador
- [`DOCUMENTACION_COLORES.py`](./DOCUMENTACION_COLORES.py) - Parámetros de colores en disrupciones
- [`DOCUMENTACION_COSTOS_OPERATIVOS.py`](./DOCUMENTACION_COSTOS_OPERATIVOS.py) - Detalle de costos
- [`utils/catalogo_disrupciones.py`](./utils/catalogo_disrupciones.py) - Escenarios que pueden ocurrir

---

## 📞 Soporte y Contacto

Para preguntas sobre:
- **Configuración:** Contacta al administrador del sistema
- **Datos iniciales:** Revisa esta guía o `REPORTE_FUNCIONAMIENTO_SIMULADOR.md`
- **Cambios de código:** Requiere acceso al repositorio y modificación del código

---

**Última actualización:** 11 de abril de 2026  
**Versión:** 1.0  
**Autor:** Sistema de Documentación Automática
