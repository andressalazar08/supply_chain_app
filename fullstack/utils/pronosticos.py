"""
Funciones de pronóstico de demanda
Implementa métodos estadísticos para predicción
"""

from typing import List, Dict, Tuple


def promedio_movil(datos: List[float], n: int) -> float:
    """
    Pronóstico por Promedio Móvil Simple
    
    Args:
        datos: Lista de demandas históricas (más reciente al final)
        n: Número de períodos a promediar
    
    Returns:
        Pronóstico para el siguiente período
    """
    if len(datos) < n:
        n = len(datos)
    
    if n == 0:
        return 0.0
    
    ultimos_n = datos[-n:]
    return sum(ultimos_n) / n


def suavizacion_exponencial_simple(datos: List[float], alpha: float, pronostico_inicial: float = None) -> float:
    """
    Pronóstico por Suavización Exponencial Simple
    
    Args:
        datos: Lista de demandas históricas
        alpha: Constante de suavización (0 < alpha < 1)
        pronostico_inicial: Pronóstico inicial (si es None, usa el primer dato)
    
    Returns:
        Pronóstico para el siguiente período
    """
    if not datos:
        return 0.0
    
    if pronostico_inicial is None:
        pronostico_inicial = datos[0]
    
    pronostico = pronostico_inicial
    
    for demanda_real in datos:
        pronostico = alpha * demanda_real + (1 - alpha) * pronostico
    
    return pronostico


def suavizacion_exponencial_doble_holt(
    datos: List[float], 
    alpha: float, 
    beta: float,
    nivel_inicial: float = None,
    tendencia_inicial: float = None
) -> Tuple[float, List[float]]:
    """
    Pronóstico por Suavización Exponencial Doble de Holt
    Considera nivel y tendencia
    
    Args:
        datos: Lista de demandas históricas
        alpha: Constante de suavización de nivel (0 < alpha < 1)
        beta: Constante de suavización de tendencia (0 < beta < 1)
        nivel_inicial: Nivel inicial (si es None, usa el primer dato)
        tendencia_inicial: Tendencia inicial (si es None, calcula automáticamente)
    
    Returns:
        Tupla: (pronóstico_siguiente_periodo, lista_pronosticos_historicos)
    """
    if not datos or len(datos) < 2:
        return datos[0] if datos else 0.0, datos
    
    # Inicializar nivel y tendencia
    if nivel_inicial is None:
        nivel = datos[0]
    else:
        nivel = nivel_inicial
    
    if tendencia_inicial is None:
        # Calcular tendencia inicial como diferencia promedio de primeros períodos
        if len(datos) >= 3:
            tendencia = (datos[2] - datos[0]) / 2
        else:
            tendencia = datos[1] - datos[0]
    else:
        tendencia = tendencia_inicial
    
    pronosticos = []
    
    for demanda_real in datos:
        # Pronóstico para este período
        pronostico = nivel + tendencia
        pronosticos.append(pronostico)
        
        # Actualizar nivel
        nivel_anterior = nivel
        nivel = alpha * demanda_real + (1 - alpha) * (nivel + tendencia)
        
        # Actualizar tendencia
        tendencia = beta * (nivel - nivel_anterior) + (1 - beta) * tendencia
    
    # Pronóstico para el siguiente período
    pronostico_siguiente = nivel + tendencia
    
    return pronostico_siguiente, pronosticos


def calcular_mape(datos_reales: List[float], datos_pronosticados: List[float]) -> float:
    """
    Calcula el Mean Absolute Percentage Error (MAPE)
    
    Args:
        datos_reales: Demanda real
        datos_pronosticados: Demanda pronosticada
    
    Returns:
        MAPE en porcentaje (0-100)
    """
    if not datos_reales or not datos_pronosticados:
        return 0.0
    
    if len(datos_reales) != len(datos_pronosticados):
        # Ajustar longitud al mínimo
        min_len = min(len(datos_reales), len(datos_pronosticados))
        datos_reales = datos_reales[:min_len]
        datos_pronosticados = datos_pronosticados[:min_len]
    
    errores_porcentuales = []
    
    for real, pronostico in zip(datos_reales, datos_pronosticados):
        if real != 0:  # Evitar división por cero
            error = abs((real - pronostico) / real) * 100
            errores_porcentuales.append(error)
    
    if not errores_porcentuales:
        return 0.0
    
    return sum(errores_porcentuales) / len(errores_porcentuales)


def calcular_mad(datos_reales: List[float], datos_pronosticados: List[float]) -> float:
    """
    Calcula el Mean Absolute Deviation (MAD)
    
    Args:
        datos_reales: Demanda real
        datos_pronosticados: Demanda pronosticada
    
    Returns:
        MAD (desviación absoluta media)
    """
    if not datos_reales or not datos_pronosticados:
        return 0.0
    
    if len(datos_reales) != len(datos_pronosticados):
        min_len = min(len(datos_reales), len(datos_pronosticados))
        datos_reales = datos_reales[:min_len]
        datos_pronosticados = datos_pronosticados[:min_len]
    
    errores_absolutos = [abs(real - pronostico) for real, pronostico in zip(datos_reales, datos_pronosticados)]
    
    return sum(errores_absolutos) / len(errores_absolutos) if errores_absolutos else 0.0


