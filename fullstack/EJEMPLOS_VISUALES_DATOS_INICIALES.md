# 🎬 Ejemplos Visuales: Datos Iniciales en Acción

**Propósito:** Mostrar exactamente qué ven los estudiantes y cómo están configurados los datos iniciales  
**Dirigido a:** Docentes que quieren explicar el sistema a su grupo

---

## 📱 Ejemplo 1: Tres Empresas, Mismos Datos Iniciales

### **Escenario: Profesor crea simulación con estos parámetros:**

```
┌──────────────────────────────────────────┐
│   CREAR NUEVA SIMULACIÓN                 │
├──────────────────────────────────────────┤
│ Nombre: Prueba Inicial Q2 2026           │
│ Capital: $50,000,000                     │
│ Inv. 750ml: 120 unidades                 │
│ Inv. 1L: 80 unidades                     │
│                                          │
│ [CREAR SIMULACIÓN]                       │
└──────────────────────────────────────────┘
```

### **Resultado: Base de Datos**

```
SIMULACION
├─ ID: 1
├─ Nombre: "Prueba Inicial Q2 2026"
├─ Capital Inicial Empresas: $50,000,000
├─ Duración: 30 semanas
├─ Estado: pausado
└─ Activa: true

EMPRESA (3 empresas creadas por el profesor)
├─ Empresa 1: "Distribuidora Alpha"
│  ├─ Capital Inicial: $50,000,000 ✓
│  ├─ Capital Actual: $50,000,000 ✓
│  └─ Simulación: "Prueba Inicial Q2 2026"
│
├─ Empresa 2: "Distribuidora Beta"
│  ├─ Capital Inicial: $50,000,000 ✓ (IGUAL)
│  ├─ Capital Actual: $50,000,000 ✓ (IGUAL)
│  └─ Simulación: "Prueba Inicial Q2 2026"
│
└─ Empresa 3: "Distribuidora Gamma"
   ├─ Capital Inicial: $50,000,000 ✓ (IGUAL)
   ├─ Capital Actual: $50,000,000 ✓ (IGUAL)
   └─ Simulación: "Prueba Inicial Q2 2026"
```

### **Inventarios Iniciales**

```
EMPRESA 1 - Distribuidora Alpha
├─ INVENTARIO Vino 750ml
│  ├─ Cantidad: 120 und ✓
│  ├─ Punto Reorden: 72 und ✓
│  ├─ Stock Seguridad: 24 und ✓
│  ├─ Stock Máximo: 360 und ✓
│  └─ Valor: 120 × $18,000 = $2,160,000
│
└─ INVENTARIO Vino 1L
   ├─ Cantidad: 80 und ✓
   ├─ Punto Reorden: 48 und ✓
   ├─ Stock Seguridad: 16 und ✓
   ├─ Stock Máximo: 240 und ✓
   └─ Valor: 80 × $21,000 = $1,680,000

EMPRESA 2 - Distribuidora Beta
├─ INVENTARIO Vino 750ml
│  ├─ Cantidad: 120 und ✓ (IDÉNTICO)
│  ├─ Punto Reorden: 72 und ✓ (IDÉNTICO)
│  ├─ Stock Seguridad: 24 und ✓ (IDÉNTICO)
│  ├─ Stock Máximo: 360 und ✓ (IDÉNTICO)
│  └─ Valor: 120 × $18,000 = $2,160,000
│
└─ INVENTARIO Vino 1L
   ├─ Cantidad: 80 und ✓ (IDÉNTICO)
   ├─ Punto Reorden: 48 und ✓ (IDÉNTICO)
   ├─ Stock Seguridad: 16 und ✓ (IDÉNTICO)
   ├─ Stock Máximo: 240 und ✓ (IDÉNTICO)
   └─ Valor: 80 × $21,000 = $1,680,000

EMPRESA 3 - Distribuidora Gamma
├─ INVENTARIO Vino 750ml
│  ├─ Cantidad: 120 und ✓ (IDÉNTICO)
│  ├─ Punto Reorden: 72 und ✓ (IDÉNTICO)
│  └─ ... [IGUAL A EMPRESA 1 Y 2]
│
└─ INVENTARIO Vino 1L [IGUAL A OTROS]
```

