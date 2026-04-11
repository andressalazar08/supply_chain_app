# 🔧 Guía Técnica: Verificación de Datos Iniciales para Administradores

**Versión:** 1.0  
**Dirigido a:** Administradores y Docentes Técnicos  
**Propósito:** Verificar que los datos iniciales sean correctos antes de procesar grupos

---

## 📋 1. Acceso a la Administración

### **1.1 Login como Admin**
```
URL: http://localhost:5000/
Usuario: admin
Contraseña: [Tu contraseña admin]
Tipo de usuario: profesor
```

### **1.2 Dashboard Principal**
Una vez logueado, accede a:
```
Profesor → Dashboard Principal
```

---

## 🎮 2. Crear/Verificar Nueva Simulación

### **2.1 Ruta en Interfaz Web**
```
Dashboard Profesor → Sección "Crear Nueva Simulación"
   → Modal "Configurar Nueva Simulación"
```

### **2.2 Campos a Configurar**

**Campo 1: Nombre de la Simulación**
```
Ubicación: Campo "Nombre de la Simulación (opcional)"
Tipo: Texto
Ejemplo: "Práctica Inicial - Grupo A"
Si está vacío: Se genera automáticamente como "Simulación N"
```

**Campo 2: Capital Inicial por Empresa**
```
Ubicación: Campo "Capital Inicial por Empresa"
Tipo: Número
Rango: $1,000,000 - Ilimitado
Valor recomendado: $50,000,000
Mínimo funcional: $20,000,000 (permite compras significativas)
```

**Campo 3: Inventario Inicial Productos 750ml**
```
Ubicación: Campo "Inventario inicial — Productos 750ml"
Tipo: Número entero
Rango: 0 - Ilimitado
Valor por defecto: 120 unidades
Rango recomendado: 80 - 200 unidades
```

**Campo 4: Inventario Inicial Productos 1L**
```
Ubicación: Campo "Inventario inicial — Productos 1L"
Tipo: Número entero
Rango: 0 - Ilimitado
Valor por defecto: 80 unidades
Rango recomendado: 50 - 150 unidades
```

### **2.3 Procesos al Crear Simulación**

Cuando haces clic en **"Crear Nueva Simulación"**, el sistema:

**Paso 1:** Desactiva la simulación anterior (si existe)
```sql
UPDATE simulacion SET activa = FALSE WHERE activa = TRUE;
```

**Paso 2:** Crea nueva simulación con parámetros
```sql
INSERT INTO simulacion (
  nombre, semana_actual, dia_actual, estado, 
  duracion_semanas, capital_inicial_empresas, activa
) VALUES (
  'Tu nombre', 1, 1, 'pausado', 30, tu_capital, TRUE
);
```

**Paso 3:** Vincula todas las empresas a la nueva simulación
```sql
UPDATE empresa SET simulacion_id = new_sim_id, 
  capital_inicial = tu_capital, capital_actual = tu_capital
WHERE profesor_id = tu_id AND activa = TRUE;
```

**Paso 4:** Resetea inventarios a valores iniciales
```sql
UPDATE inventario SET 
  cantidad_actual = inv_inicial,
  cantidad_reservada = 0,
  punto_reorden = calculo_automatico,
  stock_seguridad = calculo_automatico
WHERE empresa_id IN (...)
```

**Paso 5:** Calcula automáticamente demanda y parámetros (ver sección 3)

---

## 📊 3. Datos Calculados Automáticamente

### **3.1 Cálculo de Demanda Base**

Cuando se crea la simulación, el sistema calcula para cada producto:

