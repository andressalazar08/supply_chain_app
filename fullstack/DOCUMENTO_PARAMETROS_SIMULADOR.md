# Documento de Parametros del Simulador

Este documento consolida los parametros funcionales vigentes de la herramienta.

## 1. Costos de productos por referencia

| Codigo | Producto | Costo unitario |
|---|---|---:|
| SV-750 | Sangre de la Vid 750ml | $20.000 |
| SV-1L | Sangre de la Vid 1L | $25.000 |
| ED-750 | Elixir Dorado 750ml | $17.000 |
| ED-1L | Elixir Dorado 1L | $20.000 |
| SR-750 | Susurro Rosado 750ml | $15.000 |
| SR-1L | Susurro Rosado 1L | $18.000 |
| OP-750 | Oceano Profundo 750ml | $18.000 |
| OP-1L | Oceano Profundo 1L | $22.000 |

## 2. Precios de venta iniciales (precio base)

| Codigo | Producto | Precio base |
|---|---|---:|
| SV-750 | Sangre de la Vid 750ml | $48.000 |
| SV-1L | Sangre de la Vid 1L | $55.000 |
| ED-750 | Elixir Dorado 750ml | $38.000 |
| ED-1L | Elixir Dorado 1L | $45.000 |
| SR-750 | Susurro Rosado 750ml | $35.000 |
| SR-1L | Susurro Rosado 1L | $42.000 |
| OP-750 | Oceano Profundo 750ml | $40.000 |
| OP-1L | Oceano Profundo 1L | $48.000 |

## 3. Lead time de compra: proveedor actual y proveedor externo

### 3.1. Operacion normal (sin disrupcion de proveedor)
- Referencias especiales (Sangre de la Vid y Susurro Rosado): 2 dias.
- Resto de referencias (Elixir Dorado y Oceano Profundo): 3 dias.
- Proveedor operativo: actual.

### 3.2. Con disrupcion 1 activa (retraso_proveedor)
- Proveedor actual:
  - Sangre de la Vid / Susurro Rosado: 4 dias.
  - Elixir Dorado / Oceano Profundo: 6 dias.
  - Restriccion operativa: solo recibe pedidos en dias pares.
- Proveedor externo:
  - Sangre de la Vid / Susurro Rosado: 2 dias.
  - Elixir Dorado / Oceano Profundo: 3 dias.
  - Costo adicional por unidad: +$5.000.
- Si en la disrupcion 1 se elige opcion B, la compra se mantiene con proveedor actual.

## 4. Cantidades de compra y minimos por producto

Regla de compra vigente por presentacion:
- Productos 750ml: multiples de 30 unidades.
- Productos 1L: multiples de 20 unidades.

Asociacion por referencia:
- SV-750, ED-750, SR-750, OP-750: minimo operativo 30 y en multiples de 30.
- SV-1L, ED-1L, SR-1L, OP-1L: minimo operativo 20 y en multiples de 20.

## 5. Lead time de entrega por region (logistica)

| Region | Dias de entrega/ciclo |
|---|---:|
| Andina | 2 |
| Caribe | 4 |
| Pacifica | 4 |
| Orinoquia | 5 |
| Amazonia | 6 |

## 6. Flota de vehiculos: cantidad, capacidad y costos

### 6.1. Flota propia
| Grupo | Cantidad de vehiculos | Capacidad por vehiculo | Costo por vehiculo |
|---|---:|---:|---:|
| 350 | 3 | 350 und | $700.000 |
| 400 | 8 | 400 und | $800.000 |
| 450 | 4 | 450 und | $900.000 |
| 500 | 4 | 500 und | $1.000.000 |

Total flota propia: 19 vehiculos.

### 6.2. Transporte externo
- Vehiculo externo: V_EXTERNO.
- Costo por unidad: $3.000.
- Modelo de cobro: variable por unidades transportadas.

## 7. Fechas de activacion de disrupciones

| Disrupcion | Key | Dia inicio | Dia fin |
|---|---|---:|---:|
| Retraso en Proveedor Estrategico | retraso_proveedor | 8 | 21 |
| Aumento Inesperado en la Demanda | aumento_demanda | 29 | 35 |
| Reduccion de Capacidad Logistica por Fallas en Flota | falla_flota | 43 | 56 |

## 8. Duracion de la simulacion

- Duracion configurada: 8 semanas.
- Equivalencia operativa: 56 dias.

## 9. Informacion adicional necesaria para operar la herramienta

### 9.1. Parametros iniciales de arranque
- Capital inicial por empresa: $50.000.000.
- Inventario inicial 750ml: 120 unidades.
- Inventario inicial 1L: 80 unidades.
- Dias de historico de demanda al iniciar: 30.

### 9.2. Costos operativos globales
- Costo de almacenamiento: $0,5 por unidad por dia.
- Costo por faltante (venta perdida): $10 por unidad.

### 9.2.1. Costo de mantenimiento de inventario (implementado por producto)
- Formula aplicada: Costo = I_promedio * v * r.
- Parametro de tasa de mantenimiento anual (r): 20%.
- Base de conversion diaria: 365 dias.
- Tasa diaria equivalente: r_d = 0,20 / 365.
- Aplicacion: se calcula por cada producto en cada empresa y luego se suma.
- Efecto financiero: el total diario se descuenta de capital_actual (penaliza capital).

### 9.3. Tarifa base de transporte por region (parametro complementario)
- Andina: $500 por unidad.
- Pacifica: $1.000 por unidad.
- Caribe: $1.000 por unidad.
- Orinoquia: $1.500 por unidad.
- Amazonia: $2.000 por unidad.

### 9.4. Reglas de disrupciones con impacto operativo directo
- Disrupcion 1 (retraso_proveedor):
  - Opcion A habilita proveedor externo con +$5.000 por unidad.
  - Opcion B mantiene proveedor actual y prioriza racionamiento.
- Disrupcion 2 (aumento_demanda):
  - Multiplicador de demanda segun opcion: A=1.30, B=1.15, C=sin efecto.
- Disrupcion 3 (falla_flota):
  - Durante la disrupcion, los vehiculos propios de capacidad 500 quedan fuera de operacion.
  - Transporte externo con costo unitario de $3.000 cuando aplica.

## 10. Fuentes tecnicas de referencia

- utils/parametros_iniciales.py
- routes/estudiante.py
- utils/logistica.py
- utils/catalogo_disrupciones.py
- config.py

---

Documento generado para consolidacion funcional y operativa del simulador.
