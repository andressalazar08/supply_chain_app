# 🚀 GUÍA RÁPIDA - MÓDULO DE VENTAS

## ⚡ Inicio Rápido

### 1. Reinicializar Base de Datos
```bash
cd supply_chain_app
python init_db.py
```
✅ **Resultado esperado**: 309 registros de ventas históricas creados

### 2. Iniciar Aplicación
```bash
python app.py
```
🌐 **URL**: http://localhost:5000

### 3. Login como Ventas
```
👤 Usuario: estudiante_1_1
🔑 Contraseña: estudiante123
```

---

## 🎯 Pruebas del Módulo

### ✅ Test 1: Ver Dashboard
1. Login como `estudiante_1_1`
2. Deberías ver automáticamente el **Dashboard de Ventas**
3. Verificar que se muestran:
   - ✔️ 4 cards con métricas (Ingresos, Unidades, Nivel Servicio, Pérdidas)
   - ✔️ Gráfico de ventas por región
   - ✔️ Gráfico de ingresos por producto
   - ✔️ Tabla de desempeño regional
   - ✔️ Panel de ajuste de precios (5 productos)

### ✅ Test 2: Ajustar Precio
1. En la sección "Ajuste de Precios"
2. Buscar "Laptop Empresarial"
   - Costo: $800
   - Precio Actual: $1,200
   - Margen: ~33%
3. Cambiar precio a: `1,350`
4. Click en "Aplicar"
5. ✔️ Debería aparecer mensaje: "Precio de Laptop Empresarial actualizado a $1,350.00 (+12.5%)"

### ✅ Test 3: Ver Análisis Regional
1. Click en "Análisis Regional" en el sidebar
2. Deberías ver:
   - ✔️ Gráfico de comparación de regiones
   - ✔️ 5 cards detalladas (una por región)
   - ✔️ Barras de nivel de cumplimiento
   - ✔️ Insights (Mejor región y Oportunidad de mejora)

### ✅ Test 4: Gráfico Precio vs Demanda
1. Volver al Dashboard
2. En la sección "Tendencias: Precio vs Demanda"
3. Seleccionar diferentes productos del dropdown
4. ✔️ El gráfico debe actualizarse mostrando 2 líneas (Precio y Demanda)

### ✅ Test 5: Verificar Regiones en Historial
1. Scroll hasta "Historial de Ventas Recientes"
2. ✔️ Verificar que cada venta tiene una badge de región con color:
   - 🔵 Caribe (azul)
   - 🟢 Pacífica (verde)
   - 🟠 Orinoquía (naranja)
   - 🟢 Amazonía (verde oscuro)
   - 🟣 Andina (púrpura)

---

## 🔧 Pruebas con el Profesor

### Test 6: Avanzar un Día
1. Logout (`estudiante_1_1`)
2. Login como profesor:
   ```
   Usuario: admin
   Contraseña: admin123
   ```
3. En el Panel de Control:
   - Click en "Iniciar Simulación" (si está pausada)
   - Click en "Avanzar 1 Día"
4. Logout y volver a entrar como `estudiante_1_1`
5. ✔️ Deberías ver datos del **Día 8** con nuevas ventas generadas

### Test 7: Verificar Efecto de Cambio de Precio
1. Como `estudiante_1_1`, anota los ingresos actuales de un producto
2. Cambia el precio (ej: sube 20%)
3. Login como `admin`
4. Avanza 2-3 días
5. Vuelve como `estudiante_1_1`
6. ✔️ Verifica en el gráfico Precio vs Demanda que la demanda cambió

---

## 📊 Datos de Ejemplo Esperados

### Productos Iniciales
| Producto | Precio Base | Costo | Elasticidad |
|----------|-------------|-------|-------------|
| Laptop Empresarial | $1,200 | $800 | 1.8 |
| Monitor LED 24" | $300 | $200 | 1.5 |
| Teclado Mecánico | $150 | $100 | 1.3 |
| Mouse Inalámbrico | $50 | $30 | 1.2 |
| Impresora Multifuncional | $400 | $280 | 1.6 |

