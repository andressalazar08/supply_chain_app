# 📋 RESUMEN EJECUTIVO: Datos Iniciales del Simulador de Cadena de Abastecimiento

**Fecha:** Abril 11, 2026  
**Dirigido a:** Docentes y Administradores  
**Pregunta Central:** ¿Todas las empresas empiezan con las mismas condiciones?

---

## ✅ RESPUESTA DIRECTA

### **¿Todas las empresas empiezan igual?**

**SÍ - A EXCEPCIÓN DEL CAPITAL (que el admin puede ajustar)**

```
╔════════════════════════════════════════════════════════════════╗
║                    DATOS INICIALES IDÉNTICOS                  ║
║                                                                ║
║  ✓ Inventario Inicial (mismas unidades por tipo de producto)  ║
║  ✓ Costo Unitario de Productos                               ║
║  ✓ Precio Base de Productos                                  ║
║  ✓ Demanda del Mercado (misma distribución probabilística)   ║
║  ✓ Parámetros de Inventario (punto reorden, stock seguridad) ║
║  ✓ Tiempos de Entrega                                        ║
║  ✓ Costos Operativos                                         ║
║  ✓ Duración de Simulación                                    ║
║                                                                ║
║                      DATO VARIABLE                            ║
║                                                                ║
║  ⚠️ CAPITAL INICIAL (El admin puede asignar diferente a cada ║
║     empresa, o mantener igual para todas)                   ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 🎯 Datos Iniciales Configurables (Un Líder Control)

Cada vez que el admin crea una **Nueva Simulación**, debe establecer:

| Parámetro | Ejemplo | Nota |
|-----------|---------|------|
| **Capital Inicial por Empresa** | $50,000,000 | Se aplica a TODAS auto |
| **Inventario 750ml** | 120 unidades | Se aplica a TODAS |
| **Inventario 1L** | 80 unidades | Se aplica a TODAS |

**La configuración es:** ***Un valor → Se replica en TODAS las empresas***

---

## 🔒 Datos Iniciales Fijos (No Configurables)

Estos datos están "cableados" en el sistema y no se pueden cambiar sin código:

| Aspecto | Valor |
|--------|-------|
| **Número de Productos** | 2 tipos (vinos 750ml y 1L) |
| **Regiones de Mercado** | 5 (Andina, Caribe, Pacífica, Orinoquia, Amazonia) |
| **Duración Simulación** | 30 semanas (≈90 días) |
| **Estructura de Roles** | 3 (Ventas, Compras, Logística) |
| **Costo Almacenamiento** | $0.50/unidad/día |
| **Costo Faltante** | $10.00/unidad no vendida |
| **Volatilidad Demanda** | ±20% variación |
| **Lead Time Proveedor** | 1 día |

---

## 📊 Lo que Cada Empresa VE en el Día 1

Cuando accede por primera vez, cada estudiante ve:

```
╔═══════════════════════════════════════════════════════════════════╗
║                    VISTA INICIAL ESTUDIANTE                      ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  CAPITAL DISPONIBLE                                              ║
║  ├─ Inicial: $50,000,000 (ej.)                                   ║
║  ├─ En Inventario: $2,160,000 (120 × $18,000 costo 750ml)       ║
║  └─ Libre para Compras: $47,840,000                              ║
║                                                                   ║
║  INVENTARIO A MANO                                               ║
║  ├─ Vino 750ml: 120 unidades @ $18,000 = $2,160,000             ║
║  └─ Vino 1L: 80 unidades @ $21,000 = $1,680,000                 ║
║                                                                   ║
║  PRECIOS INICIALES                                               ║
║  ├─ Vino 750ml precio de venta: $45,000 (puede cambiar)         ║
║  └─ Vino 1L precio de venta: $60,000 (puede cambiar)             ║
║                                                                   ║
║  NIVEL DE SERVICIO INICIAL                                       ║
║  └─ Día 1: Depende de la demanda aleatoria (50-100%)            ║
║                                                                   ║
║  COMPETENCIA                                                     ║
║  └─ Todas las empresas activas compiten por clientes            ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 🎲 ¿Hay Ventaja Competitiva Inicial?

