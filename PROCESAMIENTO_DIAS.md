# 📅 Sistema de Procesamiento de Días Simulados

## 🎯 Descripción General

El sistema funciona con **días simulados** que avanzan únicamente cuando el **profesor** presiona el botón **"Avanzar al Día X"**. Este mecanismo permite que los estudiantes tomen decisiones estratégicas entre cada día simulado.

---

## 🔄 Flujo de Procesamiento Automático

Cuando el profesor avanza al siguiente día, el sistema ejecuta automáticamente las siguientes operaciones:

### 1️⃣ **Procesamiento de Ventas** 
```
Para cada empresa:
  Para cada producto:
    Para cada región (5 regiones de Colombia):
      ✓ Generar demanda aleatoria basada en:
         - Demanda promedio del producto
         - Desviación estándar
         - Disrupciones activas (aumento_demanda)
      
      ✓ Procesar venta:
         - Si hay stock → Vender
         - Si no hay stock → Registrar venta perdida
      
      ✓ Actualizar inventario:
         - Reducir cantidad_actual
         - Crear MovimientoInventario (salida_venta)
      
      ✓ Calcular financieros:
         - Ingreso = cantidad_vendida × precio_venta
         - Costo = cantidad_vendida × costo_promedio
         - Margen = ingreso - costo
```

**Archivo:** `utils/procesamiento_dias.py → procesar_ventas_dia()`

---

### 2️⃣ **Recepción de Compras**
```
Para cada empresa:
  ✓ Buscar órdenes de compra con dia_entrega == dia_actual
  
  Para cada orden que llega:
    ✓ Actualizar inventario:
       - Calcular nuevo costo promedio ponderado
       - Incrementar cantidad_actual
       - Crear MovimientoInventario (entrada_compra)
    
    ✓ Cambiar estado de orden:
       - De "en_transito" → "recibido"
```

**Consideraciones:**
- Los tiempos de entrega se calculan al crear la orden:
  - `dia_entrega = dia_actual + lead_time_producto + impacto_disrupciones`
- El costo promedio ponderado mantiene la trazabilidad contable

**Archivo:** `utils/procesamiento_dias.py → procesar_llegadas_compras()`

---

### 3️⃣ **Entrega de Despachos Regionales**
```
Para cada empresa:
  ✓ Buscar despachos con dia_entrega_estimado == dia_actual
  
  Para cada despacho que llega:
    ✓ Cambiar estado:
       - De "en_transito" → "entregado"
       - Registrar dia_entrega_real
    
    ✓ Liberar inventario reservado:
       - cantidad_reservada -= cantidad_despachada
```

**Archivo:** `utils/procesamiento_dias.py → procesar_despachos_regionales()`

---

### 4️⃣ **Cálculo de Métricas de Desempeño**
```
Para cada empresa:
  ✓ Agregar ventas del día:
     - ingresos_dia = Σ ingresos_totales
     - costos_ventas_dia = Σ costos_totales
  
  ✓ Agregar compras del día:
     - costos_compras_dia = Σ costos_ordenes_creadas
  
  ✓ Calcular nivel de servicio:
     - nivel_servicio = (total_vendido / total_solicitado) × 100
  
  ✓ Calcular valor de inventario:
     - valor_inventario = Σ (cantidad × costo_promedio)
  
  ✓ Calcular rotación de inventario:
     - rotacion = costos_ventas / valor_inventario
  
  ✓ Actualizar capital de la empresa:
     - capital_actual += (ingresos - costos_compras)
  
  ✓ Crear registro Metrica con todos los datos
```

**Archivo:** `utils/procesamiento_dias.py → calcular_metricas_dia()`

---

### 5️⃣ **Verificación de Alertas de Inventario**
```
Para cada producto en inventario:
  ✓ Alerta CRÍTICA:
     - Si cantidad_actual ≤ stock_seguridad
  
  ✓ Alerta ADVERTENCIA:
     - Si cantidad_actual ≤ punto_reorden
  
  ✓ Alerta INFORMACIÓN:
     - Si cantidad_actual > 3 × punto_reorden (sobrestock)
```