```python
# Parámetros fijos
DIAS_COBERTURA = 5      # Stock durará 5 días
REGIONES = 5            # 5 regiones de distribución
DIAS_REORDEN = 3        # Punto reorden en 3 días
DIAS_SEGURIDAD = 1      # Stock seguridad de 1 día
FACTOR_DESVIACION = 0.20 # Variación ±20%

# Invocado desde reinicio_simulacion()
def calcular_parametros(inv_inicial, producto):
    
    # 1. Demanda promedio semanal POR REGIÓN
    demanda_promedio = max(1, round(
        inv_inicial * 7 / (DIAS_COBERTURA * REGIONES)
    ))
    
    # 2. Variación de demanda
    desviacion = max(1, round(demanda_promedio * FACTOR_DESVIACION))
    
    # 3. Consumo diario TOTAL (todas las regiones)
    consumo_diario = (demanda_promedio / 7.0) * REGIONES
    
    # 4. Punto de reorden
    punto_reorden = max(1, round(consumo_diario * DIAS_REORDEN))
    
    # 5. Stock de seguridad
    stock_seguridad = max(1, round(consumo_diario * DIAS_SEGURIDAD))
    
    # 6. Stock máximo
    stock_maximo = inv_inicial * 3
    
    return {
        'demanda_promedio': demanda_promedio,
        'desviacion': desviacion,
        'punto_reorden': punto_reorden,
        'stock_seguridad': stock_seguridad,
        'stock_maximo': stock_maximo,
        'consumo_diario': consumo_diario
    }
```

### **3.2 Ejemplo Concreto**

**Entrada:**
- `inv_750ml = 120` unidades

**Cálculos:**
```
demanda_promedio = 120 × 7 / (5 × 5) = 120 × 7 / 25 = 33.6 ≈ 34 / semana / región
desviacion = 34 × 0.20 = 6.8 ≈ 7
consumo_diario = (34 / 7) × 5 = 4.86 × 5 ≈ 24 / día
punto_reorden = 24 × 3 = 72
stock_seguridad = 24 × 1 = 24
stock_maximo = 120 × 3 = 360
```

**Resultado en BD:**
```
Producto 'Vino 750ml':
  demanda_promedio: 34
  desviacion_demanda: 7
  stock_maximo: 360

Inventario de Empresa X (Producto 750ml):
  cantidad_actual: 120
  punto_reorden: 72
  stock_seguridad: 24
```

---

## 🗄️ 4. Verificar Datos en la Base de Datos

### **4.1 Acceso Direct a SQLite**

**Opción 1: Desde Terminal Python**
```bash
# Activar entorno virtual
venv\Scripts\activate

# Abrir consola Python
python

# En la consola:
from app import app
from models import Simulacion, Empresa, Inventario, Producto
from extensions import db

with app.app_context():
    # Ver simulación activa
    sim = Simulacion.query.filter_by(activa=True).first()
    if sim:
        print(f"Simulación: {sim.nombre}")
        print(f"Capital: ${sim.capital_inicial_empresas:,.0f}")
        print(f"Día: {sim.dia_actual}, Semana: {sim.semana_actual}")
        print(f"Estado: {sim.estado}")
```

**Opción 2: Usando DB Browser for SQLite**
```
1. Descarga: https://sqlitebrowser.org/
2. Abre: supply_chain.db
3. Navega a tabla: simulacion, empresa, inventario
```

### **4.2 Queries SQL Útiles**

**Verificar Simulación Activa:**
```sql
SELECT id, nombre, capital_inicial_empresas, duracion_semanas, estado
FROM simulacion
WHERE activa = TRUE;
```

**Ver Todas las Empresas y su Capital:**
```sql
SELECT e.id, e.nombre, e.capital_inicial, e.capital_actual, s.nombre as simulacion
FROM empresa e
LEFT JOIN simulacion s ON e.simulacion_id = s.id
WHERE e.profesor_id = [TU_PROFESOR_ID]
ORDER BY e.nombre;
```

**Ver Inventarios Iniciales (Empresa X):**
```sql
SELECT i.id, p.nombre, i.cantidad_actual, i.punto_reorden, 
       i.stock_seguridad, p.demanda_promedio, p.desviacion_demanda
FROM inventario i
JOIN producto p ON i.producto_id = p.id
WHERE i.empresa_id = [EMPRESA_ID]
ORDER BY p.nombre;
```

**Ver Parámetros de Productos:**
```sql
SELECT id, codigo, nombre, precio_base, costo_unitario, 
       demanda_promedio, desviacion_demanda, stock_maximo
FROM producto
WHERE activo = TRUE
ORDER BY nombre;
```

**Contar Empresas sin Asignar:**
```sql
SELECT COUNT(*) as sin_simulacion
FROM empresa
WHERE simulacion_id IS NULL;
```

