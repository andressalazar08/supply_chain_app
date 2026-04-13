"""
Utilidades para generar, validar e intercambiar la base central de demanda diaria.
"""

from __future__ import annotations

import csv
import io
import random
from typing import Dict, List, Tuple

from models import DemandaMercadoDiaria, Producto
from utils.catalogo_disrupciones import CATALOGO_DISRUPCIONES


REGIONES_PESO = {
    'Andina': 0.42,
    'Caribe': 0.24,
    'Pacífica': 0.16,
    'Orinoquía': 0.11,
    'Amazonía': 0.07,
}

REGIONES_ORDEN = list(REGIONES_PESO.keys())


def _rango_disrupcion_aumento_demanda() -> Tuple[int, int, float]:
    """Obtiene ventana (inicio, fin) y multiplicador base para la disrupción de aumento de demanda."""
    dis = next((d for d in CATALOGO_DISRUPCIONES if d.get('key') == 'aumento_demanda'), None)
    if not dis:
        return (0, -1, 1.0)

    semana_trigger = int(dis.get('semana_trigger', 0))
    duracion_semanas = int(dis.get('duracion_semanas', 0))
    inicio_dia = (semana_trigger - 1) * 7 + 1
    fin_dia = inicio_dia + max(0, duracion_semanas * 7) - 1

    # Base de mercado: se usa opción B (+15%) como nivel prudente por defecto.
    multiplicador = (
        dis.get('opciones', {})
        .get('B', {})
        .get('efectos', {})
        .get('demanda_multiplicador', 1.15)
    )
    return (inicio_dia, fin_dia, float(multiplicador))


def _factor_disrupcion(dia_simulacion: int) -> Tuple[str, float]:
    """Retorna (disrupcion_key, multiplicador) para un día de simulación."""
    if dia_simulacion <= 0:
        return (None, 1.0)

    inicio, fin, mult = _rango_disrupcion_aumento_demanda()
    if inicio <= dia_simulacion <= fin:
        return ('aumento_demanda', mult)
    return (None, 1.0)


def _generar_demanda_regional(producto_id: int, dia_simulacion: int, disrupcion_mult: float) -> Dict[str, int]:
    """
    Genera demanda diaria por región con estas reglas:
    - Días típicos: 20-60 unidades por producto/región.
    - Días atípicos ocasionales: por debajo de 20 o por encima de 60.
    - Jerarquía regional: Andina > Caribe > Pacífica > Orinoquía > Amazonía.
    - Variabilidad no lineal entre días.
    """
    rng = random.Random(f"demanda-regional:{producto_id}:{dia_simulacion}")

    # Base descendente realista con brechas variables (no lineales).
    andina = rng.randint(46, 58)
    caribe = andina - rng.randint(3, 10)
    pacifica = caribe - rng.randint(2, 8)
    orinoquia = pacifica - rng.randint(2, 7)
    amazonia = orinoquia - rng.randint(2, 6)

    valores = {
        'Andina': andina,
        'Caribe': caribe,
        'Pacífica': pacifica,
        'Orinoquía': orinoquia,
        'Amazonía': amazonia,
    }

    # Patrón semanal suave + tendencia moderada + disrupción de mercado.
    patron_semana = [1.05, 0.98, 1.01, 0.96, 1.08, 0.93, 0.90]
    idx = (abs(dia_simulacion) - 1) % 7 if dia_simulacion != 0 else 0
    estacional = patron_semana[idx]
    tendencia = 1.0 + (0.0007 * max(0, dia_simulacion))
    factor_global = estacional * tendencia * disrupcion_mult

    # Días atípicos: pocos días con caídas fuertes o picos altos.
    outlier = None
    chance = rng.random()
    if chance < 0.08:
        outlier = 'bajo'
        factor_global *= rng.uniform(0.40, 0.75)
    elif chance < 0.16:
        outlier = 'alto'
        factor_global *= rng.uniform(1.25, 1.75)

    # Aplicar variación por región sin perder orden.
    for region in REGIONES_ORDEN:
        jitter = rng.uniform(-0.10, 0.10)
        valores[region] = int(round(valores[region] * factor_global * (1.0 + jitter)))

    # Rango típico por defecto.
    minimo, maximo = 20, 60

    # En días atípicos permitimos rangos extendidos.
    if outlier == 'bajo':
        minimo, maximo = 6, 45
    elif outlier == 'alto':
        minimo, maximo = 25, 95

    for region in REGIONES_ORDEN:
        valores[region] = max(minimo, min(maximo, valores[region]))

    # Reforzar jerarquía estricta: Andina > Caribe > Pacífica > Orinoquía > Amazonía.
    for i in range(1, len(REGIONES_ORDEN)):
        superior = REGIONES_ORDEN[i - 1]
        actual = REGIONES_ORDEN[i]
        if valores[actual] >= valores[superior]:
            valores[actual] = max(minimo, valores[superior] - rng.randint(1, 4))

    # Ajuste final: evitar igualdad en cadena por efecto de límites.
    for i in range(1, len(REGIONES_ORDEN)):
        superior = REGIONES_ORDEN[i - 1]
        actual = REGIONES_ORDEN[i]
        if valores[actual] >= valores[superior]:
            valores[actual] = max(minimo, valores[superior] - 1)

    return valores


