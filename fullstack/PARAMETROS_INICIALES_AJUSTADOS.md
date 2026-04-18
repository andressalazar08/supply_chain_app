# Parametros Iniciales Ajustados

Fecha de ajuste: 2026-04-18

Este documento consolida los parametros iniciales que quedaron ajustados para que el arranque de la simulacion sea coherente entre capital, inventario, precios, costos, demanda y pedidos de abastecimiento de los primeros 3 dias.

Base principal de demanda configurada: data/demanda_base_principal.csv

## 1. Parametros canónicos del arranque

Fuente de verdad: utils/parametros_iniciales.py

| Parametro | Valor ajustado | Uso operativo |
|---|---:|---|
| Duracion de simulacion | 8 semanas (56 dias) | Horizonte de juego |
| Historico de demanda | 30 dias | Base historica para analitica |
| Capital inicial por empresa | $50,000,000 | Caja inicial por equipo |
| Inventario inicial 750 ml | 120 und por producto | Stock inicial de referencias 750 |
| Inventario inicial 1L | 80 und por producto | Stock inicial de referencias 1L |
| Dias de cobertura inicial objetivo | 5 dias | Calibracion de demanda e inventario |
| Punto de reorden | 3 dias de consumo | Señal de abastecimiento |
| Stock de seguridad | 1 dia de consumo | Colchon de riesgo |
| Factor de desviacion demanda | 20% | Variabilidad base |
| Stock maximo por producto | 1500 und | Tope operativo |
| Dias de llegada pedidos iniciales | Dia 1, 2 y 3 | Arranque sin penalizacion por inactividad inicial |
| Cobertura pedidos iniciales | 2.5 dias | Cantidad total en transito inicial |
| Tope pedidos iniciales | 1600 und | Control de sobrecarga inicial |

## 2. Catalogo economico base (precios y costos)

Estos valores se aplican al reiniciar simulacion para mantener coherencia economica de arranque.

| Codigo | Producto | Precio base | Costo unitario | Margen bruto aprox. |
|---|---|---:|---:|---:|
| SV-750 | Sangre de la Vid 750ml | $48,000 | $20,000 | 58.3% |
| SV-1L | Sangre de la Vid 1L | $55,000 | $25,000 | 54.5% |
| ED-750 | Elixir Dorado 750ml | $38,000 | $17,000 | 55.3% |
| ED-1L | Elixir Dorado 1L | $45,000 | $20,000 | 55.6% |
| SR-750 | Susurro Rosado 750ml | $35,000 | $15,000 | 57.1% |
| SR-1L | Susurro Rosado 1L | $42,000 | $18,000 | 57.1% |
| OP-750 | Oceano Profundo 750ml | $40,000 | $18,000 | 55.0% |
| OP-1L | Oceano Profundo 1L | $48,000 | $22,000 | 54.2% |

## 3. Formulas de calibracion (inventario-demanda)

Se mantiene una logica unica en reinicio y calibracion para evitar desalineaciones.

- Demanda promedio semanal por region:

  demanda_promedio = round((inv_inicial * 7) / (dias_cobertura * regiones))

- Desviacion de demanda:

  desviacion = round(demanda_promedio * 0.20)

- Consumo diario esperado por empresa (todas las regiones):

  consumo_diario_empresa = (demanda_promedio / 7) * 5

- Punto de reorden:

  punto_reorden = round(consumo_diario_empresa * 3)

- Stock de seguridad:

  stock_seguridad = round(consumo_diario_empresa * 1)

## 4. Generacion de demanda diaria de mercado (BD central)

Ajuste aplicado: la demanda central usa primero la base principal CSV y filtra exactamente el rango operativo del juego.

- Rango obligatorio aplicado por simulacion:

  historico = dias -30 a -1

  operativo = dias 1 a 56

- Si el CSV no existe o no cubre todas las combinaciones dia/producto/region requeridas,
  el sistema activa un fallback sintetico para no bloquear la simulacion.

- El CSV principal actual contiene cobertura superior (hasta dia 210), pero el sistema usa
  solo el tramo necesario para el juego de 56 dias.

Como fallback controlado, la demanda diaria de mercado sintetica se construye desde la demanda_promedio del producto y el numero de empresas activas.

- Base diaria de mercado por producto:

  demanda_diaria_mercado = (demanda_promedio / 7) * 5 * empresas_activas

- Esa demanda se distribuye por pesos regionales (Andina, Caribe, Pacifica, Orinoquia, Amazonia), con estacionalidad semanal, tendencia suave y variabilidad controlada.

Resultado esperado: la escala de demanda central queda alineada con inventario inicial y capacidad de reposicion.

## 5. Pedidos de abastecimiento de arranque (Dias 1-3)

Ajuste aplicado en utils/historico_simulacion.py:

- Se generan pedidos en transito con llegada en dias 1, 2 y 3.
- Cantidad diaria fija objetivo por producto (por empresa y por dia):

  SV-1L: 213

  SV-750: 208

  ED-750: 212

  ED-1L: 195

  SR-750: 184

  SR-1L: 193

  OP-750: 204

  OP-1L: 190

- Total diario objetivo: 1599 und (capacidad máxima 1600).
- Si en el futuro el perfil supera la capacidad, se ajusta por factor proporcional.

Resultado esperado: los primeros dias no castigan al equipo por la inactividad previa al uso de la plataforma.

## 6. Archivos impactados por el ajuste

- utils/parametros_iniciales.py
- utils/reinicio_simulacion.py
- utils/demanda_central.py
- utils/historico_simulacion.py
- calibrar_demanda.py
- routes/profesor.py
- templates/profesor/dashboard.html
- config.py
- models.py
- generar_base_demanda.py
- data/demanda_base_principal.csv

## 7. Recomendacion operativa para aplicar en curso activo

Si se requiere que una simulacion ya creada adopte estos parametros de forma integral, ejecutar un reinicio desde el panel del profesor con los valores por defecto o con los valores deseados.

Con ese reinicio se recalculan inventarios, demanda, precios base/costos, historico y pedidos iniciales de dias 1-3 bajo el esquema ajustado.