---

## ✅ 5. Checklist de Validación Técnica

### **5.1 Antes de Iniciar la Simulación**

- [ ] **Simulación Activa Existe**
  ```python
  sim = Simulacion.query.filter_by(activa=True).first()
  assert sim is not None, "No hay simulación activa"
  ```

- [ ] **Capital Configurado Correctamente**
  ```python
  assert sim.capital_inicial_empresas >= 1000000, "Capital muy bajo"
  print(f"✓ Capital: ${sim.capital_inicial_empresas:,.0f}")
  ```

- [ ] **Empresas Vinculadas**
  ```python
  empresas = Empresa.query.filter_by(simulacion_id=sim.id).all()
  assert len(empresas) > 0, "No hay empresas asignadas"
  print(f"✓ Empresas: {len(empresas)}")
  ```

- [ ] **Inventarios Inicializados**
  ```python
  for emp in empresas:
      invs = Inventario.query.filter_by(empresa_id=emp.id).all()
      assert len(invs) == 2, f"Empresa {emp.nombre} falta inventario"
      for inv in invs:
          assert inv.cantidad_actual > 0, "Stock en cero"
      print(f"✓ {emp.nombre}: Inventarios OK")
  ```

- [ ] **Demanda Calculada**
  ```python
  productos = Producto.query.filter_by(activo=True).all()
  for prod in productos:
      assert prod.demanda_promedio > 0, f"{prod.nombre} sin demanda"
      assert prod.desviacion_demanda > 0, f"{prod.nombre} sin desviación"
  print(f"✓ Productos: Demanda OK")
  ```

- [ ] **Simulación en Estado Correcto**
  ```python
  assert sim.estado == 'pausado', "Simulación debe estar pausada"
  assert sim.dia_actual == 1, "Debe empezar en día 1"
  print(f"✓ Estado: {sim.estado}, Día: {sim.dia_actual}")
  ```

### **5.2 Validación Completa (Script)**

```python
#!/usr/bin/env python
"""
Script de validación de datos iniciales
Ejecutar: python validar_datos_iniciales.py
"""

from app import app
from models import Simulacion, Empresa, Inventario, Producto, Usuario
from extensions import db

def validar_datos_iniciales(profesor_id=None):
    with app.app_context():
        print("\n" + "="*60)
        print("VALIDACIÓN DE DATOS INICIALES")
        print("="*60 + "\n")
        
        # 1. Simulación activa
        sim = Simulacion.query.filter_by(activa=True).first()
        if not sim:
            print("❌ ERROR: No hay simulación activa")
            return False
        
        print(f"✓ Simulación: {sim.nombre}")
        print(f"  - Capital inicial: ${sim.capital_inicial_empresas:,.0f}")
        print(f"  - Duración: {sim.duracion_semanas} semanas")
        print(f"  - Estado: {sim.estado}")
        print(f"  - Día: {sim.dia_actual}")
        
        # 2. Empresas vinculadas
        empresas = Empresa.query.filter_by(simulacion_id=sim.id).all()
        if not empresas:
            print("❌ ERROR: No hay empresas asignadas a la simulación")
            return False
        
        print(f"\n✓ Empresas: {len(empresas)}")
        
        # 3. Validar cada empresa
        for i, emp in enumerate(empresas, 1):
            print(f"\n  [{i}] {emp.nombre}")
            print(f"      Capital: ${emp.capital_inicial:,.0f}")
            
            # Inventarios
            invs = Inventario.query.filter_by(empresa_id=emp.id).all()
            if len(invs) != 2:
                print(f"      ❌ Inventarios incompletos: {len(invs)}/2")
                return False
            
            for inv in invs:
                print(f"      - {inv.producto.nombre}: {inv.cantidad_actual:.0f} und")
                print(f"        (Punto reorden: {inv.punto_reorden}, "
                      f"Stock seg: {inv.stock_seguridad})")
            
            # Estudiantes asignados
            estudiantes = Usuario.query.filter_by(empresa_id=emp.id).all()
            print(f"      Estudiantes: {len(estudiantes)}")
        
        # 4. Productos
        productos = Producto.query.filter_by(activo=True).all()
        print(f"\n✓ Productos Disponibles: {len(productos)}")
        for prod in productos:
            print(f"  - {prod.nombre} (${prod.costo_unitario:,.0f} costo)")
            print(f"    Demanda promedio: {prod.demanda_promedio:.0f} ± {prod.desviacion_demanda:.0f}")
        
        print("\n" + "="*60)
        print("✅ VALIDACIÓN OK - Sistema listo para iniciar")
        print("="*60 + "\n")
        return True

if __name__ == '__main__':
    validar_datos_iniciales()
```

