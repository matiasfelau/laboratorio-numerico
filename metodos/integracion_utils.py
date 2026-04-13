"""Utilidades compartidas para métodos de integración numérica.

Este módulo concentra validaciones y normalización para mantener DRY
entre Trapecio, Simpson 1/3 y Simpson 3/8.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from tabulate import tabulate


def normalizar_variante(variante: str) -> tuple[str, str]:
    """Normaliza la variante de integración a simple o compuesto.

    Parameters
    ----------
    variante:
        Texto recibido desde la capa de UI/API.

    Returns
    -------
    tuple[str, str]
        Clave normalizada y etiqueta para salida.
    """
    raw = str(variante or "").strip().lower().replace("á", "a")
    if raw in {"simple", "s"}:
        return "simple", "Simple"
    if raw in {"compuesto", "compuesta", "c"}:
        return "compuesto", "Compuesto"
    raise ValueError("Variante no válida. Usá: Simple o Compuesto.")


def validar_intervalo(a: float, b: float) -> None:
    """Valida que el intervalo de integración sea distinto."""
    if a == b:
        raise ValueError("El intervalo de integración no puede tener extremos iguales.")


def validar_subintervalos(n: int, *, minimo: int, multiplo_de: int | None = None) -> None:
    """Valida cantidad de subintervalos para reglas compuestas.

    Parameters
    ----------
    n:
        Cantidad de subintervalos.
    minimo:
        Cota inferior válida para n.
    multiplo_de:
        Si se define, exige que n sea múltiplo de este valor.
    """
    if n < minimo:
        raise ValueError(f"La cantidad de subintervalos n debe ser >= {minimo}.")

    if multiplo_de is not None and n % multiplo_de != 0:
        raise ValueError(f"La cantidad de subintervalos n debe ser múltiplo de {multiplo_de}.")


def asegurar_valor_real(value: object, field_name: str) -> float:
    """Convierte una evaluación numérica en escalar real finito."""
    try:
        numeric = complex(value)
    except Exception as exc:
        raise ValueError(f"La función evaluada en {field_name} no produjo un valor numérico.") from exc

    if abs(numeric.imag) > 1e-12:
        raise ValueError(f"La función evaluada en {field_name} produjo un valor complejo.")

    real_value = float(numeric.real)
    if not np.isfinite(real_value):
        raise ValueError(f"La función evaluada en {field_name} no es un número finito.")

    return real_value


def evaluar_funcion(f: Callable[[float], object], x: float, field_name: str) -> float:
    """Evalúa f(x) y valida que el resultado sea real finito."""
    return asegurar_valor_real(f(x), field_name)


def construir_nodos_evaluados(
    f: Callable[[float], object],
    a: float,
    b: float,
    n_subintervalos: int,
) -> tuple[list[float], list[float]]:
    """Construye nodos uniformes y evalúa f en cada uno."""
    validar_subintervalos(n_subintervalos, minimo=1)

    h = (b - a) / n_subintervalos
    x_nodos: list[float] = []
    y_nodos: list[float] = []

    for i in range(n_subintervalos + 1):
        xi = a + i * h
        yi = evaluar_funcion(f, xi, f"x_{i}")
        x_nodos.append(float(xi))
        y_nodos.append(float(yi))

    return x_nodos, y_nodos


def renderizar_tabla_nodos(x_nodos: list[float], y_nodos: list[float], precision: int) -> str:
    """Renderiza tabla de nodos con columnas n, x_n, f(x_n)."""
    filas = []
    for i, (xi, yi) in enumerate(zip(x_nodos, y_nodos)):
        filas.append([i, round(float(xi), precision), round(float(yi), precision)])

    return tabulate(
        filas,
        headers=["n", "x_n", "f(x_n)"],
        tablefmt="grid",
        floatfmt=f".{precision}f",
    )
