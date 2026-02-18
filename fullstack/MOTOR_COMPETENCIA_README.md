# Motor de Competencia de Precios - Resumen de Implementación

## ✅ Funcionalidades Implementadas

### 1. **Motor de Competencia de Precios** (`utils/procesamiento_dias.py`)

#### Función `calcular_precios_mercado()`
- Calcula el precio promedio del mercado para cada producto
- Obtiene información de stock disponible de todas las empresas
- Retorna: precio promedio y lista de empresas con sus precios y stock

#### Función `calcular_market_share()`
Distribuye market share según competitividad de precio:
- **Precio >150% del promedio**: 0% market share (nadie compra)
- **Precio 120-150%**: 10-30% market share (ventas bajas)
- **Precio 90-120%**: 40-60% market share (ventas normales)
- **Precio 70-90%**: 50-80% market share (ventas altas)
- **Precio <70%**: 30-50% market share (sospecha de calidad)

Factores adicionales:
- Elasticidad del producto (vinos premium menos sensibles al precio)
- Aleatoriedad del consumidor (±5%)
- Sin stock = sin ventas (automático)

#### Función `distribuir_demanda_competitiva()`
- Genera demanda TOTAL del mercado (no por empresa)
- Distribuye la demanda entre TODAS las empresas competidoras
- Normaliza market shares para que sumen 100%
- Limita ventas por stock disponible
- Reasigna demanda no satisfecha a otras empresas

#### Función `procesar_ventas_dia()` - MODIFICADA
Ahora con competencia realista:
- Genera demanda total del mercado por producto y región
- Llama al motor de distribución competitiva
- Cada empresa recibe su porción según competitividad
- Registra ventas perdidas por dos razones:
  * **Sin stock**: Tenía demanda pero no inventario
  * **Precio no competitivo**: Tenía stock pero precio muy alto

---

### 2. **Dashboard de Competitividad** (`routes/estudiante.py`)

#### Nuevo endpoint: `/api/ventas/competitividad`
Retorna para cada producto:
- **Precio de tu empresa**
- **Precio promedio del mercado**
- **Diferencia porcentual** (+X% o -X%)
- **Clasificación**: Muy Alto | Alto | Competitivo | Bajo | Muy Bajo
- **Color del badge**: danger | warning | success | info
- **Expectativa de ventas**: Muy Bajas | Bajas | Normales | Altas | Medias
- **Stock actual**: Para identificar oportunidades perdidas

---

### 3. **Interfaz de Competitividad** (`templates/estudiante/ventas/dashboard.html`)

#### Nueva sección en Dashboard (Tab 1)
Tabla de análisis de competitividad que muestra:
- 🍷 Producto
- 💰 Tu precio vs Precio mercado
- 📊 Diferencia porcentual con emoji (📈/📉/➡️)
- 🎯 Estado competitivo (badge coloreado)
- 📈 Expectativa de ventas
- 📦 Stock disponible

#### Leyenda interpretativa:
```
- Muy Alto (>+50%): No competitivo - Ventas muy bajas esperadas
- Alto (+20% a +50%): Precio alto - Ventas bajas esperadas
- Competitivo (-10% a +20%): Rango del mercado - Ventas normales
- Bajo (-30% a -10%): Precio atractivo - Ventas altas esperadas
- Muy Bajo (<-30%): Sospechosamente bajo - Puede generar desconfianza
```

---

### 4. **Trazabilidad en Movimientos de Inventario**

Los movimientos de salida por venta ahora incluyen:
```
"Venta día X - Region Y - Market share: Z% - Precio 50%+ sobre mercado ($XX,XXX)"
```

Información registrada:
- Día de simulación
- Región de venta
- % de mercado capturado
- Comparación con precio promedio del mercado

---

### 5. **Catálogo de Productos Actualizado**

8 productos de vino premium:

| Código | Nombre | Categoría | Costo | Precio Base | Margen |
|--------|--------|-----------|-------|-------------|---------|
| SV-750 | Sangre de la Vid 750ml | Tinto | $45,000 | $75,000 | 66% |
| SV-1L | Sangre de la Vid 1L | Tinto | $58,000 | $95,000 | 63% |
| ED-750 | Elixir Dorado 750ml | Blanco | $42,000 | $70,000 | 66% |
| ED-1L | Elixir Dorado 1L | Blanco | $54,000 | $90,000 | 66% |
| SR-750 | Susurro Rosado 750ml | Rosado | $38,000 | $62,000 | 63% |
| SR-1L | Susurro Rosado 1L | Rosado | $49,000 | $80,000 | 63% |
| OP-750 | Oceano Profundo 750ml | Especial | $52,000 | $85,000 | 63% |
| OP-1L | Oceano Profundo 1L | Especial | $68,000 | $110,000 | 61% |