---

## 💻 Ejemplo 2: Lo que Cada Estudiante Ve (Día 1)

### **Estudiante 1 - ROL LOGÍSTICA (Distribuidora Alpha)**

**Pantalla: Dashboard Logística**

```
╔═══════════════════════════════════════════════════════════╗
║         GESTIÓN DE INVENTARIO - DÍA 1, SEMANA 1           ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  CAPITAL DISPONIBLE                                       ║
║  ┌─────────────────────────────────────────────────────┐ ║
║  │ Capital Inicial:        $50,000,000                 │ ║
║  │ Compras Pendientes:     $0                          │ ║
║  │ Valor Inventario:       $3,840,000                  │ ║
║  │ Capital Libre:          $46,160,000 (Disponible)   │ ║
║  └─────────────────────────────────────────────────────┘ ║
║                                                           ║
║  INVENTARIO ACTUAL                                        ║
║  ┌─────────────────────────────────────────────────────┐ ║
║  │ Vino 750ml TINTO RESERVA                            │ ║
║  │ ├─ Stock Actual:        120 unidades                │ ║
║  │ ├─ Punto Reorden:       72 unidades ⚠️ Debes        │ ║
║  │ ├─ Stock Mínimo:        24 unidades    comprar      │ ║
║  │ ├─ Stock Máximo:        360 unidades   cuando se    │ ║
║  │ ├─ Costo Unitario:      $18,000        baje a 72    │ ║
║  │ └─ Demanda semanal est: 34 un/región               │ ║
║  │                                                     │ ║
║  │ Vino 1L BLANCO JOVEN                                │ ║
║  │ ├─ Stock Actual:        80 unidades                │ ║
║  │ ├─ Punto Reorden:       48 unidades                │ ║
║  │ ├─ Stock Mínimo:        16 unidades                │ ║
║  │ ├─ Stock Máximo:        240 unidades               │ ║
║  │ ├─ Costo Unitario:      $21,000                    │ ║
║  │ └─ Demanda semanal est: 23 un/región               │ ║
║  └─────────────────────────────────────────────────────┘ ║
║                                                           ║
║  RECOMENDACION: El stock durará ~5 días. Comienza a     ║
║  planificar tu primer pedido YA.                         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

### **Estudiante 2 - ROL VENTAS (Distribuidora Beta)**

**Pantalla: Dashboard Ventas - Matriz de Precios**

```
╔═══════════════════════════════════════════════════════════╗
║         GESTIÓN DE PRECIOS - DÍA 1, SEMANA 1              ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  PRODUCTOS DISPONIBLES PARA VENTA                         ║
║  ┌─────────────────────────────────────────────────────┐ ║
║  │ Vino 750ml TINTO RESERVA                            │ ║
║  │ ├─ Precio Base (tu referencia):  $45,000            │ ║
║  │ ├─ Precio Actual (es el mismo):  $45,000 ✓          │ ║
║  │ ├─ Costo (piso de precio):       $18,000            │ ║
║  │ ├─ Margen potencial:             $27,000/botella    │ ║
║  │ └─ Stock disponible:             120 botellas       │ ║
║  │                                                     │ ║
║  │    [CAMBIAR PRECIO] ← Puedes mover a $40-60K       │ ║
║  │                                                     │ ║
║  │ Vino 1L BLANCO JOVEN                                │ ║
║  │ ├─ Precio Base:                  $60,000            │ ║
║  │ ├─ Precio Actual:                $60,000 ✓          │ ║
║  │ ├─ Costo:                        $21,000            │ ║
║  │ ├─ Margen potencial:             $39,000/botella    │ ║
║  │ └─ Stock disponible:             80 botellas        │ ║
║  │                                                     │ ║
║  │    [CAMBIAR PRECIO] ← Puedes mover a $50-80K       │ ║
║  └─────────────────────────────────────────────────────┘ ║
║                                                           ║
║  ANÁLISIS COMPETITIVO                                     ║
║  ├─ Precio Promedio Mercado (750ml): $45,500            ║
║  │  Tu precio:    $45,000 (Competitivo ✓)               ║
║  │  Recomendación: MANTÉN por ahora                     ║
║  │                                                       ║
║  └─ Precio Promedio Mercado (1L): $61,000               ║
║     Tu precio:    $60,000 (Competitivo ✓)               ║
║     Recomendación: MANTÉN por ahora                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

