"""Método de integración numérica por regla del trapecio.

Incluye modalidad simple y compuesta.
"""

from __future__ import annotations

from utils.parametros import resolver_config

from .integracion_utils import (
    construir_nodos_evaluados,
    normalizar_variante,
    renderizar_tabla_nodos,
    validar_intervalo,
)


def _trapecio_desde_nodos(x_nodos: list[float], y_nodos: list[float]) -> float:
    """Aplica trapecio usando nodos ya evaluados."""
    n_subintervalos = len(x_nodos) - 1
    h = (x_nodos[-1] - x_nodos[0]) / n_subintervalos
    suma_intermedia = sum(y_nodos[1:-1])
    return (h / 2.0) * (y_nodos[0] + y_nodos[-1] + 2.0 * suma_intermedia)


def trapecio(f, a: float, b: float, variante: str = "Simple", n: int | None = None) -> None:
    """Ejecuta regla del trapecio y emite salida de texto para la UI."""
    config = resolver_config()
    precision = config.precision

    validar_intervalo(a, b)
    variante_key, variante_label = normalizar_variante(variante)

    if variante_key == "simple":
        n_subintervalos = 1
        n_texto = "N/A"
    else:
        if n is None:
            raise ValueError("Para Trapecio compuesto debés ingresar la cantidad de subintervalos n.")
        n_subintervalos = int(n)
        n_texto = str(n_subintervalos)

    x_nodos, y_nodos = construir_nodos_evaluados(f, a, b, n_subintervalos)
    resultado = _trapecio_desde_nodos(x_nodos, y_nodos)

    resultado_redondeado = round(float(resultado), precision)

    print(renderizar_tabla_nodos(x_nodos, y_nodos, precision))

    print("INTEGRACION_METODO: Trapecio")
    print(f"INTEGRACION_VARIANTE: {variante_label}")
    print(f"INTEGRACION_SUBINTERVALOS: {n_texto}")
    print(f"INTEGRACION_RESULTADO: {resultado_redondeado:.{precision}f}")
