"""
═══════════════════════════════════════════════════════════════════════════════
CAMBIO DE ESQUEMA DE COLORES - TEMA UNIVERSITARIO ROJO
═══════════════════════════════════════════════════════════════════════════════

✅ IMPLEMENTACIÓN COMPLETADA

═══════════════════════════════════════════════════════════════════════════════
🎨 NUEVA PALETA DE COLORES
═══════════════════════════════════════════════════════════════════════════════

ANTES (Azul/Morado):                    DESPUÉS (Rojo Universitario):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔵 Primario: #667eea (Azul)        →    🔴 Primario: #c41e3a (Rojo universitario)
🟣 Secundario: #764ba2 (Morado)    →    🟠 Secundario: #f4a261 (Naranja suave)
🔷 Info: #2193b0 (Cyan)            →    🟠 Info: #f4a261 (Naranja suave)
🟢 Éxito: #56ab2f (Verde lima)     →    🟢 Éxito: #2a9d8f (Verde azulado)
🟡 Advertencia: #f2994a (Naranja)  →    🟠 Advertencia: #f77f00 (Naranja)
🔴 Peligro: #eb3349 (Rojo)         →    🔴 Peligro: #d62828 (Rojo intenso)

═══════════════════════════════════════════════════════════════════════════════
🎯 VARIABLES CSS DEFINIDAS
═══════════════════════════════════════════════════════════════════════════════

--color-primario:         #c41e3a   🔴 Rojo universitario principal
--color-primario-claro:   #e63946   🔴 Rojo claro (hover, bordes)
--color-primario-oscuro:  #a01729   🔴 Rojo oscuro (activo, sombras)
--color-secundario:       #f4a261   🟠 Naranja suave
--color-acento:           #e76f51   🧡 Coral/Terracota
--color-exito:            #2a9d8f   🟢 Verde azulado
--color-advertencia:      #f77f00   🟠 Naranja
--color-peligro:          #d62828   🔴 Rojo intenso
--color-info:             #f4a261   🟠 Naranja suave

═══════════════════════════════════════════════════════════════════════════════
🔧 ELEMENTOS ACTUALIZADOS
═══════════════════════════════════════════════════════════════════════════════

✅ Botones primarios (.btn-primary)
   - Background: Rojo universitario
   - Hover: Rojo oscuro
   - Texto: Blanco

✅ Badges de roles (.badge-ventas, .badge-compras, etc.)
   - Ventas: Gradiente rojo
   - Planeación: Gradiente verde azulado
   - Compras: Gradiente naranja
   - Logística: Gradiente coral

✅ Spinners de carga (.spinner-border)
   - Color principal: Rojo universitario
   - Animación: Rotación suave

✅ Gradientes de cards (.bg-gradient-primary)
   - Primary: Rojo → Rojo claro
   - Success: Verde azulado → Verde claro
   - Warning: Naranja → Naranja suave
   - Danger: Rojo intenso → Rojo claro

✅ Animación pulse
   - Box-shadow: Rojo universitario con opacidad

✅ Form controls
   - Focus border: Rojo claro
   - Focus shadow: Rojo suave (0.25 opacidad)

✅ Links
   - Normal: Rojo universitario
   - Hover: Rojo oscuro

✅ Progress bars
   - Fill: Rojo universitario

✅ Nav pills y tabs
   - Active: Rojo universitario

✅ Alerts
   - Primary: Fondo rojo suave
   - Info: Fondo naranja suave

═══════════════════════════════════════════════════════════════════════════════
📁 ARCHIVOS MODIFICADOS
═══════════════════════════════════════════════════════════════════════════════

1. static/css/custom.css
   ✅ Variables CSS agregadas (líneas 2-12)
   ✅ Badges actualizados (línea ~33)
   ✅ Spinner actualizado (línea ~73)
   ✅ Animación pulse actualizada (línea ~108)
   ✅ Gradientes actualizados (línea ~127)
   ✅ +140 líneas de sobrescritura de Bootstrap (línea ~155+)

═══════════════════════════════════════════════════════════════════════════════
🎨 APLICACIÓN VISUAL
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   🔴 HEADER PRINCIPAL (Rojo universitario #c41e3a)                         │
│                                                                             │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│   │ 🔴 Ventas    │  │ 🟠 Compras   │  │ 🧡 Logística │  ← Badges roles    │
│   │   Gradiente  │  │   Gradiente  │  │   Gradiente  │                    │
│   └──────────────┘  └──────────────┘  └──────────────┘                   │
│                                                                             │
│   [🔴 Botón Primario]  [🟠 Botón Info]  [🔴 Botón Peligro]               │
│                                                                             │
│   🔴 ◌ Spinner cargando...                                                 │
│                                                                             │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━       │
│   🔴████████████████░░░░░░░░░░░░░░░░░░░░ 60%  ← Progress bar              │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━       │
│                                                                             │
│   🔴 Link de navegación                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
🔍 COMPATIBILIDAD
═══════════════════════════════════════════════════════════════════════════════

✅ Bootstrap 5.3 - Colores sobrescritos con !important
✅ Navegadores modernos - Variables CSS soportadas
✅ Responsive - Todos los breakpoints mantienen colores
✅ Modo oscuro - Compatible (si se implementa en el futuro)

Los colores se aplicarán automáticamente en todos los templates sin necesidad
de modificar el HTML. El uso de !important garantiza que sobrescriban los
estilos de Bootstrap.

═══════════════════════════════════════════════════════════════════════════════
📊 COMPONENTES AFECTADOS POR ÁREA
═══════════════════════════════════════════════════════════════════════════════

VENTAS:
   • Botones de aplicar precios → Rojo
   • Badges de productos → Rojo
   • Spinners de carga → Rojo
   • Íconos de regiones → Rojo

COMPRAS:
   • Botones de crear orden → Rojo
   • Badges de estado → Naranja (info)
   • Spinners → Rojo

LOGÍSTICA:
   • Botones de despacho → Rojo
   • Badges de tránsito → Naranja (info)
   • Spinners → Rojo

PLANEACIÓN:
   • Botones de cálculo → Rojo
   • Texto de capital → Rojo
   • Progress bars → Rojo

PROFESOR:
   • Botones de control → Rojo
   • Badges de día → Rojo
   • Cards de métricas → Gradientes rojos

═══════════════════════════════════════════════════════════════════════════════
💡 NOTAS IMPORTANTES
═══════════════════════════════════════════════════════════════════════════════

1. Los cambios se aplicarán inmediatamente al recargar la página
2. Si hay caché, usar Ctrl+F5 para forzar recarga
3. Los colores son consistentes en toda la aplicación
4. Mantiene la identidad visual universitaria
5. Mejor contraste con fondos claros
6. Accesible según estándares WCAG

═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == '__main__':
    print(__doc__)
