"""
Script para calibrar la demanda de los productos en la simulación activa.

Uso:
    python calibrar_demanda.py 700 500
       (inv_750ml=700, inv_1L=500 — los mismos valores con que se inició la simulación)

Si no se pasan argumentos usa los valores por defecto (700 / 500).

La fórmula mantiene el mismo criterio que reiniciar_simulacion():
  - El stock inicial debe consumirse en SEMANAS_COBERTURA semanas
  - punto_reorden y stock_seguridad se recalculan acorde
"""
import sys
from app import app
from extensions import db
from models import Producto, Inventario

DIAS_COBERTURA     = 5
REGIONES           = 5
DIAS_REORDEN       = 3
DIAS_SEGURIDAD     = 1
FACTOR_DESVIACION  = 0.20


def calibrar(inv_750ml: int = 700, inv_1l: int = 500):
    with app.app_context():
        productos = Producto.query.filter_by(activo=True).all()
        if not productos:
            print("⚠️  No hay productos registrados.")
            return

        print(f"\n{'='*60}")
        print(f"  Calibración automática de demanda")
        print(f"  Inv. inicial 750ml = {inv_750ml} und  |  1L = {inv_1l} und")
        print(f"  Cobertura objetivo  = {DIAS_COBERTURA} días")
        print(f"{'='*60}\n")

        for producto in productos:
            inv_inicial = inv_750ml if '750ml' in producto.nombre else inv_1l

            nueva_demanda    = max(1, round(inv_inicial * 7 / (DIAS_COBERTURA * REGIONES)))
            nueva_desviacion = max(1, round(nueva_demanda * FACTOR_DESVIACION))

            demanda_diaria_empresa = nueva_demanda / 7.0 * REGIONES
            nuevo_punto_reorden    = max(1, round(demanda_diaria_empresa * DIAS_REORDEN))
            nuevo_stock_seguridad  = max(1, round(demanda_diaria_empresa * DIAS_SEGURIDAD))
            nuevo_stock_maximo     = inv_inicial * 3

            anterior_demanda    = producto.demanda_promedio
            anterior_desviacion = producto.desviacion_demanda

            producto.demanda_promedio   = nueva_demanda
            producto.desviacion_demanda = nueva_desviacion
            producto.stock_maximo       = nuevo_stock_maximo

            # Actualizar punto_reorden y stock_seguridad en TODOS los inventarios del producto
            inventarios = Inventario.query.filter_by(producto_id=producto.id).all()
            for inv in inventarios:
                inv.punto_reorden    = nuevo_punto_reorden
                inv.stock_seguridad  = nuevo_stock_seguridad

            print(f"  [{producto.codigo}] {producto.nombre}")
            print(f"    demanda_promedio  : {anterior_demanda:.1f}  →  {nueva_demanda}")
            print(f"    desviacion_demanda: {anterior_desviacion:.1f}  →  {nueva_desviacion}")
            print(f"    punto_reorden     : {nuevo_punto_reorden}  |  stock_seguridad: {nuevo_stock_seguridad}")
            print(f"    stock_maximo      : {nuevo_stock_maximo}  |  consumo diario aprox.: {demanda_diaria_empresa:.0f} und\n")

        db.session.commit()
        print("✅  Calibración aplicada correctamente a la BD.\n")


if __name__ == '__main__':
    inv_750ml = int(sys.argv[1]) if len(sys.argv) > 1 else 700
    inv_1l    = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    calibrar(inv_750ml, inv_1l)
