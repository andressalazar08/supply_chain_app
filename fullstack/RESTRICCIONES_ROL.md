# Sistema de Restricciones de Rol Implementado

## Cambios Realizados

### 1. Decorador de Restricción de Roles
Se creó un nuevo decorador `@rol_required()` en [routes/estudiante.py](routes/estudiante.py) que:

- Verifica que el usuario esté autenticado
- Valida que tenga empresa y rol asignados
- Comprueba que su rol esté en la lista de roles permitidos
- Redirige al dashboard general si no tiene permiso
- Muestra mensaje claro de error indicando el rol requerido

**Ejemplo de uso:**
```python
@bp.route('/ventas')
@login_required
@rol_required('ventas', 'admin')
def dashboard_ventas():
    # Solo accesible para roles: ventas y admin
    ...
```

### 2. Restricciones Aplicadas por Módulo

#### Módulo de Ventas
- **Roles permitidos:** `ventas`, `admin`
- **Rutas protegidas:**
  - `/ventas` - Dashboard de ventas
  - `/ventas/analisis-regional` - Análisis por región
  - `/api/ventas/*` - Todas las APIs de ventas
  
- **Excepciones:**
  - `/ventas/ajustar-precio` - Solo `admin` (cambio de precios)

#### Módulo de Compras
- **Roles permitidos:** `compras`, `admin`
- **Rutas protegidas:**
  - `/compras` - Dashboard de compras
  - `/compras/crear-orden-manual` - Crear órdenes
  - `/compras/crear-orden-desde-requerimiento` - Procesar requerimientos
  - `/compras/requerimientos` - Ver requerimientos
  - `/api/compras/*` - Todas las APIs de compras

#### Módulo de Logística
- **Roles permitidos:** `logistica`, `admin`
- **Rutas protegidas:**
  - `/logistica` - Dashboard de logística
  - `/logistica/recepcion` - Recepción de compras
  - `/logistica/despacho` - Crear despachos regionales
  - `/logistica/movimientos` - Movimientos de inventario
  - `/logistica/crear-despacho` - Ejecutar despachos
  - `/logistica/actualizar-inventario` - Ajustes de stock
  - `/api/logistica/*` - Todas las APIs de logística

#### Módulo de Planeación
- **Roles permitidos:** `planeacion`, `admin`
- **Rutas protegidas:**
  - `/planeacion` - Dashboard de planeación
  - `/planeacion/generar-pronostico` - Generar pronósticos
  - `/planeacion/guardar-pronostico` - Guardar pronósticos
  - `/planeacion/requerimientos` - Ver requerimientos
  - `/planeacion/crear-requerimiento` - Crear requerimientos
  - `/api/planeacion/*` - Todas las APIs de planeación

### 3. Restricciones Visuales en Templates

#### Sidebar ([templates/estudiante/_sidebar.html](templates/estudiante/_sidebar.html))
Solo muestra las opciones de menú para los módulos que el usuario puede acceder:

```html
{% if current_user.rol in ['ventas', 'admin'] %}
<a href="{{ url_for('estudiante.dashboard_ventas') }}">
    <i class="fas fa-chart-line me-2"></i>Ventas
</a>
{% endif %}
```

#### Dashboard General ([templates/estudiante/dashboard_general.html](templates/estudiante/dashboard_general.html))
- **Sidebar:** Solo muestra enlaces a módulos permitidos
- **Tarjetas de módulos:** Solo renderiza las tarjetas de los módulos accesibles
- **Responsivo:** El grid se ajusta automáticamente según los módulos visibles

### 4. Comportamiento del Sistema

#### Para Rol "Ventas"
✅ Puede acceder a:
- Dashboard General
- Módulo de Ventas (completo)
- Ver análisis regional

❌ No puede acceder a:
- Módulo de Compras
- Módulo de Logística
- Módulo de Planeación
- Ajustar precios (solo Admin)