**Archivo:** `utils/procesamiento_dias.py → verificar_alertas_inventario()`

---

### 6️⃣ **Mantenimiento de Disrupciones**
```
✓ Disrupciones activas continúan afectando si:
   - dia_actual >= dia_inicio
   - dia_actual <= dia_fin
   - activo == True

✓ Las disrupciones se desactivan automáticamente cuando:
   - dia_actual > dia_fin
```

**Archivo:** `models.py → DisrupcionActiva.esta_activa()`

---

## 🎮 Control del Profesor

### Estados de la Simulación

| Estado | Descripción | Acciones Disponibles |
|--------|-------------|---------------------|
| **pausado** | Estado inicial | Iniciar |
| **en_curso** | Simulación activa | Pausar, Avanzar Día, Finalizar |
| **finalizado** | Simulación terminada | Reiniciar |

### Botones de Control

#### 1. **Iniciar Simulación**
- Cambia estado de `pausado` → `en_curso`
- Registra `fecha_inicio`
- Permite a estudiantes trabajar

#### 2. **Pausar**
- Cambia estado de `en_curso` → `pausado`
- Estudiantes pueden seguir tomando decisiones
- Profesor puede revisar datos sin avanzar tiempo

#### 3. **Avanzar 1 Día** ⭐
```python
# Ruta: /profesor/control-simulacion
# Acción: avanzar_dia

1. Verificar que estado == 'en_curso'
2. Incrementar simulacion.dia_actual += 1
3. Ejecutar avanzar_simulacion():
   - Procesar ventas
   - Procesar compras
   - Procesar despachos
   - Calcular métricas
   - Verificar alertas
4. Mostrar resumen de eventos procesados
5. Mostrar alertas críticas
```

**Importante:** Esta es la acción principal que hace avanzar el tiempo en la simulación.

#### 4. **Finalizar**
- Cambia estado a `finalizado`
- Registra `fecha_fin`
- Bloquea nuevas acciones de estudiantes

#### 5. **Reiniciar**
- Requiere confirmación escribiendo "REINICIAR"
- Vuelve al día 1
- Mantiene datos históricos
- Estado → `pausado`

---

## 📊 Resumen de Procesamiento

Después de avanzar un día, el sistema muestra:

```
✅ Día X → Día X+1 procesado exitosamente

📊 Resumen:
   - 45 ventas procesadas
   - 3 compras recibidas
   - 2 despachos entregados

⚠️ Alertas:
   - Distribuidora Alpha: 2 alertas críticas de inventario
   - Comercializadora Beta: 1 alerta de advertencia
```

---

## 🔗 Integración con Disrupciones

Las disrupciones afectan el procesamiento de cada día:

### Retraso de Proveedor
```python
# Afecta: procesar_llegadas_compras()
lead_time_ajustado = lead_time_base + calcular_impacto_lead_time(...)
dia_entrega = dia_orden + lead_time_ajustado
```

### Aumento de Demanda
```python
# Afecta: procesar_ventas_dia()
demanda_ajustada = calcular_impacto_demanda(demanda_base, ...)
cantidad_solicitada = round(demanda_ajustada)
```

### Reducción de Capacidad
```python
# Afecta: Limitaciones de despacho (futuro)
capacidad_ajustada = calcular_impacto_capacidad(capacidad_base, ...)
```

### Aumento de Costos
```python
# Afecta: Órdenes de compra creadas por estudiantes
costo_ajustado = calcular_impacto_costo(costo_base, ...)
```

### Región Bloqueada
```python
# Afecta: Ventas y despachos a esa región
disponible, dias_extra = verificar_region_disponible(...)
if not disponible:
    # No procesar ventas/despachos
```

---

## 💡 Casos de Uso

