"""Método de integración numérica por regla de Simpson 3/8.

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


def _simpson_38_desde_nodos(x_nodos: list[float], y_nodos: list[float]) -> float:
    """Aplica Simpson 3/8 usando nodos ya evaluados."""
    n_subintervalos = len(x_nodos) - 1
    h = (x_nodos[-1] - x_nodos[0]) / n_subintervalos

    suma_multiplos_3 = sum(y_nodos[i] for i in range(1, n_subintervalos) if i % 3 == 0)
    suma_restantes = sum(y_nodos[i] for i in range(1, n_subintervalos) if i % 3 != 0)

    return (3.0 * h / 8.0) * (y_nodos[0] + y_nodos[-1] + 3.0 * suma_restantes + 2.0 * suma_multiplos_3)


def simpson_38(
    f,
    a: float,
    b: float,
    variante: str = "Simple",
    n: int | None = None,
) -> None:
    """Ejecuta Simpson 3/8 y emite salida de texto para la UI."""
    config = resolver_config()
    precision = config.precision

    validar_intervalo(a, b)
    variante_key, variante_label = normalizar_variante(variante)

    if variante_key == "simple":
        n_subintervalos = 3
        n_texto = "N/A"
    else:
        if n is None:
            raise ValueError("Para Simpson 3/8 compuesto debés ingresar la cantidad de subintervalos n.")
        n_original = int(n)
        if n_original < 3:
            n_subintervalos = 3
        elif n_original % 3 != 0:
            n_subintervalos = n_original + (3 - (n_original % 3))
        else:
            n_subintervalos = n_original

        validar_subintervalos(n_subintervalos, minimo=3, multiplo_de=3)
        n_texto = str(n_subintervalos)

        if n_subintervalos != n_original:
            print(
                "INTEGRACION_WARNING: "
                f"n={n_original} es incompatible con Simpson 3/8 compuesto; se compensó automáticamente a n={n_subintervalos}."
            )

    x_nodos, y_nodos = construir_nodos_evaluados(f, a, b, n_subintervalos)
    resultado = _simpson_38_desde_nodos(x_nodos, y_nodos)

    resultado_redondeado = round(float(resultado), precision)

    print(renderizar_tabla_nodos(x_nodos, y_nodos, precision))

    print("INTEGRACION_METODO: Simpson 3/8")
    print(f"INTEGRACION_VARIANTE: {variante_label}")
    print(f"INTEGRACION_SUBINTERVALOS: {n_texto}")
    print(f"INTEGRACION_RESULTADO: {resultado_redondeado:.{precision}f}")