### **Estudiante 3 - ROL PLANEACIÓN (Distribuidora Gamma)**

**Pantalla: Dashboard Planeación - Pronóstico**

```
╔═══════════════════════════════════════════════════════════╗
║      PRONÓSTICO DE DEMANDA - DÍA 1, SEMANA 1              ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  DATOS HISTÓRICOS (Ninguno - Es el Día 1)                ║
║  └─ Demanda Semanal Promedio Estimada: 23-34 ut/región  ║
║                                                           ║
║  PARÁMETROS CALCULADOS POR SISTEMA                       ║
║  ┌─────────────────────────────────────────────────────┐ ║
║  │ Producto 750ml:                                     │ ║
║  │ ├─ Demanda Promedio (semanal/región): 34 unidades  │ ║
║  │ ├─ Desviación Estándar: ±7 unidades                │ ║
║  │ ├─ Elasticidad Precio: 1.5x (sensible a precio)    │ ║
║  │ └─ Patrón: Variabilidad normal (aleatorio)          │ ║
║  │                                                     │ ║
║  │ Producto 1L:                                        │ ║
║  │ ├─ Demanda Promedio (semanal/región): 23 unidades  │ ║
║  │ ├─ Desviación Estándar: ±5 unidades                │ ║
║  │ ├─ Elasticidad Precio: 1.5x (sensible a precio)    │ ║
║  │ └─ Patrón: Variabilidad normal (aleatorio)          │ ║
║  └─────────────────────────────────────────────────────┘ ║
║                                                           ║
║  SUGERENCIA DE COMPRA (Basada en stock inicial)          ║
║  ├─ 750ml: Debes comprar ~200+ en próximas 2 semanas    ║
║  └─ 1L: Debes comprar ~150+ en próximas 2 semanas       ║
║                                                           ║
║  NEXT STEPS:                                             ║
║  1. Coordina con COMPRAS para hacer los pedidos          ║
║  2. Stock durará ~5 días si no reordenas                 ║
║  3. Espera datos reales después de Semana 1              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 📊 Ejemplo 3: Comparación de Datos - Todas Igual

### **Tabla Comparativa: DIÍ 1, todas las empresas**

```
┌──────────────────┬──────────────┬──────────────┬──────────────┐
│ PARÁMETRO        │ ALPHA        │ BETA         │ GAMMA        │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ Capital Inicial  │ $50,000,000  │ $50,000,000  │ $50,000,000  │
│ Vino 750ml Stock │ 120 und      │ 120 und      │ 120 und      │
│ Vino 1L Stock    │ 80 und       │ 80 und       │ 80 und       │
│ 750ml Costo      │ $18,000      │ $18,000      │ $18,000      │
│ 1L Costo         │ $21,000      │ $21,000      │ $21,000      │
│ 750ml Precio     │ $45,000      │ $45,000      │ $45,000      │
│ 1L Precio        │ $60,000      │ $60,000      │ $60,000      │
│ Punto Reorden 750│ 72 und       │ 72 und       │ 72 und       │
│ Punto Reorden 1L │ 48 und       │ 48 und       │ 48 und       │
│ Stock Max 750    │ 360 und      │ 360 und      │ 360 und      │
│ Stock Max 1L     │ 240 und      │ 240 und      │ 240 und      │
│ Duración Sim     │ 30 semanas   │ 30 semanas   │ 30 semanas   │
│ Regiones         │ 5            │ 5            │ 5            │
│ Costo Almacen    │ $0.50/und/dí │ $0.50/und/dí │ $0.50/und/dí │
│ Costo Faltante   │ $10/und      │ $10/und      │ $10/und      │
└──────────────────┴──────────────┴──────────────┴──────────────┘

