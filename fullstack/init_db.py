"""
Script de inicialización de base de datos
Crea datos de ejemplo para pruebas
"""

from app import app
from extensions import db
from models import Usuario, Empresa, Producto, Inventario, Simulacion, Escenario, Venta, Pronostico
from werkzeug.security import generate_password_hash
import random

def init_db():
    """Inicializa la base de datos con datos de ejemplo"""
    
    with app.app_context():
        # Eliminar todas las tablas existentes
        db.drop_all()
        
        # Crear todas las tablas
        db.create_all()
        
        print("✓ Base de datos creada")
        
        # Crear usuario administrador
        admin = Usuario(
            username='admin',
            password=generate_password_hash('admin123'),
            rol='admin',
            nombre_completo='Administrador del Sistema',
            email='admin@erpeducativo.com'
        )
        db.session.add(admin)
        print("✓ Usuario administrador creado")
        
        # Crear empresas de ejemplo
        empresas_data = [
            {'nombre': 'Distribuidora Alpha', 'capital_inicial': 1000000},
            {'nombre': 'Comercializadora Beta', 'capital_inicial': 1000000},
            {'nombre': 'Logística Gamma', 'capital_inicial': 1000000},
        ]
        
        empresas = []
        for emp_data in empresas_data:
            empresa = Empresa(
                nombre=emp_data['nombre'],
                capital_inicial=emp_data['capital_inicial'],
                capital_actual=emp_data['capital_inicial']
            )
            empresas.append(empresa)
            db.session.add(empresa)
        
        db.session.commit()
        print(f"✓ {len(empresas)} empresas creadas")
        
        # Crear estudiantes de ejemplo
        roles = ['ventas', 'planeacion', 'compras', 'logistica']
        roles_num = {'ventas': '1', 'planeacion': '2', 'compras': '3', 'logistica': '4'}
        
        estudiantes_creados = 0
        for i, empresa in enumerate(empresas, 1):
            for rol in roles:
                username = f"estudiante_{roles_num[rol]}_{i}"
                estudiante = Usuario(
                    username=username,
                    password=generate_password_hash('estudiante123'),
                    rol=rol,
                    empresa_id=empresa.id,
                    nombre_completo=f"Estudiante {rol.capitalize()} - {empresa.nombre}",
                    email=f"{username}@erpeducativo.com"
                )
                db.session.add(estudiante)
                estudiantes_creados += 1
        
        db.session.commit()
        print(f"✓ {estudiantes_creados} estudiantes creados")
        
        # Crear productos de ejemplo
        productos_data = [
            {
                'codigo': 'PROD001',
                'nombre': 'Laptop Empresarial',
                'categoria': 'Electrónica',
                'precio_base': 1200.00,
                'precio_actual': 1200.00,
                'precio_sugerido': 1250.00,
                'costo_unitario': 800.00,
                'demanda_promedio': 50,
                'desviacion_demanda': 10,
                'elasticidad_precio': 1.8,
                'tiempo_entrega': 3
            },
            {
                'codigo': 'PROD002',
                'nombre': 'Monitor LED 24"',
                'categoria': 'Electrónica',
                'precio_base': 300.00,
                'precio_actual': 300.00,
                'precio_sugerido': 320.00,
                'costo_unitario': 200.00,
                'demanda_promedio': 80,
                'desviacion_demanda': 15,
                'elasticidad_precio': 1.5,
                'tiempo_entrega': 2
            },
            {
                'codigo': 'PROD003',
                'nombre': 'Teclado Mecánico',
                'categoria': 'Accesorios',
                'precio_base': 150.00,
                'precio_actual': 150.00,
                'precio_sugerido': 165.00,
                'costo_unitario': 100.00,
                'demanda_promedio': 100,
                'desviacion_demanda': 20,
                'elasticidad_precio': 1.3,
                'tiempo_entrega': 1
            },
            {
                'codigo': 'PROD004',
                'nombre': 'Mouse Inalámbrico',
                'categoria': 'Accesorios',
                'precio_base': 50.00,
                'precio_actual': 50.00,
                'precio_sugerido': 55.00,
                'costo_unitario': 30.00,
                'demanda_promedio': 150,
                'desviacion_demanda': 25,
                'elasticidad_precio': 1.2,
                'tiempo_entrega': 1
            },
            {
                'codigo': 'PROD005',
                'nombre': 'Impresora Multifuncional',
                'categoria': 'Electrónica',
                'precio_base': 400.00,
                'precio_actual': 400.00,
                'precio_sugerido': 430.00,
                'costo_unitario': 280.00,
                'demanda_promedio': 30,
                'desviacion_demanda': 8,
                'elasticidad_precio': 1.6,
                'tiempo_entrega': 4
            },
        ]
        
        productos = []
        for prod_data in productos_data:
            producto = Producto(**prod_data)
            productos.append(producto)
            db.session.add(producto)
        
        db.session.commit()
        print(f"✓ {len(productos)} productos creados")
        
        # Crear inventarios iniciales para cada empresa
        inventarios_creados = 0
        for empresa in empresas:
            for producto in productos:
                inventario = Inventario(
                    empresa_id=empresa.id,
                    producto_id=producto.id,
                    cantidad_actual=100,
                    cantidad_reservada=0,
                    punto_reorden=50,
                    stock_seguridad=20,
                    costo_promedio=producto.costo_unitario
                )
                db.session.add(inventario)
                inventarios_creados += 1
        
        db.session.commit()
        print(f"✓ {inventarios_creados} registros de inventario creados")
        
        # Crear simulación inicial
        simulacion = Simulacion(
            dia_actual=1,
            estado='pausado',
            duracion_dias=30
        )
        db.session.add(simulacion)
        db.session.commit()
        print("✓ Simulación inicial creada")
        
        # Crear escenarios de ejemplo
        escenarios_data = [
            {
                'nombre': 'Pico de Demanda - Black Friday',
                'descripcion': 'Aumento del 50% en la demanda de todos los productos',
                'tipo': 'oportunidad',
                'parametros': {'aumento_demanda': 0.5}
            },
            {
                'nombre': 'Huelga de Transportadores',
                'descripcion': 'Retraso de 2 días en todas las entregas',
                'tipo': 'disrupcion',
                'parametros': {'retraso_dias': 2}
            },
            {
                'nombre': 'Crisis de Abastecimiento',
                'descripcion': 'Aumento del 30% en costos de productos',
                'tipo': 'crisis',
                'parametros': {'aumento_costos': 0.3}
            },
            {
                'nombre': 'Promoción Especial',
                'descripcion': 'Oportunidad de venta con margen 20% mayor',
                'tipo': 'oportunidad',
                'parametros': {'aumento_margen': 0.2}
            },
        ]
        
        for esc_data in escenarios_data:
            escenario = Escenario(**esc_data)
            db.session.add(escenario)
        
        db.session.commit()
        print(f"✓ {len(escenarios_data)} escenarios creados")
        
        # Crear datos de ventas históricas de ejemplo (últimos 7 días)
        regiones = ['Caribe', 'Pacifica', 'Orinoquia', 'Amazonia', 'Andina']
        canales = ['retail', 'mayorista', 'distribuidor']
        
        ventas_creadas = 0
        for dia in range(1, 8):  # Días 1 a 7
            for empresa in empresas:
                for producto in productos:
                    # Generar ventas en diferentes regiones
                    num_regiones_vendidas = random.randint(2, 4)  # Vende en 2-4 regiones por día
                    regiones_vendidas = random.sample(regiones, num_regiones_vendidas)
                    
                    for region in regiones_vendidas:
                        # Calcular demanda con variación regional
                        factor_regional = {
                            'Caribe': 0.9,
                            'Pacifica': 0.85,
                            'Orinoquia': 0.7,
                            'Amazonia': 0.6,
                            'Andina': 1.2  # Región más poblada
                        }
                        
                        demanda_base = producto.demanda_promedio * factor_regional[region]
                        cantidad_solicitada = max(1, int(random.gauss(demanda_base, producto.desviacion_demanda)))
                        
                        # Simular disponibilidad (85-100% de cumplimiento)
                        tasa_cumplimiento = random.uniform(0.85, 1.0)
                        cantidad_vendida = int(cantidad_solicitada * tasa_cumplimiento)
                        cantidad_perdida = cantidad_solicitada - cantidad_vendida
                        
                        # Precio con pequeña variación
                        precio_unitario = producto.precio_actual * random.uniform(0.95, 1.05)
                        ingreso_total = cantidad_vendida * precio_unitario
                        margen = ((precio_unitario - producto.costo_unitario) / precio_unitario * 100) if precio_unitario > 0 else 0
                        
                        canal = random.choice(canales)
                        
                        venta = Venta(
                            empresa_id=empresa.id,
                            producto_id=producto.id,
                            dia_simulacion=dia,
                            region=region,
                            canal=canal,
                            cantidad_solicitada=cantidad_solicitada,
                            cantidad_vendida=cantidad_vendida,
                            cantidad_perdida=cantidad_perdida,
                            precio_unitario=precio_unitario,
                            ingreso_total=ingreso_total,
                            costo_unitario=producto.costo_unitario,
                            margen=margen
                        )
                        db.session.add(venta)
                        ventas_creadas += 1
        
        db.session.commit()
        print(f"✓ {ventas_creadas} registros de ventas históricas creados")
        
        print("\n" + "="*50)
        print("✅ Base de datos inicializada correctamente")
        print("="*50)
        print("\nCredenciales de acceso:")
        print("\n👨‍🏫 PROFESOR:")
        print("  Usuario: admin")
        print("  Contraseña: admin123")
        print("\n👨‍🎓 ESTUDIANTES:")
        print("  Usuario: estudiante_[1-4]_[1-3]")
        print("  Contraseña: estudiante123")
        print("\nEjemplos:")
        print("  - estudiante_1_1 (Ventas - Empresa 1)")
        print("  - estudiante_2_1 (Planeación - Empresa 1)")
        print("  - estudiante_3_2 (Compras - Empresa 2)")
        print("  - estudiante_4_3 (Logística - Empresa 3)")
        print("\n" + "="*50)

if __name__ == '__main__':
    init_db()