def generar_base_demanda_simulacion(simulacion, dias_historico: int = 30, replace: bool = True) -> Tuple[bool, str]:
    """Genera la base central de demanda para histórico + horizonte de simulación."""
    productos = Producto.query.filter_by(activo=True).all()
    if not productos:
        return (False, 'No hay productos activos para generar demanda central.')

    if replace:
        DemandaMercadoDiaria.query.filter_by(simulacion_id=simulacion.id).delete()

    total_dias = int(simulacion.duracion_semanas or 0) * 7
    if total_dias <= 0:
        return (False, 'La simulación no tiene duración válida para construir la demanda.')

    registros = []
    for dia in range(-abs(dias_historico), total_dias + 1):
        if dia == 0:
            continue
        for producto in productos:
            dis_key, dis_mult = _factor_disrupcion(dia)
            demanda_regional = _generar_demanda_regional(producto.id, dia, dis_mult)

            for region, cantidad in demanda_regional.items():
                registros.append(DemandaMercadoDiaria(
                    simulacion_id=simulacion.id,
                    dia_simulacion=dia,
                    producto_id=producto.id,
                    region=region,
                    demanda_base=int(cantidad),
                    disrupcion_key=dis_key,
                    multiplicador_disrupcion=dis_mult,
                    fuente='sistema',
                ))

    if registros:
        from extensions import db

        db.session.bulk_save_objects(registros)
        db.session.flush()

    combos = len(productos) * len(REGIONES_ORDEN)
    dias_generados = dias_historico + total_dias
    return (True, f'Demanda central generada: {len(registros)} registros ({dias_generados} días x {combos} combinaciones).')


def obtener_demanda_base(simulacion_id: int, dia_simulacion: int, producto_id: int, region: str) -> int:
    """Obtiene demanda base central para un día/producto/región."""
    row = DemandaMercadoDiaria.query.filter_by(
        simulacion_id=simulacion_id,
        dia_simulacion=dia_simulacion,
        producto_id=producto_id,
        region=region,
    ).first()
    return int(row.demanda_base) if row else 0


def validar_cobertura_demanda_dia(simulacion_id: int, dia_simulacion: int) -> Tuple[bool, str]:
    """Valida que exista demanda central completa para un día concreto."""
    productos = Producto.query.filter_by(activo=True).count()
    esperado = productos * len(REGIONES_ORDEN)

    actual = DemandaMercadoDiaria.query.filter_by(
        simulacion_id=simulacion_id,
        dia_simulacion=dia_simulacion,
    ).count()

    if actual < esperado:
        return (False, f'Demanda central incompleta para día {dia_simulacion}: {actual}/{esperado} registros.')
    return (True, 'Cobertura de demanda diaria OK.')


def exportar_demanda_csv(simulacion_id: int) -> str:
    """Exporta la base central de demanda a CSV en texto UTF-8."""
    filas = DemandaMercadoDiaria.query.filter_by(simulacion_id=simulacion_id).order_by(
        DemandaMercadoDiaria.dia_simulacion,
        DemandaMercadoDiaria.producto_id,
        DemandaMercadoDiaria.region,
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'dia_simulacion', 'producto_codigo', 'producto_id', 'region',
        'demanda_base', 'disrupcion_key', 'multiplicador_disrupcion', 'fuente'
    ])

    for f in filas:
        codigo = f.producto.codigo if f.producto else ''
        writer.writerow([
            f.dia_simulacion,
            codigo,
            f.producto_id,
            f.region,
            int(f.demanda_base),
            f.disrupcion_key or '',
            float(f.multiplicador_disrupcion or 1.0),
            f.fuente or 'admin',
        ])

    return output.getvalue()


def _parse_int(value, field_name: str) -> int:
    try:
        return int(str(value).strip())
    except Exception as exc:
        raise ValueError(f'Valor inválido en {field_name}: {value}') from exc


