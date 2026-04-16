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

    print("INTEGRACION_METODO: Montecarlo")
    print("INTEGRACION_VARIANTE: Muestreo aleatorio")
    print(f"INTEGRACION_SUBINTERVALOS: {n_muestras}")
    print(f"INTEGRACION_RESULTADO: {area_redondeada:.{precision}f}")
    print(f"MONTECARLO_DIMENSIONES: {dimension}")
    print(f"MONTECARLO_VOLUMEN: {volumen:.{precision}f}")
    print(f"MONTECARLO_MEDIA_MUESTRAL: {media_muestral:.{precision}f}")
    print(f"MONTECARLO_DESVIACION_ESTANDAR: {desviacion_estandar:.{precision}f}")
    print(f"MONTECARLO_ERROR_ESTANDAR: {error_estandar:.{precision}f}")
    print(f"MONTECARLO_IC_PORCENTAJE: {ic_porcentaje:.2f}")
    print(f"MONTECARLO_IC_INFERIOR: {ic_integral_inferior:.{precision}f}")
    print(f"MONTECARLO_IC_SUPERIOR: {ic_integral_superior:.{precision}f}")
