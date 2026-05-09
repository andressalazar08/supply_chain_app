#!/usr/bin/env python
"""Restaurar los datos iniciales del simulador.

 Este script crea, de forma idempotente:
- el catalogo base de productos,
- empresas de ejemplo,
- los tres usuarios de demo solicitados,
- y luego reinicia la simulacion para generar inventarios,
  demanda central e historico inicial.

Uso:
    python seed_datos_iniciales.py
"""

from werkzeug.security import generate_password_hash

from app import app
from extensions import db
from models import Empresa, Producto, Simulacion, Usuario
from utils.parametros_iniciales import CATALOGO_PRODUCTOS_BASE
from utils.reinicio_simulacion import reiniciar_simulacion


PRODUCTOS_BASE = [
    {
        "codigo": "SV-750",
        "nombre": "Sangre de la Vid 750ml",
        "categoria": "Vinos",
        "tiempo_entrega": 1,
    },
    {
        "codigo": "SV-1L",
        "nombre": "Sangre de la Vid 1L",
        "categoria": "Vinos",
        "tiempo_entrega": 1,
    },
    {
        "codigo": "ED-750",
        "nombre": "Elixir Dorado 750ml",
        "categoria": "Vinos",
        "tiempo_entrega": 1,
    },
    {
        "codigo": "ED-1L",
        "nombre": "Elixir Dorado 1L",
        "categoria": "Vinos",
        "tiempo_entrega": 1,
    },
    {
        "codigo": "SR-750",
        "nombre": "Susurro Rosado 750ml",
        "categoria": "Vinos",
        "tiempo_entrega": 1,
    },
    {
        "codigo": "SR-1L",
        "nombre": "Susurro Rosado 1L",
        "categoria": "Vinos",
        "tiempo_entrega": 1,
    },
    {
        "codigo": "OP-750",
        "nombre": "Océano Profundo 750ml",
        "categoria": "Vinos",
        "tiempo_entrega": 1,
    },
    {
        "codigo": "OP-1L",
        "nombre": "Océano Profundo 1L",
        "categoria": "Vinos",
        "tiempo_entrega": 1,
    },
]

EMPRESAS_DEMO = [
    "Empresa Andina",
    "Empresa Caribe",
    "Empresa Pacifica",
]

USUARIOS_DEMO = [
    ("estudiante_ventas", "ventas"),
    ("estudiante_compras", "compras"),
    ("estudiante_logistica", "logistica"),
]
PASSWORD_DEMO = "student123"


def _asegurar_productos():
    creados = 0
    for producto_data in PRODUCTOS_BASE:
        producto = Producto.query.filter_by(codigo=producto_data["codigo"]).first()
        base = CATALOGO_PRODUCTOS_BASE.get(producto_data["codigo"], {})

        if producto:
            producto.nombre = producto_data["nombre"]
            producto.categoria = producto_data["categoria"]
            producto.precio_base = float(base.get("precio_base", producto.precio_base or 0))
            producto.precio_actual = float(base.get("precio_base", producto.precio_actual or 0))
            producto.precio_sugerido = float(base.get("precio_base", producto.precio_sugerido or 0))
            producto.costo_unitario = float(base.get("costo_unitario", producto.costo_unitario or 0))
            producto.tiempo_entrega = producto_data["tiempo_entrega"]
            producto.activo = True
            continue

        producto = Producto(
            codigo=producto_data["codigo"],
            nombre=producto_data["nombre"],
            categoria=producto_data["categoria"],
            precio_base=float(base["precio_base"]),
            precio_actual=float(base["precio_base"]),
            precio_sugerido=float(base["precio_base"]),
            costo_unitario=float(base["costo_unitario"]),
            demanda_promedio=100,
            desviacion_demanda=20,
            elasticidad_precio=1.5,
            tiempo_entrega=producto_data["tiempo_entrega"],
            stock_maximo=1500,
            activo=True,
        )
        db.session.add(producto)
        creados += 1

    db.session.commit()
    return creados


def _asegurar_simulacion_activa():
    simulacion = Simulacion.query.filter_by(activa=True).first()
    if simulacion:
        return simulacion

    simulacion = Simulacion(
        nombre="Simulacion 1",
        semana_actual=1,
        dia_actual=1,
        estado="pausado",
        activa=True,
        duracion_semanas=8,
        capital_inicial_empresas=50_000_000.0,
    )
    db.session.add(simulacion)
    db.session.commit()
    return simulacion


