"""Métodos para problemas de valor inicial y' = f(x, y)."""

from __future__ import annotations

from typing import Callable

from tabulate import tabulate

from utils.parametros import resolver_config


def _evaluar_f(f: Callable[[float, float], object], x: float, y: float, etiqueta: str) -> float:
    try:
        value = f(x, y)
        numeric = complex(value)
    except Exception as exc:
        raise ValueError(f"No se pudo evaluar f en {etiqueta}.") from exc

    if abs(numeric.imag) > 1e-12:
        raise ValueError(f"La función produjo un valor complejo en {etiqueta}.")

    real_value = float(numeric.real)
    if not (real_value == real_value and abs(real_value) != float("inf")):
        raise ValueError(f"La función produjo un valor no finito en {etiqueta}.")

    return real_value


def _evaluar_solucion_exacta(solucion_exacta: Callable[[float], object], x: float, etiqueta: str) -> float:
    try:
        value = solucion_exacta(x)
        numeric = complex(value)
    except Exception as exc:
        raise ValueError(f"No se pudo evaluar la solución exacta en {etiqueta}.") from exc

    if abs(numeric.imag) > 1e-12:
        raise ValueError(f"La solución exacta produjo un valor complejo en {etiqueta}.")

    real_value = float(numeric.real)
    if not (real_value == real_value and abs(real_value) != float("inf")):
        raise ValueError(f"La solución exacta produjo un valor no finito en {etiqueta}.")

    return real_value


def _formatear_precision(valor: float, precision: int) -> str:
    return f"{valor:.{precision}f}"


def _runge_kutta_4(
    f: Callable[[float, float], object],
    solucion_exacta: Callable[[float], object],
    y0: float,
    h: float,
    a: float,
    b: float,
) -> None:
    cfg = resolver_config()
    precision = cfg.precision

    if h <= 0:
        raise ValueError("El paso h debe ser > 0.")
    if b <= a:
        raise ValueError("El intervalo debe cumplir a < b.")

    x = float(a)
    y = round(float(y0), precision)
    tol = 1e-12

    tabla: list[list[float | int | str]] = []

    i = 0
    while x < b:
        h_eff = min(h, b - x)
        if h_eff <= 0:
            break

        k1 = round(_evaluar_f(f, x, y, f"x={x}, y={y}"), precision)
        k2 = round(_evaluar_f(f, x + h_eff / 2.0, y + (h_eff * k1) / 2.0, f"x={x + h_eff / 2.0}, y={y + (h_eff * k1) / 2.0}"), precision)
        k3 = round(_evaluar_f(f, x + h_eff / 2.0, y + (h_eff * k2) / 2.0, f"x={x + h_eff / 2.0}, y={y + (h_eff * k2) / 2.0}"), precision)
        k4 = round(_evaluar_f(f, x + h_eff, y + h_eff * k3, f"x={x + h_eff}, y={y + h_eff * k3}"), precision)
        y_next = round(y + (h_eff / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4), precision)
        y_exacta = round(_evaluar_solucion_exacta(solucion_exacta, x, f"x={x}"), precision)
        error = round(y_exacta - y, precision)
        i += 1
        error_display: float | str = "-" if i == 1 else error
        tabla.append([
            i,
            round(x, precision),
            y,
            k1,
            k2,
            k3,
            k4,
            _formatear_precision(y_next, precision),
            y_exacta,
            error_display if error_display == "-" else _formatear_precision(float(error_display), precision),
        ])

        x_next = x + h_eff
        if x_next > b - tol:
            x_next = b
        x = x_next
        y = y_next

    # Fila terminal para mostrar explícitamente el extremo inclusivo x_n=b.
    if abs(x - b) <= tol:
        k1 = round(_evaluar_f(f, x, y, f"x={x}, y={y}"), precision)
        k2 = round(_evaluar_f(f, x + h / 2.0, y + (h * k1) / 2.0, f"x={x + h / 2.0}, y={y + (h * k1) / 2.0}"), precision)
        k3 = round(_evaluar_f(f, x + h / 2.0, y + (h * k2) / 2.0, f"x={x + h / 2.0}, y={y + (h * k2) / 2.0}"), precision)
        k4 = round(_evaluar_f(f, x + h, y + h * k3, f"x={x + h}, y={y + h * k3}"), precision)
        y_next = round(y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4), precision)
        y_exacta = round(_evaluar_solucion_exacta(solucion_exacta, x, f"x={x}"), precision)
        error = round(y_exacta - y, precision)
        i += 1
        tabla.append([
            i,
            round(x, precision),
            y,
            k1,
            k2,
            k3,
            k4,
            "-",
            y_exacta,
            _formatear_precision(error, precision),
        ])

    headers = [
        "n",
        "x_n",
        "y_n",
        "k1",
        "k2",
        "k3",
        "k4",
        "y_{n+1}",
        "solucion exacta",
        "error",
    ]

    print(tabulate(tabla, headers=headers, tablefmt="grid", floatfmt=f".{precision}f"))


def euler(
    f: Callable[[float, float], object],
    solucion_exacta: Callable[[float], object],
    y0: float,
    h: float,
    a: float,
    b: float,
) -> None:
    cfg = resolver_config()
    precision = cfg.precision

    if h <= 0:
        raise ValueError("El paso h debe ser > 0.")
    if b <= a:
        raise ValueError("El intervalo debe cumplir a < b.")

    x = float(a)
    y = round(float(y0), precision)
    tol = 1e-12
    tabla: list[list[float | int | str]] = []

    i = 0
    while x < b:
        h_eff = min(h, b - x)
        if h_eff <= 0:
            break

        k1 = round(_evaluar_f(f, x, y, f"x={x}, y={y}"), precision)
        y_next = round(y + h_eff * k1, precision)
        y_exacta = round(_evaluar_solucion_exacta(solucion_exacta, x, f"x={x}"), precision)
        error = round(y_exacta - y, precision)
        i += 1
        error_display: float | str = "-" if i == 1 else error
        tabla.append([
            i,
            round(x, precision),
            y,
            _formatear_precision(y_next, precision),
            y_exacta,
            error_display if error_display == "-" else _formatear_precision(float(error_display), precision),
        ])

        x_next = x + h_eff
        if x_next > b - tol:
            x_next = b
        x = x_next
        y = y_next

    # Fila terminal para mostrar explícitamente el extremo inclusivo x_n=b.
    if abs(x - b) <= tol:
        k1 = round(_evaluar_f(f, x, y, f"x={x}, y={y}"), precision)
        y_next = round(y + h * k1, precision)
        y_exacta = round(_evaluar_solucion_exacta(solucion_exacta, x, f"x={x}"), precision)
        error = round(y_exacta - y, precision)
        i += 1
        tabla.append([i, round(x, precision), y, "-", y_exacta, _formatear_precision(error, precision)])

    headers = ["n", "x_n", "y_n", "y_{n+1}", "solucion exacta", "error"]
    print(tabulate(tabla, headers=headers, tablefmt="grid", floatfmt=f".{precision}f"))


def runge_kutta_4(
    f: Callable[[float, float], object],
    solucion_exacta: Callable[[float], object],
    y0: float,
    h: float,
    a: float,
    b: float,
) -> None:
    _runge_kutta_4(f, solucion_exacta, y0, h, a, b)
