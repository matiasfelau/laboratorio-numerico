"""Método de integración numérica por muestreo Montecarlo.

Estimación de integral definida:
I = volumen * promedio(f(x_i)), con x_i ~ U(D).
"""

from __future__ import annotations

from statistics import NormalDist

import numpy as np

from utils.parametros import resolver_config
from .integracion_utils import validar_intervalo, validar_subintervalos


def _evaluar_muestra(f, punto: np.ndarray, etiqueta: str) -> float:
    """Evalúa la función en una muestra y valida salida real finita."""
    try:
        value = f(punto)
        numeric = complex(value)
    except Exception as exc:
        raise ValueError(f"La función evaluada en {etiqueta} no produjo un valor numérico.") from exc

    if abs(numeric.imag) > 1e-12:
        raise ValueError(f"La función evaluada en {etiqueta} produjo un valor complejo.")

    real_value = float(numeric.real)
    if not np.isfinite(real_value):
        raise ValueError(f"La función evaluada en {etiqueta} no es un número finito.")

    return real_value


def montecarlo(
    f,
    limites_inferiores: np.ndarray,
    limites_superiores: np.ndarray,
    n_muestras: int,
    ic_porcentaje: float = 95.0,
    semilla: int | None = None,
    segunda_funcion=None,
    modo: str = "dominio",
) -> None:
    """Ejecuta integración por Montecarlo y emite salida para la UI."""
    config = resolver_config()
    precision = config.precision

    validar_subintervalos(n_muestras, minimo=1)

    limites_inferiores = np.asarray(limites_inferiores, dtype=float)
    limites_superiores = np.asarray(limites_superiores, dtype=float)

    if limites_inferiores.shape != limites_superiores.shape:
        raise ValueError("Los límites inferiores y superiores deben tener la misma cantidad de dimensiones.")

    if limites_inferiores.size < 1:
        raise ValueError("Debes ingresar al menos una dimensión de integración.")

    for idx, (a_i, b_i) in enumerate(zip(limites_inferiores, limites_superiores), start=1):
        validar_intervalo(float(a_i), float(b_i))
        if float(b_i) < float(a_i):
            raise ValueError(f"En la dimensión {idx}, el límite superior debe ser mayor que el inferior.")

    dimension = int(limites_inferiores.size)
    modo_normalizado = str(modo or "dominio").strip().lower()

    if modo_normalizado == "entre_curvas":
        if dimension != 1:
            raise ValueError("El cálculo de área entre curvas requiere un único intervalo [a,b].")
        if segunda_funcion is None:
            raise ValueError("Debes ingresar una segunda función para calcular área entre curvas.")

        a = float(limites_inferiores[0])
        b = float(limites_superiores[0])
        rng = np.random.default_rng(semilla)
        x_muestras = rng.uniform(a, b, size=n_muestras)

        f_values = np.asarray(
            [_evaluar_muestra(f, np.asarray([xv], dtype=float), f"muestra f {i + 1}") for i, xv in enumerate(x_muestras)],
            dtype=float,
        )
        g_values = np.asarray(
            [
                _evaluar_muestra(segunda_funcion, np.asarray([xv], dtype=float), f"muestra g {i + 1}")
                for i, xv in enumerate(x_muestras)
            ],
            dtype=float,
        )

        y_min = float(min(np.min(f_values), np.min(g_values)))
        y_max = float(max(np.max(f_values), np.max(g_values)))
        if abs(y_max - y_min) < 1e-12:
            y_min -= 1.0
            y_max += 1.0

        y_muestras = rng.uniform(y_min, y_max, size=n_muestras)

        inferiores = np.minimum(f_values, g_values)
        superiores = np.maximum(f_values, g_values)
        mascara_favorable = (y_muestras >= inferiores) & (y_muestras <= superiores)

        casos_favorables = int(np.count_nonzero(mascara_favorable))
        casos_totales = int(n_muestras)

        rect_area = float((b - a) * (y_max - y_min))
        prob_hat = casos_favorables / max(casos_totales, 1)

        estimacion = rect_area * prob_hat
        desviacion_estandar = rect_area * float(np.sqrt(max(prob_hat * (1.0 - prob_hat), 0.0)))
        error_estandar = desviacion_estandar / np.sqrt(n_muestras)

        z_critico = NormalDist().inv_cdf(0.5 + ic_porcentaje / 200.0)
        margen_error_estimacion = z_critico * error_estandar
        ic_estimacion_inferior = estimacion - margen_error_estimacion
        ic_estimacion_superior = estimacion + margen_error_estimacion

        area_redondeada = round(estimacion, precision)
        ic_integral_inferior, ic_integral_superior = sorted([ic_estimacion_inferior, ic_estimacion_superior])

        print("INTEGRACION_METODO: Montecarlo")
        print("INTEGRACION_VARIANTE: Área entre curvas")
        print(f"INTEGRACION_SUBINTERVALOS: {n_muestras}")
        print(f"INTEGRACION_RESULTADO: {area_redondeada:.{precision}f}")
        print("MONTECARLO_MODO: curves")
        print("MONTECARLO_DIMENSIONES: 1")
        print(f"MONTECARLO_VOLUMEN: {rect_area:.{precision}f}")
        print(f"MONTECARLO_MEDIA_MUESTRAL: {prob_hat:.{precision}f}")
        print(f"MONTECARLO_DESVIACION_ESTANDAR: {desviacion_estandar:.{precision}f}")
        print(f"MONTECARLO_ERROR_ESTANDAR: {error_estandar:.{precision}f}")
        print(f"MONTECARLO_IC_PORCENTAJE: {ic_porcentaje:.2f}")
        print(f"MONTECARLO_IC_INFERIOR: {ic_integral_inferior:.{precision}f}")
        print(f"MONTECARLO_IC_SUPERIOR: {ic_integral_superior:.{precision}f}")
        print(f"MONTECARLO_CASOS_FAVORABLES: {casos_favorables}")
        print(f"MONTECARLO_CASOS_TOTALES: {casos_totales}")
        return

    rng = np.random.default_rng(semilla)
    muestras = rng.uniform(limites_inferiores, limites_superiores, size=(n_muestras, dimension))
    y_nodos = np.asarray(
        [_evaluar_muestra(f, np.asarray(muestra, dtype=float), f"muestra {i + 1}") for i, muestra in enumerate(muestras)],
        dtype=float,
    )

    volumen = float(np.prod(limites_superiores - limites_inferiores))

    media_muestral = float(np.mean(y_nodos))
    desviacion_estandar_base = float(np.std(y_nodos, ddof=1)) if n_muestras > 1 else 0.0
    desviacion_estandar = volumen * desviacion_estandar_base
    error_estandar = desviacion_estandar / np.sqrt(n_muestras)

    estimacion = volumen * media_muestral

    z_critico = NormalDist().inv_cdf(0.5 + ic_porcentaje / 200.0)
    margen_error_estimacion = z_critico * error_estandar
    ic_estimacion_inferior = estimacion - margen_error_estimacion
    ic_estimacion_superior = estimacion + margen_error_estimacion

    area_redondeada = round(estimacion, precision)
    ic_integral_inferior, ic_integral_superior = sorted([ic_estimacion_inferior, ic_estimacion_superior])

    casos_favorables: int | None = None
    casos_totales = int(n_muestras)
    if dimension == 1:
        a = float(limites_inferiores[0])
        b = float(limites_superiores[0])
        y_floor = min(0.0, float(np.min(y_nodos)))
        y_ceiling = max(0.0, float(np.max(y_nodos)))
        if abs(y_ceiling - y_floor) < 1e-12:
            y_floor -= 1.0
            y_ceiling += 1.0

        x_rand = rng.uniform(a, b, size=n_muestras)
        y_rand = rng.uniform(y_floor, y_ceiling, size=n_muestras)
        favorables = 0
        for xv, yv in zip(x_rand, y_rand):
            f_val = _evaluar_muestra(f, np.asarray([xv], dtype=float), "conteo favorable")
            lower_y = min(0.0, f_val)
            upper_y = max(0.0, f_val)
            if lower_y <= float(yv) <= upper_y:
                favorables += 1
        casos_favorables = int(favorables)

    print("INTEGRACION_METODO: Montecarlo")
    print("INTEGRACION_VARIANTE: Muestreo aleatorio")
    print(f"INTEGRACION_SUBINTERVALOS: {n_muestras}")
    print(f"INTEGRACION_RESULTADO: {area_redondeada:.{precision}f}")
    print("MONTECARLO_MODO: expr")
    print(f"MONTECARLO_DIMENSIONES: {dimension}")
    print(f"MONTECARLO_VOLUMEN: {volumen:.{precision}f}")
    print(f"MONTECARLO_MEDIA_MUESTRAL: {media_muestral:.{precision}f}")
    print(f"MONTECARLO_DESVIACION_ESTANDAR: {desviacion_estandar:.{precision}f}")
    print(f"MONTECARLO_ERROR_ESTANDAR: {error_estandar:.{precision}f}")
    print(f"MONTECARLO_IC_PORCENTAJE: {ic_porcentaje:.2f}")
    print(f"MONTECARLO_IC_INFERIOR: {ic_integral_inferior:.{precision}f}")
    print(f"MONTECARLO_IC_SUPERIOR: {ic_integral_superior:.{precision}f}")
    if casos_favorables is not None:
        print(f"MONTECARLO_CASOS_FAVORABLES: {casos_favorables}")
        print(f"MONTECARLO_CASOS_TOTALES: {casos_totales}")
