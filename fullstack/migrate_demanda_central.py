"""
Migración: crea la tabla demanda_mercado_diaria si no existe.
Ejecutar una sola vez: python migrate_demanda_central.py
"""

from sqlalchemy import inspect, text

from app import app, db

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS demanda_mercado_diaria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacion_id INTEGER NOT NULL,
    dia_simulacion INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    region VARCHAR(50) NOT NULL,
    demanda_base INTEGER NOT NULL DEFAULT 0,
    disrupcion_key VARCHAR(50),
    multiplicador_disrupcion REAL DEFAULT 1.0,
    fuente VARCHAR(20) DEFAULT 'sistema',
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(simulacion_id) REFERENCES simulacion(id),
    FOREIGN KEY(producto_id) REFERENCES productos(id),
    UNIQUE(simulacion_id, dia_simulacion, producto_id, region)
);
"""


with app.app_context():
    with db.engine.connect() as conn:
        inspector = inspect(db.engine)
        tablas = inspector.get_table_names()

        if 'demanda_mercado_diaria' not in tablas:
            conn.execute(text(CREATE_TABLE_SQL))
            conn.commit()
            print('✅ Tabla demanda_mercado_diaria creada.')
        else:
            print('ℹ️  La tabla demanda_mercado_diaria ya existe.')

    print('Migración completada.')
