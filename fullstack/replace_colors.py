"""
Script para reemplazar todos los colores azul/morado por rojo en templates HTML
"""

import os
import re

def replace_colors_in_file(filepath):
    """Reemplaza colores azul/morado por rojo en un archivo"""
    
    # Mapeo de colores
    color_map = {
        '#667eea': '#c41e3a',  # Azul → Rojo universitario
        '#764ba2': '#e63946',  # Morado → Rojo claro
        '#3498db': '#c41e3a',  # Azul → Rojo universitario
        '#2193b0': '#f4a261',  # Cyan → Naranja
        '#6dd5ed': '#e76f51',  # Cyan claro → Coral
        '#2c3e50': '#34495e',  # Gris oscuro (mantener)
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Reemplazar cada color
        for old_color, new_color in color_map.items():
            # Case insensitive replacement
            content = re.sub(old_color, new_color, content, flags=re.IGNORECASE)
        
        # Solo escribir si hubo cambios
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error procesando {filepath}: {e}")
        return False

def process_templates():
    """Procesa todos los templates HTML"""
    
    templates_dir = 'templates'
    files_changed = 0
    
    print("="*80)
    print("🎨 REEMPLAZANDO COLORES AZUL/MORADO → ROJO")
    print("="*80)
    
    for root, dirs, files in os.walk(templates_dir):
        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                
                if replace_colors_in_file(filepath):
                    files_changed += 1
                    relative_path = os.path.relpath(filepath)
                    print(f"✅ {relative_path}")
    
    print("\n" + "="*80)
    print(f"✅ COMPLETADO: {files_changed} archivos actualizados")
    print("="*80)
    print("\n📋 COLORES REEMPLAZADOS:")
    print("   🔵 #667eea → 🔴 #c41e3a (Rojo universitario)")
    print("   🟣 #764ba2 → 🔴 #e63946 (Rojo claro)")
    print("   🔷 #3498db → 🔴 #c41e3a (Rojo universitario)")
    print("   🔷 #2193b0 → 🟠 #f4a261 (Naranja)")
    print("   🔷 #6dd5ed → 🧡 #e76f51 (Coral)")
    print("\n💡 Recarga la aplicación con Ctrl+F5")
    print("="*80)

if __name__ == '__main__':
    process_templates()