✓ TODAS LAS FILAS SON IDÉNTICAS = COMPETENCIA JUSTA
```

---

## 🎯 Ejemplo 4: Día 5 - Cómo Divergen los Resultados

### **DÍA 5 - Las datos iniciales son iguales, pero las decisiones varían:**

#### **Escenario Alpha: Estrategia Agresiva en Precio**

```
DECISIONES TOMADAS (Días 1-4):
├─ Ventas: Bajaron precio 750ml a $40,000 (vs $45,000 original)
├─ Compras: Hicieron 2 pedidos anticipados
├─ Logística: Distribuyeron más stock a región Caribe
└─ Planeación: Usaron promedio móvil simple para pronóstico

RESULTADOS (Día 5):
├─ Stock 750ml: 45 und (de 120) ⚠️ Bajo pero con cobertura
├─ Ventas 750ml: Altas (por precio bajo)
├─ Ingresos: $450,000 (día 4)
├─ Utilidad: -$120,000 (costos de almacenamiento > ingresos aún)
└─ Nivel Servicio: 92% (bueno)
```

#### **Escenario Beta: Estrategia Conservadora**

```
DECISIONES TOMADAS (Días 1-4):
├─ Ventas: Subieron precio 750ml a $52,000 (vs $45,000 original)
├─ Compras: NO hicieron pedidos aún (esperan datos)
├─ Logística: Stock concentrado en centro
└─ Planeación: Esperan completar semana 1 para analizar

RESULTADOS (Día 5):
├─ Stock 750ml: 85 und (de 120) ✓ Aún alto
├─ Ventas 750ml: Bajas (por precio alto)
├─ Ingresos: $180,000 (día 4)
├─ Utilidad: -$90,000 (menos costos que Alpha)
└─ Nivel Servicio: 75% (perdieron ventas por precio)
```

#### **Escenario Gamma: Estrategia Equilibrada**

```
DECISIONES TOMADAS (Días 1-4):
├─ Ventas: Mantuvieron precio inicial $45,000
├─ Compras: 1 pedido moderado para semana 3
├─ Logística: Distribución balanceada por regiones
└─ Planeación: Analizando datos conforme llegan

RESULTADOS (Día 5):
├─ Stock 750ml: 62 und (de 120) ✓ Equilibrado
├─ Ventas 750ml: Moderadas
├─ Ingresos: $320,000 (día 4)
├─ Utilidad: -$105,000 (promedio)
└─ Nivel Servicio: 88% (bueno)
```

### **¿QUÉ PASÓ?**

```
DÍA 1 (INICIAL): TODAS IDÉNTICAS ✓
    ├─ Capital: $50M = $50M = $50M
    ├─ Stock: 120 = 120 = 120
    ├─ Precio: $45K = $45K = $45K
    └─ → NINGUNA VENTAJA INICIAL

DÍA 5 (DESPUÉS DE DECISIONES): COMPLETAMENTE DIFERENTES ✗
    ├─ Stock: 45 < 62 < 85 (diferentes decisiones de compra)
    ├─ Precio: $40K < $45K < $52K (diferentes estrategias)
    ├─ Ingresos: $180K < $320K < $450K (resultado de decisiones)
    └─ → DIFERENCIAS = 100% POR DECISIONES, NO POR VENTAJA INICIAL
