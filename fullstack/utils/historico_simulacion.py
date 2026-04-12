"""
Utilidades para generar histórico inicial y órdenes de compra para nuevas simulaciones
"""
import random
from datetime import datetime, timedelta
from models import (Simulacion, Empresa, Producto, Inventario, Venta, Compra)
from extensions import db


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
        REGIONES = ['Caribe', 'Pacifica', 'Orinoquia', 'Amazonia', 'Andina']
        PRODUCTOS = Producto.query.filter_by(activo=True).all()
        
        if not PRODUCTOS:
            return False, "No hay productos activos para generar histórico"
        
        # Seed determinístico basado en simulación y empresa para consistencia
        random.seed(42)  # Siempre el mismo para la misma empresa
        
        ventas_creadas = 0
        
        for empresa in empresas:
            # Para cada día del histórico (-30 a -1)
            for dia_offset in range(-30, 0):
                semana_historica = dia_offset  # -30 a -1
                
                # Generar entre 2-4 productos vendidos ese día (realista)
                num_productos = random.randint(2, 4)
                productos_alearios = random.sample(PRODUCTOS, min(num_productos, len(PRODUCTOS)))
                
                for producto in productos_alearios:
                    # Usar la demanda_promedio como base (dividida entre regiones)
                    demanda_base = producto.demanda_promedio / 5  # 5 regiones
                    desviacion = producto.desviacion_demanda / 5
                    
                    # Generar cantidad vendida con distribución normal
                    cantidad_vendida = max(0, int(round(random.gauss(demanda_base, desviacion))))
                    cantidad_solicitada = max(cantidad_vendida, int(round(cantidad_vendida * random.uniform(0.95, 1.15))))  # Variación en demanda
                    cantidad_perdida = max(0, cantidad_solicitada - cantidad_vendida)
                    
                    # Si hay venta, registrarla
                    if cantidad_vendida > 0:
                        precio_unitario = producto.precio_actual or producto.precio_base
                        ingreso_total = cantidad_vendida * precio_unitario
                        costo_unitario = producto.costo_unitario
                        margen = ingreso_total - (cantidad_vendida * costo_unitario)
                        
                        venta = Venta(
                            empresa_id=empresa.id,
                            producto_id=producto.id,
                            semana_simulacion=semana_historica,  # Negativo para histórico
                            region=random.choice(REGIONES),
                            canal=random.choice(['retail', 'mayorista', 'distribuidor']),
                            cantidad_solicitada=cantidad_solicitada,
                            cantidad_vendida=cantidad_vendida,
                            cantidad_perdida=cantidad_perdida,
                            demanda_mercado_total=cantidad_solicitada,
                            precio_unitario=precio_unitario,
                            ingreso_total=round(ingreso_total, 2),
                            costo_unitario=costo_unitario,
                            margen=round(margen, 2)
                        )
                        db.session.add(venta)
                        ventas_creadas += 1
        
        db.session.commit()
        return True, f"Histórico de 30 días generado: {ventas_creadas} registros de venta"
    
    except Exception as e:
        db.session.rollback()
        return False, f"Error generando histórico: {str(e)}"


def generar_ordenes_iniciales(simulacion, empresas):
    """
    Genera órdenes de compra que llegarán el Día 1.
    Cantidad: 2-3 días de demanda promedio total (sin exceder 1500 unidades totales)
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
        
        for empresa in empresas:
            # Calcular demanda total promedio: suma de todas las demandas semanales / 7 (para convertir a diaria)
            demanda_diaria_total = sum(p.demanda_promedio for p in PRODUCTOS) / 7
            
            # Cantidad a pedir: 2.5 días de demanda (para dar colchón de 2-3 días)
            dias_cobertura = 2.5
            cantidad_total_deseada = demanda_diaria_total * dias_cobertura
            
            # Limitar a máximo 1500 unidades totales
            cantidad_total_a_pedir = min(cantidad_total_deseada, 1500)
            
            # Distribuir proporcionalmente por demanda de cada producto
            for producto in PRODUCTOS:
                proporcion = (producto.demanda_promedio / sum(p.demanda_promedio for p in PRODUCTOS))
                cantidad_producto = int(round(cantidad_total_a_pedir * proporcion))
                
                if cantidad_producto > 0:
                    costo_unitario = producto.costo_unitario
                    costo_total = cantidad_producto * costo_unitario
                    
                    # Orden llega el día 1 (semana_entrega = 1)
                    compra = Compra(
                        empresa_id=empresa.id,
                        producto_id=producto.id,
                        semana_orden=-1,  # "Ordenado" antes de empezar
                        semana_entrega=1,  # Llega día 1
                        cantidad=cantidad_producto,
                        costo_unitario=costo_unitario,
                        costo_total=round(costo_total, 2),
                        estado='en_transito'
                    )
                    db.session.add(compra)
                    ordenes_creadas += 1
        
        db.session.commit()
        return True, f"Órdenes iniciales generadas: {ordenes_creadas} compras para Día 1"
    
    except Exception as e:
        db.session.rollback()
        return False, f"Error generando órdenes iniciales: {str(e)}"
