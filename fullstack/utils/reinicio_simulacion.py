"""
Utilidades para reiniciar simulación manteniendo histórico
"""
from models import (Simulacion, Empresa, Producto, Inventario, Usuario)
from extensions import db
from datetime import datetime


def reiniciar_simulacion(capital_inicial=50000000, nombre_simulacion=None):
    """
    Crea una nueva simulación manteniendo el histórico de la anterior
    Establece condiciones iniciales iguales para todas las empresas
    
    Args:
        capital_inicial: Capital con el que empezarán todas las empresas
        nombre_simulacion: Nombre descriptivo de la nueva simulación
    
    Returns:
        tuple: (nueva_simulacion, mensaje_resultado)
    """
    try:
        # 1. Desactivar simulación actual
        simulacion_anterior = Simulacion.query.filter_by(activa=True).first()
        if simulacion_anterior:
            simulacion_anterior.activa = False
            simulacion_anterior.estado = 'finalizado'
            simulacion_anterior.fecha_fin = datetime.utcnow()
            db.session.add(simulacion_anterior)
        
        # 2. Crear nueva simulación
        if not nombre_simulacion:
            numero_sim = Simulacion.query.count() + 1
            nombre_simulacion = f'Simulación {numero_sim}'
        
        nueva_simulacion = Simulacion(
            nombre=nombre_simulacion,
            dia_actual=1,
            estado='pausado',
            fecha_inicio=datetime.utcnow(),
            duracion_dias=30,
            capital_inicial_empresas=capital_inicial,
            activa=True
        )
        db.session.add(nueva_simulacion)
        db.session.flush()  # Obtener ID de la nueva simulación
        
        # 3. Obtener empresas existentes (de simulación anterior)
        empresas_anteriores = Empresa.query.filter_by(simulacion_id=simulacion_anterior.id).all() if simulacion_anterior else []
        
        if not empresas_anteriores:
            # Si no hay empresas previas, buscar todas las empresas sin simulación asignada
            empresas_anteriores = Empresa.query.filter_by(simulacion_id=None).all()
        
        if not empresas_anteriores:
            return None, "No hay empresas registradas para reiniciar"
        
        # 4. Crear copias de empresas para la nueva simulación
        nuevas_empresas = []
        for empresa_ant in empresas_anteriores:
            nueva_empresa = Empresa(
                nombre=empresa_ant.nombre,
                capital_inicial=capital_inicial,
                capital_actual=capital_inicial,
                activa=True,
                profesor_id=empresa_ant.profesor_id,
                simulacion_id=nueva_simulacion.id
            )
            db.session.add(nueva_empresa)
            db.session.flush()  # Obtener ID
            nuevas_empresas.append(nueva_empresa)
            
            # Actualizar usuarios para que apunten a la nueva empresa
            usuarios_empresa = Usuario.query.filter_by(empresa_id=empresa_ant.id).all()
            for usuario in usuarios_empresa:
                usuario.empresa_id = nueva_empresa.id
        
        # 5. Establecer inventarios iniciales IGUALES para todas las empresas
        productos = Producto.query.filter_by(activo=True).all()
        
        inventarios_config = {}
        for producto in productos:
            # Determinar cantidad inicial según tipo de producto
            # Valores ajustados: solo 1-1.5 días de cobertura para forzar gestión activa
            if '750ml' in producto.nombre:
                cantidad_inicial = 120  # ~1 día de operación
            else:  # 1L
                cantidad_inicial = 80  # ~1 día de operación
            
            inventarios_config[producto.id] = cantidad_inicial
        
        # Crear inventarios para cada empresa
        for empresa in nuevas_empresas:
            for producto in productos:
                inventario = Inventario(
                    empresa_id=empresa.id,
                    producto_id=producto.id,
                    cantidad_actual=inventarios_config[producto.id],
                    cantidad_reservada=0,
                    punto_reorden=50,
                    stock_seguridad=20,
                    costo_promedio=producto.costo_unitario
                )
                db.session.add(inventario)
        
        # 6. Commit de todos los cambios
        db.session.commit()
        
        mensaje = f"""
        ✅ Simulación reiniciada exitosamente
        
        📊 Nueva simulación: {nombre_simulacion}
        🏢 Empresas inicializadas: {len(nuevas_empresas)}
        💰 Capital inicial: ${capital_inicial:,.0f}
        📦 Inventario por producto:
           - Productos 750ml: 300 unidades
           - Productos 1L: 200 unidades
        
        🔄 La simulación anterior se mantuvo como histórico
        """
        
        return nueva_simulacion, mensaje
        
    except Exception as e:
        db.session.rollback()
        return None, f"Error al reiniciar simulación: {str(e)}"


def obtener_simulacion_activa():
    """Obtiene la simulación actualmente activa"""
    return Simulacion.query.filter_by(activa=True).first()


def obtener_historico_simulaciones():
    """Obtiene todas las simulaciones ordenadas por fecha"""
    return Simulacion.query.order_by(Simulacion.created_at.desc()).all()