```

---

## 📈 Ejemplo 5: Fórmulas y Cálculos Automáticos

### **Cómo el Sistema Calcula los Parámetros Automáticamente**

**Input del Admin:**
```
Capital Inicial: $50,000,000
Inv. 750ml: 120 unidades
Inv. 1L: 80 unidades
```

**Sistema Calcula Automáticamente:**

```python
# Constantes (fijas)
DIAS_COBERTURA = 5        # 5 días de cobertura
REGIONES = 5              # 5 regiones
DIAS_REORDEN = 3          # 3 días de anticipación
DIAS_SEGURIDAD = 1        # 1 día de amortiguador
FACTOR_DESVIACION = 0.20  # 20% variación

# Para cada producto (750ml y 1L)
inv_inicial = 120  # (ej. 750ml)

# PASO 1: Demanda promedio semanal por región
demanda_promedio = max(1, round(
    inv_inicial * 7 / (DIAS_COBERTURA * REGIONES)
))
# = 120 × 7 / (5 × 5) = 34

# PASO 2: Desviación (volatilidad)
desviacion_demanda = max(1, round(
    demanda_promedio * FACTOR_DESVIACION
))
# = 34 × 0.20 = 7

# PASO 3: Consumo diario total (todas regiones)
consumo_diario = (demanda_promedio / 7.0) * REGIONES
# = (34 / 7) × 5 = 24

# PASO 4: Punto de reorden
punto_reorden = max(1, round(
    consumo_diario * DIAS_REORDEN
))
# = 24 × 3 = 72

# PASO 5: Stock de seguridad
stock_seguridad = max(1, round(
    consumo_diario * DIAS_SEGURIDAD
))
# = 24 × 1 = 24

# PASO 6: Stock máximo (múltiplo del inicial)
stock_maximo = inv_inicial * 3
# = 120 × 3 = 360
```

**Resultado en BD:**
```
PRODUCTO (Vino 750ml):
├─ demanda_promedio: 34
├─ desviacion_demanda: 7
└─ stock_maximo: 360

INVENTARIO (Empresa X, Vino 750ml):
├─ cantidad_actual: 120
├─ punto_reorden: 72
├─ stock_seguridad: 24
└─ stock_maximo: 360
```

---

## 🔄 Ejemplo 6: Ciclo del Día 1 al Día 30

### **Timeline Simulación - Qué Sucede**

```
┌─────────────────────────────────────────────────────────┐
│ DÍA 1-5: FASE CRÍTICA (FALTA DE REACCIÓN)              │
├─────────────────────────────────────────────────────────┤
│ Status Inicial: IGUAL para todos (120 y 80 unidades)    │
│ Presión: ALTA - Stock durará solo 5 días                │
│ Acción crítica: COMPRAS debe hacer pedidos AHORA        │
│ Riesgo: Si no compran, Día 6 estarán en problemas      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DÍA 6-14: FASE DE DIFERENCIACIÓN                       │
├─────────────────────────────────────────────────────────┤
│ Status: EMPIEZAN A VERSE DIFERENCIAS                    │
│ Quién reaccionó (compró): Stock normalizado              │
│ Quién NO reaccionó: Stock bajo o quiebres               │
│ Acción: Ajuste de estrategias basado en datos reales    │
│ Riesgo: Empezar con desventaja acumulada                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DÍA 15-21: FASE DE OPTIMIZACIÓN                        │
├─────────────────────────────────────────────────────────┤
│ Status: ESTRATEGIAS CRISTALIZADAS                       │
│ Delta: Equipos con buena gestión ↑↑ vs malos ↓↓         │
│ Acción: Fine-tuning de precios, compras, distribución   │
│ Riesgo: Si empezaste mal, es difícil recuperar          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DÍA 22-30: FASE FINAL                                  │
├─────────────────────────────────────────────────────────┤
│ Status: RESULTADOS CONSOLIDADOS                         │
│ Winners: Equipos con buena gestión integral             │
│ Losers: Equipos que no reaccionaron a tiempo            │
│ Acción: Análisis retrospectivo de decisiones            │
│ Aprendizaje: Qué funcionó, qué falló, cómo mejorar     │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Ejemplo 7: Seis Empresas con Capital Diferenciado (Opcional)

