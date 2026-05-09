"""
Script para calibrar la demanda de los productos en la simulación activa.

Uso:
    python calibrar_demanda.py 120 80
       (inv_750ml=120, inv_1L=80 — los mismos valores con que se inició la simulación)

Si no se pasan argumentos usa los valores por defecto (120 / 80).

La fórmula mantiene el mismo criterio que reiniciar_simulacion():
  - El stock inicial debe consumirse en SEMANAS_COBERTURA semanas
  - punto_reorden y stock_seguridad se recalculan acorde
"""
import sys
from app import app
from extensions import db
from models import Producto, Inventario
from utils.parametros_iniciales import (
    INVENTARIO_INICIAL_750_DEFAULT,
    INVENTARIO_INICIAL_1L_DEFAULT,
    calcular_parametros_demanda,
    inventario_inicial_por_producto,
)

def calibrar(inv_750ml: int = INVENTARIO_INICIAL_750_DEFAULT, inv_1l: int = INVENTARIO_INICIAL_1L_DEFAULT):
    with app.app_context():
        productos = Producto.query.filter_by(activo=True).all()
        if not productos:
            print("⚠️  No hay productos registrados.")
            return

        print(f"\n{'='*60}")
        print(f"  Calibración automática de demanda")
        print(f"  Inv. inicial 750ml = {inv_750ml} und  |  1L = {inv_1l} und")
        print(f"{'='*60}\n")

        for producto in productos:
            inv_inicial = inventario_inicial_por_producto(producto, inv_750ml, inv_1l)
            params = calcular_parametros_demanda(inv_inicial)

            anterior_demanda    = producto.demanda_promedio
            anterior_desviacion = producto.desviacion_demanda

            producto.demanda_promedio = params['demanda_promedio']
            producto.desviacion_demanda = params['desviacion_demanda']
            producto.stock_maximo = params['stock_maximo']

            # Actualizar punto_reorden y stock_seguridad en TODOS los inventarios del producto
            inventarios = Inventario.query.filter_by(producto_id=producto.id).all()
            for inv in inventarios:
                inv.punto_reorden = params['punto_reorden']
                inv.stock_seguridad = params['stock_seguridad']

            print(f"  [{producto.codigo}] {producto.nombre}")
            print(f"    demanda_promedio  : {anterior_demanda:.1f}  →  {params['demanda_promedio']}")
            print(f"    desviacion_demanda: {anterior_desviacion:.1f}  →  {params['desviacion_demanda']}")
            print(f"    punto_reorden     : {params['punto_reorden']}  |  stock_seguridad: {params['stock_seguridad']}")
            print(f"    stock_maximo      : {params['stock_maximo']}  |  consumo diario aprox.: {params['demanda_diaria_empresa']:.0f} und\n")

        db.session.commit()
        print("✅  Calibración aplicada correctamente a la BD.\n")


if __name__ == '__main__':
    inv_750ml = int(sys.argv[1]) if len(sys.argv) > 1 else INVENTARIO_INICIAL_750_DEFAULT
    inv_1l = int(sys.argv[2]) if len(sys.argv) > 2 else INVENTARIO_INICIAL_1L_DEFAULT
    calibrar(inv_750ml, inv_1l)