Características por producto:
- **Demanda promedio diferenciada** (750ml: 80-120 und, 1L: 55-85 und)
- **Elasticidad de precio** (1.5 - 2.0, según tipo)
- **Tiempo de entrega** (3-4 días)

---

## 🎮 Ejemplos de Comportamiento Realista

### Escenario 1: Guerra de Precios
```
Demanda total: 150 unidades de Sangre de la Vid 750ml - Región Andina

Empresa A: $75,000 (100%) + Stock 200 → Recibe 45 und (30%)
Empresa B: $65,000 (86%) + Stock 100  → Recibe 68 und (45%)
Empresa C: $90,000 (120%) + Stock 500 → Recibe 22 und (15%)
Empresa D: $150,000 (200%) + Stock 300 → Recibe 0 und (0%) ❌

Total distribuido: 135 unidades
Demanda no satisfecha: 15 unidades (Empresa B se quedó sin stock antes de tiempo)
```

### Escenario 2: Monopolio Temporal
```
Demanda total: 100 unidades de Elixir Dorado 1L - Región Caribe

Empresa A: $90,000 (100%) + Stock 0   → 0 und + 30 ventas perdidas ❌
Empresa B: $95,000 (105%) + Stock 0   → 0 und + 25 ventas perdidas ❌
Empresa C: $110,000 (122%) + Stock 200 → Recibe 100 und (100%) ✅

Resultado: Empresa C captura TODO el mercado porque es la ÚNICA con stock,
aunque su precio sea alto. ¡Oportunidad de oro!
```

### Escenario 3: Precio Sospechosamente Bajo
```
Demanda total: 80 unidades de Oceano Profundo 750ml - Región Pacífica

Empresa A: $85,000 (100%) + Stock 150 → Recibe 35 und (44%)
Empresa B: $50,000 (58%) + Stock 200  → Recibe 30 und (37%) ⚠️ 
Empresa C: $82,000 (96%) + Stock 100  → Recibe 15 und (19%)

Nota: Empresa B tiene precio muy bajo pero NO captura todo el mercado
porque los clientes sospechan de la calidad.
```

---

## 📊 Métricas de Ventas Mejoradas

### Ventas Perdidas ahora se clasifican en:
1. **Por falta de stock**: Tenías demanda asignada pero no inventario
2. **Por precio no competitivo**: Tenías stock pero tu precio era >120% del mercado

### Dashboard muestra:
- ✅ Cantidad vendida real
- ❌ Cantidad perdida (total)
- 💰 Ingresos generados
- 📊 Market share obtenido (%)
- 🎯 Competitividad vs mercado

---

## 🚀 Próximos Pasos Sugeridos

1. **Precios por región** (futuro): Permitir que cada empresa configure precios diferentes por región
2. **Histórico de precios**: Gráficas de evolución de precios del mercado
3. **Alertas automáticas**: "⚠️ Tu precio de X está 60% sobre el mercado - 0 ventas esperadas"
4. **Simulador de precios**: "Si bajo mi precio a $X, capturaré Y% del mercado"
5. **Reputación de marca**: Empresas con más ventas históricas tienen +5% de fidelización

---

## 🧪 Cómo Probar

### 1. Ejecutar script de prueba:
```bash
python test_motor_competencia.py
```

### 2. Configurar precios diferentes:
- Ir a Dashboard Ventas → Tab "Configurar Precios"
- Ajustar precios de diferentes productos
- Hacer clic en "Aplicar Cambios de Precios"

### 3. Ver competitividad:
- Dashboard Ventas → Tab 1 → Sección "Análisis de Competitividad"
- Ver tu posición vs el mercado

### 4. Avanzar día de simulación:
- Como profesor, avanzar el día
- Revisar ventas realizadas por cada empresa
- Comparar quién vendió más según precios

### 5. Verificar movimientos:
- Ir a Logística → Movimientos de Inventario
- Ver observaciones con info de market share y competitividad

---

## ✨ Características Implementadas

✅ Motor de competencia de precios  
✅ Distribución realista de demanda según competitividad  
✅ Cálculo automático de precio promedio del mercado  
✅ Market share proporcional a competitividad  
✅ Penalización por precios muy altos (0 ventas)  
✅ Penalización por precios sospechosamente bajos  
✅ Prioridad a empresas con stock disponible  
✅ Reasignación de demanda cuando hay agotamiento  
✅ Dashboard de competitividad en tiempo real  
✅ Ventas perdidas por precio no competitivo  
✅ Trazabilidad de market share en movimientos  
✅ 8 productos de vino con características diferenciadas  
✅ Inventarios iniciales para todas las empresas  

---

¡El sistema ahora simula un mercado competitivo realista! 🍷📈
