from app import app
from models import Simulacion, DemandaMercadoDiaria, Producto
from sqlalchemy import func

orden = ['Andina', 'Caribe', 'Pacífica', 'Orinoquía', 'Amazonía']
dias = [1, 2, 7, 15, 40, 80]

with app.app_context():
    sim = Simulacion.query.filter_by(activa=True).first()
    producto = Producto.query.filter_by(activo=True).first()

    print('simulacion', sim.id if sim else None)
    print('producto', producto.codigo if producto else None)

    for dia in dias:
        valores = {}
        for region in orden:
            valores[region] = (
                DemandaMercadoDiaria.query.with_entities(func.sum(DemandaMercadoDiaria.demanda_base))
                .filter_by(
                    simulacion_id=sim.id,
                    dia_simulacion=dia,
                    producto_id=producto.id,
                    region=region,
                )
                .scalar()
                or 0
            )

        jerarquia_ok = (
            valores['Andina']
            > valores['Caribe']
            > valores['Pacífica']
            > valores['Orinoquía']
            > valores['Amazonía']
        )
        print(f"dia {dia}: {valores} | jerarquia_ok={jerarquia_ok}")