### **Si el admin decide diferenciar el capital:**

```
Profesor ingresa en modal de configuración:
┌──────────────────────────────────────┐
│ Crear Nueva Simulación               │
├──────────────────────────────────────┤
│ Capital Inicial: $50,000,000         │
│ Inv. 750ml: 120 unidades             │
│ Inv. 1L: 80 unidades                 │
│ [CREAR]                              │
└──────────────────────────────────────┘

Después de crear, profesor edita cada empresa:
Profesor → Gestionar Empresas → Selecciona empresa

┌─────────────────────────────────┐
│ EDITAR EMPRESA "Distibuida Rich" │
├─────────────────────────────────┤
│ Capital Actual: $50,000,000      │
│                ↓ (cambio manual)  │
│ Capital Actual: $100,000,000 ✓   │
│ [GUARDAR]                        │
└─────────────────────────────────┘
```

**Resultado:**

```
┌────────────────────────────────────────────────────────┐
│ SIMULACIÓN CON CAPITAL DIFERENCIADO                   │
├────────────────────────────────────────────────────────┤
│ Empresa "Rich Fund"      → Capital: $100,000,000       │
│ Empresa "Medium Corp"    → Capital: $50,000,000        │
│ Empresa "Startup"        → Capital: $25,000,000        │
│ Empresa "Mega Investor"  → Capital: $150,000,000       │
│ Empresa "Bootstrap"      → Capital: $15,000,000        │
│ Empresa "Standard"       → Capital: $50,000,000        │
│                                                        │
│ ⚠️ NOTA: Ahora hay VENTAJA INICIAL                     │
│ "Rich Fund" tiene 4x más capital que "Bootstrap"       │
│                                                        │
│ ÚTIL PARA: Estudiar impacto del capital en decisiones │
│            Simular realidades económicas diferentes    │
└────────────────────────────────────────────────────────┘
```

---

## ✅ Ejemplo 8: Guión de Explicación para Estudiantes

### **Lo que Dices en la Primera Clase**

```
"Bienvenidos al Simulador de Cadena de Abastecimiento.

Hoy comenzamos todas las empresas EXACTAMENTE IGUAL:

📊 Capital: $50 millones (para todos)
📦 Inventario 750ml: 120 botellas (para todos)
📦 Inventario 1L: 80 botellas (para todos)
💰 Precios: $45,000 (750ml) y $60,000 (1L) iniciales
🏭 Costos: $18,000 (750ml) y $21,000 (1L)
🗺️  Mercado: 5 regiones (todos acceden a lo mismo)
⏱️  Tiempo: 30 semanas (para todos)

ES UN ENTORNO 100% JUSTO.

Lo que NOS IMPORTA es cómo USTEDES gestionan lo que tienen.

Sus decisiones sobre:
┌──────────────┐
│ • Precios    │  Determinarán completamente
│ • Compras    │  su éxito o fracaso.
│ • Logística  │
│ • Pronósticos│
└──────────────┘

Si una empresa gana, es porque DECIDIÓ MEJOR.
Si una empresa pierde, es porque DECIDIÓ PEOR.

No hay excusa de falta de capital, ni de inventario inicial.
Todos empezamos del mismo punto de salida.

¿Preguntas?"
```

---

## 📚 Conclusión

**Los datos iniciales están diseñados para ser:**

✅ **IDÉNTICOS** - Máxima equidad  
✅ **JUSTOS** - Nadie tiene ventaja injusta  
✅ **EDUCATIVOS** - Refleja gestión de cadena real  
✅ **COMPARABLES** - Todos sobre la misma base  

**El resultado del juego es 100% función de las decisiones tomadas, NO de las condiciones iniciales.**

---

**Versión:** 1.0 | **Fecha:** Abril 2026