### Distribución Regional Esperada
- **Andina**: ~28% de ventas (factor 1.2)
- **Caribe**: ~21% de ventas (factor 0.9)
- **Pacífica**: ~20% de ventas (factor 0.85)
- **Orinoquía**: ~16% de ventas (factor 0.7)
- **Amazonía**: ~14% de ventas (factor 0.6)

---

## 🐛 Troubleshooting

### Los gráficos están vacíos
**Solución**: 
```bash
python init_db.py
```
Asegúrate de que se crearon 309 ventas históricas.

### No puedo cambiar el precio
**Causa**: Precio inferior al costo
**Solución**: El precio debe ser ≥ costo unitario del producto

### Error de login
**Solución**: 
1. Verifica el formato: `estudiante_X_Y` donde X=1-4, Y=1-3
2. Contraseña: `estudiante123`

### La región no aparece en las ventas
**Causa**: Ventas antiguas sin región
**Solución**: Ejecutar `python init_db.py` para regenerar con nuevos campos

---

## 🎓 Escenarios de Aprendizaje

### Escenario 1: Maximizar Ingresos
**Objetivo**: Encontrar el precio óptimo para Laptop
1. Precio actual: $1,200
2. Prueba aumentar a $1,400 → observa demanda
3. Prueba bajar a $1,100 → observa demanda
4. Calcula ingreso total en cada caso
5. **Aprendizaje**: Elasticidad alta significa que bajar precio puede aumentar ingresos totales

### Escenario 2: Balancear Regiones
**Objetivo**: Mejorar ventas en región débil
1. Identifica región con más ventas perdidas
2. Comunica a compañero de Logística
3. Logística aumenta inventario
4. Observa reducción en ventas perdidas
5. **Aprendizaje**: Coordinación entre roles es clave

### Escenario 3: Gestión de Margen
**Objetivo**: Mantener margen >20% en todos los productos
1. Revisa margenes actuales
2. Productos con margen <20%: sube precio
3. Monitorea impacto en demanda
4. Ajusta si es necesario
5. **Aprendizaje**: Balance entre margen y volumen

---

## 📸 Capturas Esperadas

### Dashboard Principal
```
┌─────────────────────────────────────────────────────┐
│  Dashboard de Ventas                                │
│  Distribuidora Alpha | Día 7 | EN_CURSO             │
├─────────────────────────────────────────────────────┤
│  [💰 Ingresos]  [📦 Unidades]  [📈 Servicio]  [⚠️ Pérdidas] │
│   $45,230        320            92.5%          24      │
├─────────────────────────────────────────────────────┤
│  [Gráfico Regiones]        [Gráfico Productos]      │
│  📈 Líneas por región      📊 Barras por producto   │
├─────────────────────────────────────────────────────┤
│  Tabla: Desempeño Regional                          │
│  Caribe    | $12,450 | 95 unid | 5 perdidas | 23%  │
│  Pacífica  | $10,200 | 82 unid | 8 perdidas | 20%  │
│  ...                                                 │
└─────────────────────────────────────────────────────┘
```

---

## ✅ Checklist de Funcionalidades

- [x] Ver métricas del día en cards
- [x] Gráfico de ventas por región (líneas)
- [x] Gráfico de ingresos por producto (barras)
- [x] Tabla de desempeño regional
- [x] Ajustar precios de productos
- [x] Validación de precio mínimo (costo)
- [x] Registro de decisiones en BD
- [x] Vista de análisis regional detallado
- [x] Gráfico comparativo de regiones
- [x] Cards individuales por región
- [x] Insights automáticos (mejor/peor)
- [x] Gráfico precio vs demanda
- [x] Selector de producto dinámico
- [x] Historial de ventas con regiones
- [x] Badges de color por región
- [x] APIs JSON para Chart.js
- [x] Generación automática en procesar_dia()
- [x] Aplicación de elasticidad de precio
- [x] Factores regionales de demanda

---

**Estado**: ✅ TODAS LAS FUNCIONALIDADES IMPLEMENTADAS Y PROBADAS  
**Última Actualización**: Noviembre 2025