def _asegurar_empresas_y_estudiantes(simulacion, admin):
    empresas = []
    empresa_demo = None
    for idx, nombre_empresa in enumerate(EMPRESAS_DEMO, start=1):
        empresa = Empresa.query.filter_by(nombre=nombre_empresa).first()
        if not empresa:
            empresa = Empresa(
                nombre=nombre_empresa,
                capital_inicial=50_000_000.0,
                capital_actual=50_000_000.0,
                activa=True,
                profesor_id=admin.id,
                simulacion_id=simulacion.id,
            )
            db.session.add(empresa)
            db.session.flush()
        else:
            empresa.activa = True
            empresa.profesor_id = admin.id
            empresa.simulacion_id = simulacion.id
            if not empresa.capital_inicial or empresa.capital_inicial < 1_000_000:
                empresa.capital_inicial = 50_000_000.0
            if not empresa.capital_actual or empresa.capital_actual < 1_000_000:
                empresa.capital_actual = 50_000_000.0

        empresas.append(empresa)
        if empresa_demo is None:
            empresa_demo = empresa

    Usuario.query.filter(
        Usuario.tipo_usuario == "estudiante",
        ~Usuario.username.in_([username for username, _ in USUARIOS_DEMO]),
    ).delete(synchronize_session=False)

    db.session.flush()

    for idx, (username, rol) in enumerate(USUARIOS_DEMO, start=1):
        email = f"{username}@erpeducativo.com"
        estudiante = Usuario.query.filter_by(username=username).first()
        if estudiante:
            estudiante.nombre_completo = f"{rol.title()} Demo"
            estudiante.email = email
            estudiante.password = generate_password_hash(PASSWORD_DEMO)
            estudiante.tipo_usuario = "estudiante"
            estudiante.rol = rol
            estudiante.empresa_id = empresa_demo.id if empresa_demo else None
            estudiante.profesor_id = admin.id
            estudiante.activo = True
            estudiante.email_verified = True
            estudiante.universidad = "Universidad Demo"
            estudiante.sede = "Principal"
            estudiante.carrera = "Administracion"
            estudiante.codigo_estudiante = f"DEMO{idx:02d}"
            continue

        estudiante = Usuario(
            username=username,
            password=generate_password_hash(PASSWORD_DEMO),
            rol=rol,
            tipo_usuario="estudiante",
            empresa_id=empresa_demo.id if empresa_demo else None,
            nombre_completo=f"{rol.title()} Demo",
            email=email,
            activo=True,
            email_verified=True,
            universidad="Universidad Demo",
            sede="Principal",
            carrera="Administracion",
            codigo_estudiante=f"DEMO{idx:02d}",
            profesor_id=admin.id,
        )
        db.session.add(estudiante)

    db.session.commit()
    return empresas


def main():
    with app.app_context():
        db.create_all()

        admin = Usuario.query.filter_by(username="admin").first()
        if not admin:
            admin = Usuario(
                username="admin",
                password=generate_password_hash("admin123"),
                rol="admin",
                tipo_usuario="profesor",
                es_super_admin=True,
                nombre_completo="Administrador del Sistema",
                email="admin@erpeducativo.com",
                activo=True,
                email_verified=True,
            )
            db.session.add(admin)
            db.session.commit()

        productos_creados = _asegurar_productos()
        simulacion = _asegurar_simulacion_activa()
        empresas = _asegurar_empresas_y_estudiantes(simulacion, admin)

        nueva_simulacion, mensaje = reiniciar_simulacion(
            capital_inicial=50_000_000.0,
            nombre_simulacion="Simulacion 1",
            inv_750ml=120,
            inv_1l=80,
        )

        if not nueva_simulacion:
            raise RuntimeError(mensaje)

        print("Datos iniciales restaurados correctamente")
        print(f"Productos creados o actualizados: {productos_creados}")
        print(f"Empresas disponibles: {len(empresas)}")
        print(f"Simulacion activa: {nueva_simulacion.id} - {nueva_simulacion.nombre}")
        print(mensaje)
        print("Credenciales demo:")
        print("- Admin: admin / admin123")
        print("- Estudiantes: usuario = <empresa>_<rol>, password = student123")


if __name__ == "__main__":
    main()