### Caso 1: Día Normal
```
Profesor presiona "Avanzar al Día 2"

Empresa A:
  ✓ 15 ventas (12 cumplidas, 3 perdidas por falta de stock)
  ✓ 1 compra recibida (+500 unidades PROD001)
  ✓ 0 despachos entregados
  ✓ Capital: $1,000,000 → $1,018,500

Resultado: Nivel de servicio 80%
```

### Caso 2: Día con Disrupción
```
Profesor activa: "Paro Nacional de Transportadores" (severidad alta)
Profesor presiona "Avanzar al Día 5"

Empresa A:
  ✓ 20 ventas (demanda aumentada por pánico de compra)
  ✓ 0 compras recibidas (retraso de +10 días)
  ✓ 0 despachos entregados (regiones bloqueadas)
  ✓ Capital: $1,018,500 → $995,000 (ventas perdidas)

Resultado: Nivel de servicio 45% ⚠️
```

### Caso 3: Semana de Recuperación
```
Días 6-7: Sin disrupciones
Profesor avanza 2 días consecutivos

Empresa A:
  ✓ Llegan 3 órdenes atrasadas
  ✓ Inventario se repone
  ✓ Ventas se normalizan
  ✓ Nivel de servicio: 45% → 95% 📈

Resultado: Recuperación exitosa
```

---

## 🛠️ Archivos Involucrados

| Archivo | Responsabilidad |
|---------|----------------|
| `utils/procesamiento_dias.py` | Lógica de procesamiento automático |
| `routes/profesor.py` | Rutas de control (`control_simulacion`) |
| `templates/profesor/dashboard.html` | UI de control |
| `models.py` | Modelos (Venta, Compra, Metrica, etc.) |
| `utils/disrupciones.py` | Impacto de disrupciones |

---

## 📈 Métricas Calculadas Automáticamente

| Métrica | Fórmula | Dónde se usa |
|---------|---------|--------------|
| **Ingresos** | Σ (cantidad_vendida × precio_unitario) | Dashboard, Reportes |
| **Costos** | Σ (cantidad_vendida × costo_unitario) + costos_compras | Dashboard, Reportes |
| **Utilidad** | ingresos - costos | Ranking de empresas |
| **Nivel de Servicio** | (total_vendido / total_solicitado) × 100 | KPI principal |
| **Valor Inventario** | Σ (cantidad × costo_promedio) | Balance |
| **Rotación** | costos_ventas / valor_inventario | Eficiencia |
| **Capital Actual** | capital_inicial + Σ utilidades - Σ compras | Liquidez |

---

## 🎓 Para Estudiantes

Entre cada avance de día, los estudiantes deben:

1. **Analizar resultados del día anterior**
   - Revisar ventas perdidas
   - Verificar nivel de servicio
   - Analizar utilidades

2. **Tomar decisiones**
   - **Ventas:** Analizar demanda por región/producto
   - **Planeación:** Crear pronósticos con métodos estadísticos
   - **Compras:** Crear órdenes según pronósticos
   - **Logística:** Ajustar puntos de reorden y stock de seguridad

3. **Coordinar con equipo**
   - Planeación comunica pronósticos a Compras
   - Compras informa tiempos de llegada a Logística
   - Ventas reporta productos con más demanda

---

## ⚠️ Importante

- ✅ **Solo el profesor** puede avanzar días
- ✅ El procesamiento es **automático e instantáneo**
- ✅ Los estudiantes **no pueden deshacer** días avanzados
- ✅ Todas las operaciones se **registran en base de datos**
- ✅ Las **disrupciones se aplican automáticamente** si están activas
- ✅ El sistema **genera alertas** de problemas críticos

---

## 🔮 Próximas Mejoras

- [ ] Avance de múltiples días (ej: "Avanzar 5 días")
- [ ] Simulación en tiempo real (1 día = 1 minuto real)
- [ ] Exportar log de eventos del día
- [ ] Vista previa de eventos antes de avanzar
- [ ] Deshacer último día avanzado (rollback)

---

**Sistema desarrollado para simular entornos empresariales reales en contexto educativo colombiano.**