def _parse_float(value, field_name: str) -> float:
    try:
        return float(str(value).strip())
    except Exception as exc:
        raise ValueError(f'Valor inválido en {field_name}: {value}') from exc


def importar_demanda_csv(simulacion, file_storage, min_historico: int = 30) -> Tuple[bool, str]:
    """Valida e importa una base de demanda subida por administrador."""
    raw = file_storage.read()
    if not raw:
        return (False, 'El archivo está vacío.')

    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return (False, 'El archivo debe estar codificado en UTF-8.')

    reader = csv.DictReader(io.StringIO(text))
    required = {'dia_simulacion', 'region', 'demanda_base'}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        return (False, 'El CSV debe incluir columnas: dia_simulacion, region, demanda_base y producto_codigo o producto_id.')

    productos = Producto.query.filter_by(activo=True).all()
    by_id = {p.id: p for p in productos}
    by_codigo = {p.codigo: p for p in productos}

    if not productos:
        return (False, 'No hay productos activos para asociar la demanda.')

    total_dias = int(simulacion.duracion_semanas or 0) * 7
    if total_dias <= 0:
        return (False, 'La simulación no tiene duración válida.')

    rows: List[DemandaMercadoDiaria] = []
    seen = set()
    dias_presentes = set()

    for idx, row in enumerate(reader, start=2):
        try:
            dia = _parse_int(row.get('dia_simulacion'), 'dia_simulacion')
            region = (row.get('region') or '').strip()
            demanda = _parse_int(row.get('demanda_base'), 'demanda_base')
            if demanda < 0:
                raise ValueError('demanda_base no puede ser negativa')

            producto = None
            producto_id_raw = (row.get('producto_id') or '').strip()
            producto_codigo_raw = (row.get('producto_codigo') or '').strip()

            if producto_id_raw:
                pid = _parse_int(producto_id_raw, 'producto_id')
                producto = by_id.get(pid)
            elif producto_codigo_raw:
                producto = by_codigo.get(producto_codigo_raw)

            if not producto:
                raise ValueError('producto no identificado por producto_id/producto_codigo')

            if region not in REGIONES_ORDEN:
                raise ValueError(f'región inválida: {region}')

            if dia == 0 or dia < -365 or dia > total_dias:
                raise ValueError('dia_simulacion fuera de rango permitido')

            dis_key = (row.get('disrupcion_key') or '').strip() or None
            mult = _parse_float(row.get('multiplicador_disrupcion') or 1.0, 'multiplicador_disrupcion')

            key = (dia, producto.id, region)
            if key in seen:
                raise ValueError('fila duplicada para dia/producto/región')

            seen.add(key)
            dias_presentes.add(dia)

            rows.append(DemandaMercadoDiaria(
                simulacion_id=simulacion.id,
                dia_simulacion=dia,
                producto_id=producto.id,
                region=region,
                demanda_base=demanda,
                disrupcion_key=dis_key,
                multiplicador_disrupcion=mult,
                fuente='admin',
            ))
        except ValueError as exc:
            return (False, f'Error en fila {idx}: {exc}')

    # Validación de cobertura mínima obligatoria.
    if not any(d < 0 for d in dias_presentes):
        return (False, 'El archivo debe incluir histórico (días negativos).')

    min_dia = min(dias_presentes)
    if min_dia > -min_historico:
        return (False, f'El histórico debe cubrir al menos {min_historico} días (hasta día -{min_historico}).')

    dias_positivos = {d for d in dias_presentes if d > 0}
    esperados_positivos = set(range(1, total_dias + 1))
    if not esperados_positivos.issubset(dias_positivos):
        faltantes = sorted(list(esperados_positivos - dias_positivos))[:10]
        return (False, f'Faltan días de simulación en CSV. Primeros faltantes: {faltantes}')

    combinaciones_esperadas = len(productos) * len(REGIONES_ORDEN)
    conteo_por_dia: Dict[int, int] = {}
    for dia, _, _ in seen:
        conteo_por_dia[dia] = conteo_por_dia.get(dia, 0) + 1

    for dia, count in conteo_por_dia.items():
        if count != combinaciones_esperadas:
            return (False, f'Cobertura incompleta en día {dia}: {count}/{combinaciones_esperadas} combinaciones.')

    from extensions import db

    DemandaMercadoDiaria.query.filter_by(simulacion_id=simulacion.id).delete()
    db.session.bulk_save_objects(rows)
    db.session.flush()

    return (True, f'Base de demanda importada correctamente ({len(rows)} filas).')
