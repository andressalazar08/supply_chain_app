# Reporte de funcionamiento del simulador

## 1. Descripción general

El simulador es una herramienta web creada para representar el funcionamiento de una empresa dentro de una cadena de abastecimiento. Su objetivo es que los usuarios puedan tomar decisiones como si estuvieran administrando una empresa real, observando después qué efectos tienen esas decisiones sobre las ventas, el inventario, los costos y la rentabilidad.

La aplicación está pensada como un entorno de aprendizaje y práctica. Cada usuario ve una parte del proceso según su rol, por ejemplo ventas, compras, logística o administración. De esta manera, la herramienta permite trabajar de forma organizada y simular la interacción entre distintas áreas de una empresa.

## 2. ¿Para qué sirve?

La herramienta sirve para:

- Practicar la toma de decisiones empresariales en un entorno simulado.
- Entender cómo cambian las ventas cuando varían los precios o el stock.
- Evaluar el efecto de las compras y la logística sobre el inventario.
- Medir el desempeño de cada empresa mediante indicadores como ingresos, utilidad y nivel de servicio.
- Permitir que varios usuarios participen en la misma simulación y vean cómo sus decisiones afectan al resto del equipo.

En resumen, el simulador ayuda a aprender haciendo, mostrando consecuencias reales dentro del sistema sin necesidad de operar una empresa real.

## 3. Propósito de la herramienta

El propósito principal es educativo. La aplicación busca que los usuarios comprendan cómo funciona una cadena de abastecimiento y cómo se relacionan entre sí las decisiones de diferentes áreas.

También cumple un propósito de seguimiento y evaluación, porque deja registro de lo que hace cada usuario. Eso permite revisar después qué decisiones se tomaron, cómo impactaron el inventario y qué resultados produjo cada acción.

## 4. Funcionamiento general explicado de forma sencilla

La aplicación funciona como un ciclo continuo de simulación.

Primero, el profesor o administrador inicia una simulación. Cuando la simulación está activa, los estudiantes pueden entrar con su usuario y trabajar en su módulo correspondiente.

Después, cada rol realiza acciones específicas:

- El área de ventas ajusta precios y analiza el comportamiento del mercado.
- Compras define requerimientos, selecciona proveedor y crea órdenes para abastecer la empresa.
- Logística gestiona recepciones, despachos y movimientos de inventario.

Cada vez que un usuario toma una decisión, la aplicación la guarda y la asocia a su empresa. Más adelante, cuando otro usuario entra al sistema, puede ver los cambios generados por esas decisiones.

El simulador también avanza por días de simulación. En cada avance se procesan ventas, compras que llegan, despachos, costos operativos y métricas. Así el sistema va actualizando automáticamente el estado de cada empresa.

## 5. ¿Cómo se guardan los datos?

La aplicación guarda la información en una base de datos local. Eso significa que los datos no se pierden cuando un usuario cierra sesión o cambia de pantalla.

Allí se almacenan, entre otros:

- Los usuarios y sus roles.
- Las empresas creadas dentro de la simulación.
- Las decisiones tomadas por cada usuario.
- Las ventas registradas por producto y por región.
- Las compras y sus estados.
- El inventario disponible.
- Las métricas de desempeño.
- Los pronósticos y requerimientos generados.

Gracias a esto, la información persiste y puede ser consultada después por otros usuarios autorizados.

## 6. Qué sucede cuando avanza la simulación

Cada avance de la simulación representa un nuevo día de operación. En ese proceso el sistema:

1. Genera o actualiza ventas según la demanda y el precio.
2. Registra las ventas perdidas cuando no hay suficiente inventario.
3. Recibe compras que estaban en tránsito.
4. Actualiza el inventario disponible.
5. Calcula costos operativos.
6. Registra métricas como ingresos, utilidad y nivel de servicio.
7. Revisa alertas de inventario y posibles disrupciones.

Esto permite que el simulador refleje una operación dinámica, donde cada decisión afecta el siguiente resultado.

## 7. Relación entre usuarios

La aplicación está diseñada para que varios usuarios trabajen sobre una misma empresa o simulación. Por eso, cuando un usuario realiza una acción, los demás pueden ver sus efectos al consultar sus paneles.

Por ejemplo:

- Si ventas cambia el precio, eso puede afectar la demanda.
- Si compras no realiza pedidos a tiempo, el inventario puede bajar.
- Si logística no responde a tiempo, pueden aparecer demoras o faltantes.
- Si compras calcula mal el requerimiento o elige un proveedor inadecuado, la empresa puede comprar de más o de menos.

De esta forma, el simulador muestra que las decisiones de una área influyen en todas las demás.

## 8. Conclusión

El simulador es una herramienta de aprendizaje interactiva que permite experimentar el funcionamiento de una empresa de forma controlada. Su valor está en que integra varias áreas, guarda los resultados de las acciones y muestra de manera clara cómo una decisión en un módulo afecta a toda la operación.

En términos simples, sirve para aprender a administrar una cadena de abastecimiento viendo resultados concretos dentro de la misma aplicación.
