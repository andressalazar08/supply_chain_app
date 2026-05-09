"""
Migración: agrega columnas demanda_mercado_total (ventas) y market_share (metricas).
Ejecutar una sola vez: python migrate_market_kpis.py
"""
from app import app, db

ADD_VENTAS_COL = """
ALTER TABLE ventas ADD COLUMN demanda_mercado_total REAL DEFAULT 0;
"""

ADD_METRICAS_COL = """
ALTER TABLE metricas ADD COLUMN market_share REAL DEFAULT 0;
"""

with app.app_context():
    with db.engine.connect() as conn:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)

        cols_ventas = [c['name'] for c in inspector.get_columns('ventas')]
        if 'demanda_mercado_total' not in cols_ventas:
            conn.execute(text(ADD_VENTAS_COL))
            conn.commit()
            print("✅ Columna demanda_mercado_total agregada a ventas")
        else:
            print("ℹ️  demanda_mercado_total ya existe en ventas")

        cols_metricas = [c['name'] for c in inspector.get_columns('metricas')]
        if 'market_share' not in cols_metricas:
            conn.execute(text(ADD_METRICAS_COL))
            conn.commit()
            print("✅ Columna market_share agregada a metricas")
        else:
            print("ℹ️  market_share ya existe en metricas")

    print("\nMigración completada.")
