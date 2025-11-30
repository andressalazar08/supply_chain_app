"""
Script para eliminar restricciones de rol en routes/estudiante.py
Permite que todos los estudiantes accedan a todos los módulos
"""

import re

# Leer el archivo
with open('routes/estudiante.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón para encontrar bloques de restricción
pattern = r"    if current_user\.rol != '[^']+?':\s+flash\('[^']+?', 'error'\)\s+return redirect\(url_for\('[^']+?'\)\)\s+"

# Reemplazar con comentario
replacement = "    # Acceso permitido para todos los roles - Panel unificado\n    "

# Hacer el reemplazo
new_content = re.sub(pattern, replacement, content)

# Guardar el archivo
with open('routes/estudiante.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Restricciones de rol eliminadas exitosamente")
print(f"📝 Se encontraron y comentaron las validaciones de acceso por rol")
