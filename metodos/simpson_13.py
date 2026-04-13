"""Método de integración numérica por regla de Simpson 1/3.

Incluye modalidad simple y compuesta.
"""

from __future__ import annotations

from utils.parametros import resolver_config

from .integracion_utils import (
    construir_nodos_evaluados,
    normalizar_variante,
    renderizar_tabla_nodos,
    validar_intervalo,
    validar_subintervalos,
)


def _simpson_13_desde_nodos(x_nodos: list[float], y_nodos: list[float]) -> float:
    """Aplica Simpson 1/3 usando nodos ya evaluados."""
    n_subintervalos = len(x_nodos) - 1
    h = (x_nodos[-1] - x_nodos[0]) / n_subintervalos

    suma_impares = sum(y_nodos[i] for i in range(1, n_subintervalos, 2))
    suma_pares = sum(y_nodos[i] for i in range(2, n_subintervalos, 2))

    return (h / 3.0) * (y_nodos[0] + y_nodos[-1] + 4.0 * suma_impares + 2.0 * suma_pares)


def simpson_13(
    f,
    a: float,
    b: float,
    variante: str = "Simple",
    n: int | None = None,
) -> None:
    """Ejecuta Simpson 1/3 y emite salida de texto para la UI."""
    config = resolver_config()
    precision = config.precision

    validar_intervalo(a, b)
    variante_key, variante_label = normalizar_variante(variante)

    if variante_key == "simple":
        n_subintervalos = 2
        n_texto = "N/A"
    else:
        if n is None:
            raise ValueError("Para Simpson 1/3 compuesto debés ingresar la cantidad de subintervalos n.")
        n_subintervalos = int(n)
        validar_subintervalos(n_subintervalos, minimo=2, multiplo_de=2)
        n_texto = str(n_subintervalos)

    x_nodos, y_nodos = construir_nodos_evaluados(f, a, b, n_subintervalos)
    resultado = _simpson_13_desde_nodos(x_nodos, y_nodos)

    resultado_redondeado = round(float(resultado), precision)

    print(renderizar_tabla_nodos(x_nodos, y_nodos, precision))

    print("INTEGRACION_METODO: Simpson 1/3")
    print(f"INTEGRACION_VARIANTE: {variante_label}")
    print(f"INTEGRACION_SUBINTERVALOS: {n_texto}")
    print(f"INTEGRACION_RESULTADO: {resultado_redondeado:.{precision}f}")
