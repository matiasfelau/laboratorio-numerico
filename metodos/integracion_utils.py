"""Utilidades compartidas para métodos de integración numérica.

Este módulo concentra validaciones y normalización para mantener DRY
entre Trapecio, Simpson 1/3 y Simpson 3/8.
"""

from __future__ import annotations

import sympy as sp
from typing import Callable

import numpy as np
from tabulate import tabulate


def _normalizar_texto_matematico(texto: str) -> str:
    return str(texto).replace("π", "pi").replace("ℯ", "euler").strip()


def _estimar_maximo_abs_derivada_en_intervalo(
    derivada_expr: sp.Expr,
    x: sp.Symbol,
    a: float,
    b: float,
) -> float | None:
    """Estima max |derivada(x)| en [a,b] tolerando puntos no evaluables."""
    derivada_num = sp.lambdify(x, derivada_expr, modules=["numpy"])
    x_vals = np.linspace(a, b, 401)
    valores_abs: list[float] = []

    for xi in x_vals:
        yi: float | None = None

        # Primer intento: función lambdify (rápido).
        try:
            with np.errstate(all="ignore"):
                raw = derivada_num(float(xi))
            yi = float(raw)
        except Exception:
            yi = None

        # Fallback: evaluación simbólica puntual.
        if yi is None:
            try:
                yi = float(sp.N(derivada_expr.subs(x, sp.Float(float(xi)))))
            except Exception:
                yi = None

        if yi is None or not np.isfinite(yi):
            continue

        valores_abs.append(abs(yi))

    if not valores_abs:
        return None

    return float(max(valores_abs))


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


def calcular_error_truncamiento_trapecio(
    f_expr_text: str,
    a: float,
    b: float,
    n_subintervalos: int,
    precision: int,
    x_eval_derivada: float | None = None,
) -> float | None:
    """Calcula el error de truncamiento teórico para la regla del trapecio compuesto.

    Fórmula: E = -(b-a)/12 * h^2 * f''(ξ)
    donde h = (b-a)/n y ξ es un punto en [a, b].

    Si se ingresa x_eval_derivada, usa |f''(x_eval_derivada)|.
    En caso contrario, estima |f''(ξ)| como máximo de |f''(x)| en el intervalo.
    """
    try:
        x = sp.Symbol("x")
        expr = sp.sympify(
            _normalizar_texto_matematico(f_expr_text),
            locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E, "x": x},
        )

        if expr.free_symbols - {x}:
            return None

        f_double_prime = sp.diff(expr, x, 2)
        if x_eval_derivada is not None:
            val = sp.N(f_double_prime.subs(x, sp.Float(x_eval_derivada)))
            max_f_double_prime = abs(float(val))
        else:
            max_f_double_prime = _estimar_maximo_abs_derivada_en_intervalo(f_double_prime, x, a, b)

        if max_f_double_prime is None or not np.isfinite(max_f_double_prime):
            return None

        h = (b - a) / n_subintervalos
        error = (b - a) / 12.0 * h**2 * max_f_double_prime
        return round(float(error), precision)

    except Exception:
        return None


def calcular_error_truncamiento_simpson_13(
    f_expr_text: str,
    a: float,
    b: float,
    n_subintervalos: int,
    precision: int,
    x_eval_derivada: float | None = None,
) -> float | None:
    """Calcula el error de truncamiento teórico para Simpson 1/3 compuesto.

    Fórmula: E = -(b-a)/180 * h^4 * f⁽⁴⁾(ξ)
    donde h = (b-a)/n y ξ es un punto en [a, b].

    Si se ingresa x_eval_derivada, usa |f⁽⁴⁾(x_eval_derivada)|.
    En caso contrario, estima |f⁽⁴⁾(ξ)| como máximo de |f⁽⁴⁾(x)| en el intervalo.
    """
    try:
        x = sp.Symbol("x")
        expr = sp.sympify(
            _normalizar_texto_matematico(f_expr_text),
            locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E, "x": x},
        )

        if expr.free_symbols - {x}:
            return None

        f_fourth = sp.diff(expr, x, 4)
        if x_eval_derivada is not None:
            val = sp.N(f_fourth.subs(x, sp.Float(x_eval_derivada)))
            max_f_fourth = abs(float(val))
        else:
            max_f_fourth = _estimar_maximo_abs_derivada_en_intervalo(f_fourth, x, a, b)

        if max_f_fourth is None or not np.isfinite(max_f_fourth):
            return None

        h = (b - a) / n_subintervalos
        error = (b - a) / 180.0 * h**4 * max_f_fourth
        return round(float(error), precision)

    except Exception:
        return None


def calcular_error_truncamiento_simpson_38(
    f_expr_text: str,
    a: float,
    b: float,
    n_subintervalos: int,
    precision: int,
    x_eval_derivada: float | None = None,
) -> float | None:
    """Calcula el error de truncamiento teórico para Simpson 3/8 compuesto.

    Fórmula: E = -(3(b-a)/80) * h^4 * f⁽⁴⁾(ξ)
    donde h = (b-a)/n y ξ es un punto en [a, b].

    Si se ingresa x_eval_derivada, usa |f⁽⁴⁾(x_eval_derivada)|.
    En caso contrario, estima |f⁽⁴⁾(ξ)| como máximo de |f⁽⁴⁾(x)| en el intervalo.
    """
    try:
        x = sp.Symbol("x")
        expr = sp.sympify(
            _normalizar_texto_matematico(f_expr_text),
            locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E, "x": x},
        )

        if expr.free_symbols - {x}:
            return None

        f_fourth = sp.diff(expr, x, 4)
        if x_eval_derivada is not None:
            val = sp.N(f_fourth.subs(x, sp.Float(x_eval_derivada)))
            max_f_fourth = abs(float(val))
        else:
            max_f_fourth = _estimar_maximo_abs_derivada_en_intervalo(f_fourth, x, a, b)

        if max_f_fourth is None or not np.isfinite(max_f_fourth):
            return None

        h = (b - a) / n_subintervalos
        error = 3.0 * (b - a) / 80.0 * h**4 * max_f_fourth
        return round(float(error), precision)

    except Exception:
        return None