---

## 🔄 6. Ajustar Datos Después de Crear Simulación

### **6.1 Cambiar Capital de una Empresa**

**Vía Web:**
```
Profesor → Gestionar Empresas → Click en empresa → Editar Capital Actual
```

**Vía Base de Datos:**
```python
from app import app
from models import Empresa
from extensions import db

with app.app_context():
    emp = Empresa.query.filter_by(nombre="Mi Empresa").first()
    emp.capital_actual = 75000000
    emp.capital_inicial = 75000000
    db.session.commit()
    print("✓ Capital actualizado")
```

### **6.2 Cambiar Inventario Existente**

**Vía Base de Datos:**
```python
from app import app
from models import Inventario, Producto, Empresa
from extensions import db

with app.app_context():
    emp = Empresa.query.filter_by(nombre="Mi Empresa").first()
    prod = Producto.query.filter_by(nombre__contains="750ml").first()
    inv = Inventario.query.filter_by(
        empresa_id=emp.id, producto_id=prod.id
    ).first()
    
    inv.cantidad_actual = 200  # New stock
    db.session.commit()
    print("✓ Inventario actualizado")
```

### **6.3 Recalibrar Demanda**

Si necesitas ajustar la demanda sin reiniciar:

```bash
# Ejecutar script de calibración
python calibrar_demanda.py 150 100
# (inv_750ml=150, inv_1L=100)
```

---

## 📈 7. Monitoreo Durante Simulación

### **7.1 Ver Estado Actual**

```python
from app import app
from models import Simulacion, Empresa, Metrica
from extensions import db

with app.app_context():
    sim = Simulacion.query.filter_by(activa=True).first()
    print(f"Día: {sim.dia_actual}, Semana: {sim.semana_actual}")
    
    for emp in sim.empresas:
        # Última métrica disponible
        metrica = Metrica.query.filter_by(
            empresa_id=emp.id
        ).order_by(Metrica.semana_simulacion.desc()).first()
        
        if metrica:
            print(f"\n{emp.nombre}:")
            print(f"  Capital: ${emp.capital_actual:,.0f}")
            print(f"  Ingresos: ${metrica.ingresos:,.0f}")
            print(f"  Utilidad: ${metrica.utilidad:,.0f}")
            print(f"  Nivel Servicio: {metrica.nivel_servicio:.1f}%")
```

---

## 🐛 8. Troubleshooting

### **Problema: Capital no se actualiza**
```
Solución: Reinicia la simulación. El capital se copia al crear simulación.
```

### **Problema: Inventario muestra cero**
```
Solución: Verifica que se haya creado la simulación y ejecutado correctamente.
Query: SELECT COUNT(*) FROM inventario WHERE cantidad_actual = 0;
```

### **Problema: Estudiantes no ven sus empresas**
```
Solución: Verifica asignación:
SELECT u.username, u.empresa_id, e.nombre FROM usuario u
LEFT JOIN empresa e ON u.empresa_id = e.id
WHERE u.tipo_usuario = 'estudiante';
```

### **Problema: Demanda no se calcula**
```
Solución: Ejecuta manualmente:
python calibrar_demanda.py [inv_750ml] [inv_1l]
```

---

## 📚 Referencias Técnicas

- **Archivo de reinicio:** `utils/reinicio_simulacion.py`
- **Archivo de calibración:** `calibrar_demanda.py`
- **Modelos de datos:** `models.py`
- **Rutas administrador:** `routes/profesor.py`

---

**Última actualización:** 11 de abril de 2026  
**Versión técnica:** 1.0