def comparar_metodos(
    datos_historicos: List[float],
    metodos_config: Dict[str, Dict] = None
) -> Dict[str, Dict]:
    """
    Compara múltiples métodos de pronóstico y calcula sus errores
    
    Args:
        datos_historicos: Lista de demandas históricas
        metodos_config: Configuración de métodos a probar
    
    Returns:
        Diccionario con resultados de cada método
    """
    if not datos_historicos or len(datos_historicos) < 3:
        return {}
    
    # Configuración por defecto
    if metodos_config is None:
        metodos_config = {
            'promedio_movil_3': {'n': 3},
            'promedio_movil_5': {'n': 5},
            'exp_simple_03': {'alpha': 0.3},
            'exp_simple_05': {'alpha': 0.5},
            'exp_simple_07': {'alpha': 0.7},
            'holt_03_02': {'alpha': 0.3, 'beta': 0.2},
            'holt_05_03': {'alpha': 0.5, 'beta': 0.3},
        }
    
    resultados = {}
    
    # Dividir datos: usar los primeros n-1 para entrenar, último para validar
    datos_entrenamiento = datos_historicos[:-1]
    dato_validacion = datos_historicos[-1]
    
    for nombre_metodo, config in metodos_config.items():
        try:
            if 'promedio_movil' in nombre_metodo:
                n = config.get('n', 3)
                pronostico = promedio_movil(datos_entrenamiento, n)
                
                # Calcular pronósticos históricos para MAPE/MAD
                pronosticos_historicos = []
                for i in range(n, len(datos_entrenamiento)):
                    p = promedio_movil(datos_entrenamiento[:i], n)
                    pronosticos_historicos.append(p)
                
                datos_reales_comparacion = datos_entrenamiento[n:]
                
            elif 'exp_simple' in nombre_metodo:
                alpha = config.get('alpha', 0.5)
                pronostico = suavizacion_exponencial_simple(datos_entrenamiento, alpha)
                
                # Calcular pronósticos históricos
                pronosticos_historicos = []
                for i in range(1, len(datos_entrenamiento)):
                    p = suavizacion_exponencial_simple(datos_entrenamiento[:i], alpha)
                    pronosticos_historicos.append(p)
                
                datos_reales_comparacion = datos_entrenamiento[1:]
                
            elif 'holt' in nombre_metodo:
                alpha = config.get('alpha', 0.5)
                beta = config.get('beta', 0.3)
                pronostico, pronosticos_historicos = suavizacion_exponencial_doble_holt(
                    datos_entrenamiento, alpha, beta
                )
                datos_reales_comparacion = datos_entrenamiento
            
            else:
                continue
            
            # Calcular errores
            mape = calcular_mape(datos_reales_comparacion, pronosticos_historicos)
            mad = calcular_mad(datos_reales_comparacion, pronosticos_historicos)
            
            # Error del último pronóstico vs dato real
            error_validacion = abs(pronostico - dato_validacion)
            error_validacion_pct = (error_validacion / dato_validacion * 100) if dato_validacion > 0 else 0
            
            resultados[nombre_metodo] = {
                'pronostico': round(pronostico, 2),
                'mape': round(mape, 2),
                'mad': round(mad, 2),
                'error_validacion': round(error_validacion, 2),
                'error_validacion_pct': round(error_validacion_pct, 2),
                'parametros': config
            }
        
        except Exception as e:
            print(f"Error en método {nombre_metodo}: {str(e)}")
            continue
    
    return resultados


def obtener_mejor_metodo(resultados_comparacion: Dict[str, Dict], criterio: str = 'mape') -> Tuple[str, Dict]:
    """
    Determina el mejor método según el criterio especificado
    
    Args:
        resultados_comparacion: Resultados de comparar_metodos()
        criterio: 'mape' o 'mad'
    
    Returns:
        Tupla: (nombre_mejor_metodo, datos_mejor_metodo)
    """
    if not resultados_comparacion:
        return None, {}
    
    mejor_metodo = None
    menor_error = float('inf')
    
    for nombre, datos in resultados_comparacion.items():
        error = datos.get(criterio, float('inf'))
        
        if error < menor_error:
            menor_error = error
            mejor_metodo = nombre
    
    if mejor_metodo:
        return mejor_metodo, resultados_comparacion[mejor_metodo]
    
    return None, {}


def calcular_cantidad_pedir(
    demanda_pronosticada: float,
    stock_actual: float,
    stock_seguridad: float,
    lead_time: int,
    demanda_promedio_diaria: float = None
) -> Dict[str, float]:
    """
    Calcula la cantidad óptima a pedir
    
    Args:
        demanda_pronosticada: Demanda esperada para el período
        stock_actual: Inventario actual disponible
        stock_seguridad: Stock de seguridad deseado
        lead_time: Tiempo de entrega en días
        demanda_promedio_diaria: Demanda promedio por día (opcional)
    
    Returns:
        Diccionario con cálculos detallados
    """
    if demanda_promedio_diaria is None:
        demanda_promedio_diaria = demanda_pronosticada
    
    # Demanda durante el lead time
    demanda_lead_time = demanda_promedio_diaria * lead_time
    
    # Punto de reorden = Demanda durante lead time + Stock de seguridad
    punto_reorden = demanda_lead_time + stock_seguridad
    
    # Cantidad a pedir = Demanda pronosticada + Stock seguridad - Stock actual
    # Asegurar que no sea negativo
    cantidad_sugerida = max(0, demanda_pronosticada + stock_seguridad - stock_actual)
    
    # Stock proyectado después de recibir el pedido
    stock_proyectado = stock_actual + cantidad_sugerida
    
    # Días de cobertura
    dias_cobertura = (stock_proyectado / demanda_promedio_diaria) if demanda_promedio_diaria > 0 else 0
    
    return {
        'cantidad_sugerida': round(cantidad_sugerida, 2),
        'punto_reorden': round(punto_reorden, 2),
        'demanda_lead_time': round(demanda_lead_time, 2),
        'stock_proyectado': round(stock_proyectado, 2),
        'dias_cobertura': round(dias_cobertura, 1),
        'requiere_pedido': cantidad_sugerida > 0
    }
