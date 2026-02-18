# 📝 Cambios en el Formulario de Registro

## Resumen de Modificaciones

Se ha actualizado el formulario de registro con los siguientes cambios:

---

## ✅ Campos Agregados

### 1. **Universidad**
- Opción predeterminada: "Universidad del Valle"
- Opción: "Otra universidad" (campo de texto libre)
- Campo obligatorio

### 2. **Sede**
- Opciones predeterminadas:
  - Palmira
  - Cali
  - Buga
  - Zarzal
  - Otra sede (campo de texto libre)
- Campo obligatorio

### 3. **Código de Estudiante**
- Formato: 9-10 dígitos numéricos
- Ejemplo: 202158314
- Campo obligatorio y único
- Validación: solo acepta números
- Se usa como base para generar el username

### 4. **Carrera**
- Opción predeterminada: "Ingeniería Industrial"
- Opción: "Otra carrera" (campo de texto libre)
- Campo obligatorio

---

## ❌ Campos Eliminados

### 1. **Rol** (Ventas, Planeación, Compras, Logística)
- **Motivo:** Se asignará después por el profesor/administrador
- Ahora el campo `rol` en la BD puede ser NULL

### 2. **Empresa**
- **Motivo:** Se asignará después por el profesor/administrador
- El campo `empresa_id` permanece NULL al crear la cuenta

---

## 🔄 Cambios en el Modelo de Datos

### Tabla `usuarios` - Nuevos campos:

```sql
universidad VARCHAR(200)       -- Nombre de la universidad
sede VARCHAR(100)              -- Sede o campus
codigo_estudiante VARCHAR(20)  -- Código único de estudiante (UNIQUE)
carrera VARCHAR(200)           -- Carrera o programa académico
```

### Tabla `usuarios` - Campos modificados:

```sql
rol VARCHAR(20) NULL          -- Ahora puede ser NULL (antes era NOT NULL)
empresa_id INTEGER NULL       -- Se mantiene NULL hasta asignación
```

---

## 🎨 Interfaz del Formulario

El formulario ahora está organizado en 3 secciones:

### **1. Información Personal**
- Nombre Completo
- Correo Institucional

### **2. Información Académica**
- Universidad (con opción "Otra")
- Sede (con opción "Otra")
- Código de Estudiante
- Carrera (con opción "Otra")

### **3. Seguridad**
- Contraseña
- Confirmar Contraseña

---

## 🔧 Funcionalidades JavaScript

1. **Campos condicionales:**
   - Si selecciona "Otra universidad/sede/carrera" → aparece campo de texto
   - Los campos de texto son requeridos solo cuando se selecciona "Otro"

2. **Validación de código:**
   - Solo permite números
   - Valida formato 9-10 dígitos

3. **Validación de contraseñas:**
   - Verifica que ambas contraseñas coincidan antes de enviar

---

## 📊 Flujo de Registro Actualizado

```
1. Usuario completa formulario
   └─ Información personal
   └─ Información académica (nuevos campos)
   └─ Contraseña

2. Sistema valida datos
   └─ Correo institucional válido
   └─ Código de estudiante único
   └─ Todos los campos completos

3. Se crea usuario con:
   ✅ username = codigo_estudiante (ej: 202158314)
   ✅ rol = NULL (sin asignar)
   ✅ empresa_id = NULL (sin asignar)
   ✅ universidad, sede, codigo, carrera

4. Se envía código de verificación

5. Usuario verifica correo

6. Profesor/Admin asigna:
   → Rol (Ventas, Planeación, Compras, Logística)
   → Empresa (1, 2, 3, etc.)
```

---

## 🎯 Validaciones Implementadas

✅ **Código de estudiante:**
- Único en la base de datos
- Solo números
- 9-10 dígitos

✅ **Universidad:**
- Obligatoria
- Si es "Otra", requiere texto

✅ **Sede:**
- Obligatoria
- Si es "Otra", requiere texto

✅ **Carrera:**
- Obligatoria
- Si es "Otra", requiere texto

✅ **Correo:**
- Institucional
- Único
- Formato válido

---

## 🔄 Migración de Base de Datos

Para aplicar los cambios:

```bash
python migrate_db.py
```

Esto agregará:
- Columna `universidad`
- Columna `sede`
- Columna `codigo_estudiante` (con índice UNIQUE)
- Columna `carrera`
- Hará que `rol` sea nullable

---

## 📝 Notas Importantes

1. **Usuarios existentes:**
   - Los usuarios de prueba piloto (estudiante_1_1, etc.) NO tienen estos campos
   - Funcionarán normalmente sin problema

2. **Usuarios nuevos:**
   - DEBEN completar todos los campos académicos
   - NO se les asigna rol ni empresa al registrarse
   - El profesor debe asignarlos después

3. **Username generado:**
   - Se usa el código de estudiante como username
   - Si ya existe, se agrega un sufijo: codigo_1, codigo_2, etc.

4. **Administración:**
   - El profesor debe tener una interfaz para:
     * Ver usuarios sin rol asignado
     * Asignar rol a cada usuario
     * Asignar empresa a cada usuario

---

## ✨ Estado Actual

- ✅ Modelo actualizado
- ✅ Formulario HTML actualizado
- ✅ Validaciones implementadas
- ✅ Lógica de registro actualizada
- ✅ Script de migración actualizado
- ✅ Campos condicionales funcionando

---

## 🚀 Próximos Pasos Sugeridos

1. **Crear interfaz de administración** para que el profesor:
   - Vea lista de usuarios registrados sin rol
   - Asigne rol y empresa a cada usuario
   - Apruebe o rechace registros

2. **Dashboard de usuarios sin asignar:**
   - Mostrar información académica
   - Botones de asignación rápida
   - Filtros por universidad/sede/carrera

3. **Notificaciones:**
   - Email al usuario cuando se le asigna rol y empresa
   - Instrucciones de inicio de sesión

---

## 📞 Ejemplo de Usuario Creado

```python
Usuario(
    username="202158314",
    nombre_completo="Juan Pérez García",
    email="juan.perez@correounivalle.edu.co",
    universidad="Universidad del Valle",
    sede="Palmira",
    codigo_estudiante="202158314",
    carrera="Ingeniería Industrial",
    rol=None,              # Se asigna después
    empresa_id=None,       # Se asigna después
    email_verified=True    # Después de verificar correo
)
```

---

**Fecha de implementación:** Enero 4, 2026
**Estado:** ✅ Completado y listo para usar
