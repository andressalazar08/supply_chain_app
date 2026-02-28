"""
Migración: renombrar columnas dia_* → semana_* en la base de datos SQLite
y eliminar tablas obsoletas (disrupcion_activa, escenario)
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'supply_chain.db')

RENAMES = [
    # (tabla, columna_vieja, columna_nueva)
    ('simulacion',            'dia_actual',            'semana_actual'),
    ('simulacion',            'duracion_dias',          'duracion_semanas'),
    ('ventas',                'dia_simulacion',         'semana_simulacion'),
    ('compras',               'dia_orden',              'semana_orden'),
    ('compras',               'dia_entrega',            'semana_entrega'),
    ('metricas',              'dia_simulacion',         'semana_simulacion'),
    ('movimientos_inventario','dia_simulacion',         'semana_simulacion'),
    ('despachos_regionales',  'dia_despacho',           'semana_despacho'),
    ('despachos_regionales',  'dia_entrega_estimado',   'semana_entrega_estimado'),
    ('despachos_regionales',  'dia_entrega_real',       'semana_entrega_real'),
    ('pronosticos',           'dia_generacion',         'semana_generacion'),
    ('pronosticos',           'dia_pronostico',         'semana_pronostico'),
    ('requerimientos_compra', 'dia_necesidad',          'semana_necesidad'),
]

DROP_TABLES = ['disrupciones_activas', 'escenarios']


def get_columns(cursor, table):
    cursor.execute(f'PRAGMA table_info("{table}")')
    return [row[1] for row in cursor.fetchall()]


def get_tables(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [row[0] for row in cursor.fetchall()]


def run_migration():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    existing_tables = get_tables(c)
    print(f"Tablas en DB: {existing_tables}\n")

    # Renombrar columnas
    for table, old_col, new_col in RENAMES:
        if table not in existing_tables:
            print(f"  [SKIP] Tabla '{table}' no existe")
            continue
        cols = get_columns(c, table)
        if old_col not in cols:
            if new_col in cols:
                print(f"  [OK]   {table}.{new_col} ya existe")
            else:
                print(f"  [WARN] {table}.{old_col} no encontrada")
            continue
        c.execute(f'ALTER TABLE "{table}" RENAME COLUMN "{old_col}" TO "{new_col}"')
        print(f"  [DONE] {table}.{old_col} → {new_col}")

    # Eliminar tablas obsoletas
    print()
    for table in DROP_TABLES:
        if table in existing_tables:
            c.execute(f'DROP TABLE IF EXISTS "{table}"')
            print(f"  [DROP] Tabla '{table}' eliminada")
        else:
            print(f"  [SKIP] Tabla '{table}' no existe")

    conn.commit()
    conn.close()
    print("\n✅ Migración completada.")


if __name__ == '__main__':
    run_migration()
