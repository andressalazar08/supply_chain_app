"""
Utilidades para generar histórico inicial y órdenes de compra para nuevas simulaciones
"""
import random
from datetime import datetime, timedelta
from models import (Simulacion, Empresa, Producto, Inventario, Venta, Compra, DemandaMercadoDiaria)
from extensions import db
from utils.parametros_iniciales import (
    DIAS_ARRANQUE_PEDIDOS,
    MAX_UNIDADES_ORDENES_ARRANQUE,
    DEMANDA_DIARIA_MEDIA_ARRANQUE,
)


def generar_historico_30dias(simulacion, empresas):
    """
    Genera un histórico de 30 días de ventas previas a la simulación.
    Las ventas se generan usando demanda_promedio y desviacion_demanda de cada producto.
    Se guardan con semana_simulacion negativa (-30 a -1) para diferenciarse del juego real.
    
    El histórico es determinístico: mismo producto y empresa → siempre mismo histórico
    
    Args:
        simulacion: Objeto Simulacion
        empresas: Lista de empresas para las que generar histórico
    """
    try:
        PRODUCTOS = Producto.query.filter_by(activo=True).all()
        if not PRODUCTOS:
            return False, "No hay productos activos para generar histórico"

        if not empresas:
            return False, "No hay empresas para generar histórico"

        base_historica = DemandaMercadoDiaria.query.filter(
            DemandaMercadoDiaria.simulacion_id == simulacion.id,
            DemandaMercadoDiaria.dia_simulacion < 0,
            DemandaMercadoDiaria.dia_simulacion >= -30
        ).order_by(
            DemandaMercadoDiaria.dia_simulacion,
            DemandaMercadoDiaria.producto_id,
            DemandaMercadoDiaria.region
        ).all()

        if not base_historica:
            return False, "No existe base central histórica (-30 a -1) para generar ventas"

        ventas_creadas = 0

        for fila in base_historica:
            demanda_total = max(0, int(round(fila.demanda_base or 0)))
            if demanda_total <= 0:
                continue

            # Distribución determinística del mercado histórico entre empresas.
            pesos = []
            for empresa in empresas:
                rng = random.Random(f"hist:{simulacion.id}:{fila.dia_simulacion}:{fila.producto_id}:{fila.region}:{empresa.id}")
                pesos.append((empresa, 0.5 + rng.random()))

            suma_pesos = sum(p for _, p in pesos) or 1.0
            cuotas = [(emp, (p / suma_pesos) * demanda_total) for emp, p in pesos]

            cantidades = {emp.id: int(c) for emp, c in cuotas}
            restante = demanda_total - sum(cantidades.values())
            if restante > 0:
                cuotas_ordenadas = sorted(cuotas, key=lambda item: (item[1] - int(item[1])), reverse=True)
                for i in range(restante):
                    cantidades[cuotas_ordenadas[i % len(cuotas_ordenadas)][0].id] += 1

            for empresa in empresas:
                cantidad_solicitada = max(0, int(cantidades.get(empresa.id, 0)))
                if cantidad_solicitada <= 0:
                    continue

                rng_venta = random.Random(f"hist-venta:{simulacion.id}:{empresa.id}:{fila.dia_simulacion}:{fila.producto_id}:{fila.region}")
                factor_atencion = 0.90 + (rng_venta.random() * 0.10)
                cantidad_vendida = min(cantidad_solicitada, int(round(cantidad_solicitada * factor_atencion)))
                cantidad_perdida = max(0, cantidad_solicitada - cantidad_vendida)

                producto = next((p for p in PRODUCTOS if p.id == fila.producto_id), None)
                if not producto:
                    continue

                precio_unitario = producto.precio_actual or producto.precio_base
                costo_unitario = producto.costo_unitario
                ingreso_total = cantidad_vendida * precio_unitario
                margen = ingreso_total - (cantidad_vendida * costo_unitario)

                venta = Venta(
                    empresa_id=empresa.id,
                    producto_id=fila.producto_id,
                    semana_simulacion=fila.dia_simulacion,
                    region=fila.region,
                    canal='retail',
                    cantidad_solicitada=cantidad_solicitada,
                    cantidad_vendida=cantidad_vendida,
                    cantidad_perdida=cantidad_perdida,
                    demanda_mercado_total=demanda_total,
                    precio_unitario=precio_unitario,
                    ingreso_total=round(ingreso_total, 2),
                    costo_unitario=costo_unitario,
                    margen=round(margen, 2)
                )
                db.session.add(venta)
                ventas_creadas += 1

        db.session.commit()
        return True, f"Histórico de 30 días generado desde demanda central: {ventas_creadas} ventas"

    except Exception as e:
        db.session.rollback()
        return False, f"Error generando histórico: {str(e)}"


def generar_ordenes_iniciales(simulacion, empresas):
    """
    Genera órdenes de compra que llegarán en los Días 1, 2 y 3.
    Cantidad diaria por producto: perfil objetivo definido por DEMANDA_DIARIA_MEDIA_ARRANQUE,
    respetando capacidad máxima diaria MAX_UNIDADES_ORDENES_ARRANQUE.
    Estas órdenes aportan el "colchón inicial" para que no fallen en los primeros días.
    
    Args:
        simulacion: Objeto Simulacion
        empresas: Lista de empresas para las que generar órdenes
        
    Returns:
        tuple: (éxito, mensaje)
    """
    try:
        PRODUCTOS = Producto.query.filter_by(activo=True).all()
        
        if not PRODUCTOS:
            return False, "No hay productos activos para generar órdenes iniciales"
        
        ordenes_creadas = 0
        dias_entrega_iniciales = list(DIAS_ARRANQUE_PEDIDOS)
        perfil_diario = {
            codigo.upper(): int(cantidad)
            for codigo, cantidad in DEMANDA_DIARIA_MEDIA_ARRANQUE.items()
            if int(cantidad) > 0
        }

        total_perfil = sum(perfil_diario.values())
        if total_perfil <= 0:
            return False, 'El perfil de arranque está vacío.'

        factor_ajuste = min(1.0, float(MAX_UNIDADES_ORDENES_ARRANQUE) / float(total_perfil))
        
        for empresa in empresas:
            productos_por_codigo = {(p.codigo or '').upper(): p for p in PRODUCTOS}

            for dia_entrega in dias_entrega_iniciales:
                for codigo, cantidad_objetivo in perfil_diario.items():
                    producto = productos_por_codigo.get(codigo)
                    if not producto:
                        continue

                    cantidad_producto = int(round(cantidad_objetivo * factor_ajuste))
                    if cantidad_producto <= 0:
                        continue

                    costo_unitario = producto.costo_unitario
                    costo_total = cantidad_producto * costo_unitario

                    compra = Compra(
                        empresa_id=empresa.id,
                        producto_id=producto.id,
                        semana_orden=-1,  # "Ordenado" antes de empezar
                        semana_entrega=dia_entrega,
                        cantidad=cantidad_producto,
                        costo_unitario=costo_unitario,
                        costo_total=round(costo_total, 2),
                        estado='en_transito'
                    )
                    db.session.add(compra)
                    ordenes_creadas += 1
        
        db.session.commit()
        return True, f"Órdenes iniciales generadas: {ordenes_creadas} compras distribuidas en Días 1, 2 y 3"
    
    except Exception as e:
        db.session.rollback()
        return False, f"Error generando órdenes iniciales: {str(e)}"
