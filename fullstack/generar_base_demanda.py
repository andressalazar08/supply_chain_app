"""Genera la base central de demanda para la simulación activa."""

from app import app
from extensions import db
from models import Simulacion, DemandaMercadoDiaria
from utils.demanda_central import generar_base_demanda_simulacion
from utils.parametros_iniciales import DIAS_HISTORICO_DEMANDA


with app.app_context():
    simulacion = Simulacion.query.filter_by(activa=True).first()

    if not simulacion:
        print("No hay simulación activa.")
        raise SystemExit(1)

    ok, mensaje = generar_base_demanda_simulacion(
        simulacion,
        dias_historico=DIAS_HISTORICO_DEMANDA,
        replace=True,
    )

    if not ok:
        db.session.rollback()
        print(f"Error: {mensaje}")
        raise SystemExit(1)

    db.session.commit()

    total = DemandaMercadoDiaria.query.filter_by(simulacion_id=simulacion.id).count()
    print(f"Simulación: {simulacion.id} - {simulacion.nombre}")
    print(mensaje)
    print(f"Total filas: {total}")