**NO.** Todas parten con las mismas oportunidades.

### Factores que SÍ afectan resultados:

- **Decisiones de Ventas:** Qué precio fijan
- **Decisiones de Compras:** Cuándo y cuánto ordenan
- **Decisiones de Compras:** Cuándo, cuánto y con qué proveedor ordenan
- **Decisiones de Logística:** Cómo distribuyen por regiones y reciben pedidos

### Factores que NO varían:

- Inventario inicial (igual para todos)
- Demanda disponible (igual para todos)
- Costos de operación (igual para todos)
- Infraestructura (igual para todos)

**→ Ganador será quien tome MEJORES DECISIONES**

---

## 🛠️ Flujo de Configuración Paso a Paso

### Paso 1: Admin Accede A Dashboard
```
Profesor → Button "Crear Nueva Simulación"
```

### Paso 2: Ingresa Parámetros
```
┌─────────────────────────────────┐
│ Nombre Simulación: [opcional]   │
│ Capital Inicial: $50,000,000 ✓  │
│ Inv. 750ml: 120 unidades ✓      │
│ Inv. 1L: 80 unidades ✓          │
└─────────────────────────────────┘
```

### Paso 3: Sistema Auto-Replica
```
Empresa 1: Capital = $50M, Inv = 120/80
Empresa 2: Capital = $50M, Inv = 120/80
Empresa 3: Capital = $50M, Inv = 120/80
...
```

### Paso 4: Estudiantes Ven Datos
```
Tu empresa inicia con:
- Capital: $50,000,000
- Vino 750ml: 120 unidades
- Vino 1L: 80 unidades
```

---

## 💡 ¿Qué Significa Esto Para Tu Grupo?

### Ventaja: 
✅ **Entorno justo:** Nadie tiene ventaja injusta  
✅ **Enfoque en decisiones:** Los resultados reflejan estrategia  
✅ **Comparable:** Puedes evaluar el desempeño relativamente  

### Desventaja:
⚠️ **Muy competitivo:** No hay "cliente cautivo"  
⚠️ **Presión inicial:** Stock inicial dura ~5 días solamente  
⚠️ **SIN margen de error:** Si no compran a tiempo, pierden ventas  

---

## 📌 Datos por Tipo de Inicio

### **Escenario A: Capital Igual Para Todos (Recomendado)**

```
> Capital: $50,000,000 (todos iguales)

VENTAJA:
- Máxima equidad
- Foco en decisiones operacionales
- Mejor para evaluar competencia pura

DESAFÍO:
- Sin "rescate" si cometen errores
- Presiona la gestión de cash flow
```

### **Escenario B: Capital Diferenciado (Opcional)**

```
Empresa A: $80,000,000
Empresa B: $50,000,000
Empresa C: $30,000,000

VENTAJA:
- Simula realidades económicas diferentes
- Estudian adaptación a restricción

DESAFÍO:
- No es completamente justo
- Requiere explicación clara
```

---

## 🔍 Verificación Rápida: ¿Están Bien Los Datos?

**Usa este checklist ANTES de que los estudiantes vean los datos:**

### ✓ Checklist Pre-Simulación

- [ ] ¿Simulación activa existe?  
  ```
  Profesor → Dashboard → ¿Ves estado "En Curso" o "Pausado"?
  ```

- [ ] ¿Capital está configurado?  
  ```
  Profesor → Gestionar Empresas → ¿Ves Capital $XXM en cada empresa?
  ```

- [ ] ¿Inventario inicial está presente?  
  ```
  Estudiante → Logística → ¿Ves 120 und de 750ml y 80 und de 1L?
  ```