#### Para Rol "Compras"
✅ Puede acceder a:
- Dashboard General
- Módulo de Compras (completo)
- Crear órdenes manuales
- Procesar requerimientos de Planeación

❌ No puede acceder a:
- Módulo de Ventas
- Módulo de Logística
- Módulo de Planeación

#### Para Rol "Logística"
✅ Puede acceder a:
- Dashboard General
- Módulo de Logística (completo)
- Recibir compras
- Crear despachos regionales
- Ajustar inventarios

❌ No puede acceder a:
- Módulo de Ventas
- Módulo de Compras
- Módulo de Planeación

#### Para Rol "Planeación"
✅ Puede acceder a:
- Dashboard General
- Módulo de Planeación (completo)
- Generar pronósticos
- Crear requerimientos de compra

❌ No puede acceder a:
- Módulo de Ventas
- Módulo de Compras
- Módulo de Logística

#### Para Rol "Admin"
✅ Puede acceder a:
- **TODOS** los módulos
- Todas las funciones
- Ajustar precios de productos
- Asignar roles a compañeros

### 5. Mensajes de Error

Cuando un usuario intenta acceder a un módulo sin permisos:

```
🚫 Acceso denegado. Esta función requiere el rol: compras, admin. Tu rol actual es: ventas.
```

Y es redirigido automáticamente al Dashboard General.

### 6. Rutas Sin Restricción de Rol Específico

Estas rutas están disponibles para **todos** los estudiantes (solo requieren @login_required):
- `/estudiante/home` - Página de inicio
- `/estudiante/dashboard` - Dashboard (redirige a general)
- `/estudiante/general` - Dashboard general (vista resumen)

## Archivos Modificados

1. ✅ [routes/estudiante.py](routes/estudiante.py) - Decorador y restricciones en ~60 rutas
2. ✅ [templates/estudiante/_sidebar.html](templates/estudiante/_sidebar.html) - Sidebar condicional
3. ✅ [templates/estudiante/dashboard_general.html](templates/estudiante/dashboard_general.html) - Módulos condicionales

## Archivos Creados

1. 📄 [aplicar_restricciones_rol.py](aplicar_restricciones_rol.py) - Script de migración (temporal)

## Testing Recomendado

### Caso 1: Estudiante con rol "Ventas"
1. Iniciar sesión
2. Verificar que en sidebar solo aparece: Dashboard General y Ventas
3. Intentar acceder a `/estudiante/compras` directamente → debe redirigir con error
4. Verificar que solo aparece tarjeta de Ventas en dashboard general

### Caso 2: Estudiante con rol "Admin"
1. Iniciar sesión
2. Verificar que aparecen TODOS los módulos en sidebar
3. Verificar acceso a todas las rutas
4. Verificar que aparecen las 4 tarjetas en dashboard general

### Caso 3: Estudiante sin rol asignado
1. Iniciar sesión
2. Debe ver mensaje: "No tienes una empresa o rol asignado"
3. No puede acceder a ningún módulo específico

## Ventajas del Sistema

1. **Seguridad:** Control de acceso a nivel de ruta (backend)
2. **UX Mejorada:** Solo muestra opciones disponibles (frontend)
3. **Flexibilidad:** El Admin tiene acceso completo
4. **Claridad:** Mensajes de error informativos
5. **Mantenibilidad:** Decorador reutilizable para nuevas rutas
6. **Escalabilidad:** Fácil agregar nuevos roles o permisos

## Notas Importantes

- El Dashboard General sigue siendo accesible para TODOS los roles
- Los estudiantes pueden ver información general de la empresa independientemente de su rol
- Solo las **acciones** están restringidas según el rol
- El rol `admin` tiene acceso total y es el único que puede:
  - Ajustar precios
  - Ver todos los módulos
  - Asignar roles a otros estudiantes

---

**Fecha de Implementación:** 22 de Enero, 2026  
**Implementado por:** Sistema de Control de Acceso Basado en Roles (RBAC)