- [ ] ¿Precios están correctos?  
  ```
  Estudiante → Ventas → ¿Ves precio base sin cambios?
  ```

- [ ] ¿Requerimientos y pedidos se muestran?  
  ```
  Estudiante → Compras → ¿Ves requerimientos, proveedor y opciones de pedido?
  ```

---

## 📚 Documentación Completa

Se han generado dos documentos adicionales:

**1. `MANUAL_DATOS_INICIALES.md`**
- Guía completa para docentes y estudiantes
- Explica qué ve cada rol
- Parámetros técnicos en detalle
- FAQ (Preguntas Frecuentes)

**2. `GUIA_TECNICA_DATOS_INICIALES.md`**
- Para administradores técnicos
- Cómo verificar en BD
- Cómo ajustar datos después
- Scripts de validación

---

## 🎓 Para Los Estudiantes: ¿Qué Explicarles?

### **Línea de Comunicación Recomendada:**

> *"Todas las empresas comienzan con exactamente los mismos recursos:*
>
> - *120 botellas de vino 750ml*
> - *80 botellas de vino 1L*  
> - *$50 millones de capital inicial*
> - *Acceso al mismo mercado (5 regiones)*
>
> *La diferencia en resultados será 100% por las decisiones que tomen en:*
> - *¿A qué precio venden?*
> - *¿Cuándo compran más inventario?*
> - *¿Cómo distribuyen por regiones?*
> - *¿Cómo pronostican la demanda?*
>
> *Es un juego completamente justo. Ganará quien gestione mejor su cadena de abastecimiento."*

---

## ❓ Preguntas Finales Respondidas

### P: ¿Puedo dar a una empresa más capital inicial que otra?
**R:** Sí, pero solo **ANTES** de empezar. Una vez que se crea la simulación, todas las empresas ya tienen asignado el mismo capital. Si necesitas después, edita empresa por empresa.

### P: ¿Qué pasa si un equipo compra menos al inicio?
**R:** Su stock se agota más rápido, pierden ventas, baja nivel de servicio. DEBEN reaccionar comprando más en próximas semanas.

### P: ¿El mercado sabe si una empresa está en quiebre de stock?
**R:** Sí. Otros clientes compran en otras empresas. El competidor que NO tiene stock PIERDE esa venta.

### P: ¿Se puede paralizar una empresa sin capital?
**R:** Teóricamente sí, pero es muy difícil. Con $50M y costos razonables, se pueden hacer varias rondas de compra.

### P: ¿Es realista que todas comiencen igual?
**R:** En educación SÍ (para medir aprendizaje). En realidad NO (cada empresa tiene historia). Úsalo como punto de control.

---

## 📞 Resumen de Archivos Generados

| Archivo | Propósito | Público |
|---------|-----------|---------|
| `MANUAL_DATOS_INICIALES.md` | Guía completa de datos | Docentes + Estudiantes avanzados |
| `GUIA_TECNICA_DATOS_INICIALES.md` | Verificación técnica | Solo Administradores |
| `RESUMEN_EJECUTIVO.txt` (este) | Respuesta rápida | Todos |

---

## ✨ Conclusión

**Todas las empresas empiezan con EXACTAMENTE los mismos datos iniciales, excepto el capital (que puede ser igual o diferente según lo configure el admin).**

Esto crea un **entorno competitivo justo** donde los resultados dependen 100% de las **decisiones de los estudiantes**.

Úsalo así:
- ✅ Para evaluar habilidades de gestión
- ✅ Para entender cadena de abastecimiento
- ✅ Para trabajar en equipo multidisciplinario

---

**¿Necesitas más detalles?** Consulta:
- `MANUAL_DATOS_INICIALES.md` para información completa
- `GUIA_TECNICA_DATOS_INICIALES.md` para verificación técnica

**Versión:** 1.0  
**Fecha:** Abril 11, 2026
