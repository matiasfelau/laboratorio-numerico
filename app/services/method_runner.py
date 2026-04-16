"""Application service that dispatches validated inputs to numeric methods.

Design notes:
- Method implementations in `metodos/*` are treated as black boxes.
- This runner only parses user input, injects callables when needed,
  and preserves the current textual output contract.
"""

from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from typing import Callable

import numpy as np
import sympy as sp

from metodos import (
    aceleracion_aitken,
    biseccion,
    diferencia_finita,
    lagrange,
    montecarlo,
    newton_raphson,
    punto_fijo,
    simpson_13,
    simpson_38,
    trapecio,
)


MATH_LOCALS = {"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E}


@dataclass(frozen=True)
class MethodRunResult:
    """Result contract returned to the web layer after a method execution."""

    success: bool
    output: str
    error: str | None = None


class MethodRunner:
    """Coordinates parsing + dispatch for all supported numeric methods."""

    def run(self, method_key: str, params: dict[str, object]) -> MethodRunResult:
        """Runs a method and captures stdout without changing method internals."""
        output_buffer = StringIO()

        try:
            with redirect_stdout(output_buffer):
                self._dispatch(method_key, params)

            output = output_buffer.getvalue().strip()
            if not output:
                output = "El metodo no devolvio salida de texto."
            return MethodRunResult(success=True, output=output)
        except Exception as exc:
            return MethodRunResult(success=False, output=output_buffer.getvalue().strip(), error=str(exc))

    def _dispatch(self, method_key: str, params: dict[str, object]) -> None:
        tipo = str(params.get("tipo", "")).strip().lower()

        if method_key == "newton_raphson":
            self._run_newton_raphson(params, tipo)
            return
        if method_key == "biseccion":
            self._run_biseccion(params, tipo)
            return
        if method_key == "punto_fijo":
            self._run_punto_fijo(params, tipo)
            return
        if method_key == "aceleracion_aitken":
            self._run_aceleracion_aitken(params, tipo)
            return
        if method_key == "lagrange":
            self._run_lagrange(params)
            return
        if method_key == "diferencia_finita":
            self._run_diferencia_finita(params)
            return
        if method_key == "trapecio":
            self._run_trapecio(params)
            return
        if method_key == "simpson_13":
            self._run_simpson_13(params)
            return
        if method_key == "simpson_38":
            self._run_simpson_38(params)
            return
        if method_key == "montecarlo":
            self._run_montecarlo(params)
            return

        raise ValueError(f"Metodo no soportado: {method_key}")

    def _run_newton_raphson(self, params: dict[str, object], tipo: str) -> None:
        fx = self._build_numeric_function(str(params["f_expr"]))
        with self._temporary_callable(newton_raphson, "f", fx):
            x0 = self._parse_numeric_scalar(str(params["x"]), "punto inicial")
            newton_raphson.newton_raphson(x0, tipo)

    def _run_biseccion(self, params: dict[str, object], tipo: str) -> None:
        fx = self._build_numeric_function(str(params["f_expr"]))
        a = self._parse_numeric_scalar(str(params["a"]), "inicio del intervalo")
        b = self._parse_numeric_scalar(str(params["b"]), "final del intervalo")
        biseccion.biseccion(fx, a, b, tipo)

    def _run_punto_fijo(self, params: dict[str, object], tipo: str) -> None:
        gx = self._build_numeric_function(str(params["g_expr"]))
        with self._temporary_callable(punto_fijo, "g", gx):
            x0 = self._parse_numeric_scalar(str(params["x"]), "punto inicial")
            punto_fijo.punto_fijo(x0, tipo)

    def _run_aceleracion_aitken(self, params: dict[str, object], tipo: str) -> None:
        gx = self._build_numeric_function(str(params["g_expr"]))
        with self._temporary_callable(aceleracion_aitken, "g", gx):
            x0 = self._parse_numeric_scalar(str(params["x"]), "punto inicial")
            aceleracion_aitken.aceleracion_aitken(x0, tipo)

    def _run_lagrange(self, params: dict[str, object]) -> None:
        f_expr_text = self._normalize_math_text(str(params.get("f_expr", "")))
        x_nodos = self._parse_numeric_list(str(params["x_nodos"]), "nodos x", enforce_unique=True)
        x_eval_raw = str(params.get("x_eval", "")).strip()
        y_text = str(params.get("y_nodos", "")).strip()
        if not f_expr_text and not y_text:
            raise ValueError("Debes ingresar una funcion real o las imagenes y de los nodos.")

        if x_eval_raw:
            x_eval = self._parse_numeric_scalar(x_eval_raw, "punto de evaluación")
        else:
            if f_expr_text:
                raise ValueError("Debes ingresar el punto de evaluación cuando usas función real.")
            # In image mode, local error is not computed, so any node is a valid placeholder.
            x_eval = float(x_nodos[0])

        y_nodos = self._parse_numeric_list(y_text, "imagenes y", enforce_unique=False) if y_text else None
        if y_nodos is not None and len(y_nodos) != len(x_nodos):
            raise ValueError("La cantidad de imagenes y debe coincidir con la cantidad de nodos x.")

        lagrange.lagrange(f_expr_text, x_nodos, x_eval, y_nodos)

    def _run_diferencia_finita(self, params: dict[str, object]) -> None:
        h_value = self._parse_numeric_scalar(str(params["h"]), "paso h")
        if h_value <= 0:
            raise ValueError("El paso h debe ser > 0.")

        metodo = str(params.get("metodo", "")).strip().lower()
        f_expr_text = str(params.get("f_expr", "")).strip()
        x_text = str(params.get("x", "")).strip()

        y_xm1_text = str(params.get("y_xm1", "")).strip()
        y_x_text = str(params.get("y_x", "")).strip()
        y_xp1_text = str(params.get("y_xp1", "")).strip()

        y_xm1 = self._parse_numeric_scalar(y_xm1_text, "imagen f(x-h)") if y_xm1_text else None
        y_x = self._parse_numeric_scalar(y_x_text, "imagen f(x)") if y_x_text else None
        y_xp1 = self._parse_numeric_scalar(y_xp1_text, "imagen f(x+h)") if y_xp1_text else None

        if not f_expr_text and y_xm1 is None and y_x is None and y_xp1 is None:
            raise ValueError("Debes ingresar una expresión o imágenes para calcular la derivada.")

        if f_expr_text:
            x_value = self._parse_numeric_scalar(x_text, "punto x")
            fx = self._build_numeric_function(f_expr_text)
            with self._temporary_callable(diferencia_finita, "f", fx):
                diferencia_finita.diferencia_finita(x_value, h_value, metodo)
            return

        x_value = self._parse_numeric_scalar(x_text, "punto x") if x_text else 0.0
        diferencia_finita.diferencia_finita(x_value, h_value, metodo, y_xm1=y_xm1, y_x=y_x, y_xp1=y_xp1)

    def _run_trapecio(self, params: dict[str, object]) -> None:
        fx = self._build_numeric_function(str(params["f_expr"]))
        a = self._parse_numeric_scalar(str(params["a"]), "límite inferior a")
        b = self._parse_numeric_scalar(str(params["b"]), "límite superior b")
        variante, n_value = self._parse_integration_variant_and_n(params)
        trapecio.trapecio(fx, a, b, variante=variante, n=n_value)

    def _run_simpson_13(self, params: dict[str, object]) -> None:
        fx = self._build_numeric_function(str(params["f_expr"]))
        a = self._parse_numeric_scalar(str(params["a"]), "límite inferior a")
        b = self._parse_numeric_scalar(str(params["b"]), "límite superior b")
        variante, n_value = self._parse_integration_variant_and_n(params)
        simpson_13.simpson_13(fx, a, b, variante=variante, n=n_value)

    def _run_simpson_38(self, params: dict[str, object]) -> None:
        fx = self._build_numeric_function(str(params["f_expr"]))
        a = self._parse_numeric_scalar(str(params["a"]), "límite inferior a")
        b = self._parse_numeric_scalar(str(params["b"]), "límite superior b")
        variante, n_value = self._parse_integration_variant_and_n(params)
        simpson_38.simpson_38(fx, a, b, variante=variante, n=n_value)

    def _run_montecarlo(self, params: dict[str, object]) -> None:
        lower_bounds = self._parse_numeric_csv_list(str(params.get("lower_bounds", "")), "límites inferiores")
        upper_bounds = self._parse_numeric_csv_list(str(params.get("upper_bounds", "")), "límites superiores")

        if len(lower_bounds) != len(upper_bounds):
            raise ValueError("La cantidad de límites inferiores debe coincidir con la de límites superiores.")

        fx = self._build_numeric_multivariable_function(str(params["f_expr"]), dimension_count=len(lower_bounds))
        n_muestras = self._parse_positive_int(str(params.get("n_muestras", "")).strip(), "cantidad de muestras N")
        ic_porcentaje = self._parse_percentage(str(params.get("ic_porcentaje", "95")).strip(), "% del intervalo de confianza")

        semilla_raw = str(params.get("semilla", "")).strip()
        semilla = self._parse_int(semilla_raw, "semilla") if semilla_raw else None

        montecarlo.montecarlo(
            fx,
            limites_inferiores=lower_bounds,
            limites_superiores=upper_bounds,
            n_muestras=n_muestras,
            ic_porcentaje=ic_porcentaje,
            semilla=semilla,
        )

    def _build_numeric_function(self, expression: str) -> Callable[[object], object]:
        x = sp.Symbol("x")
        try:
            sym_expr = sp.sympify(self._normalize_math_text(expression), locals=MATH_LOCALS)
            if sym_expr.free_symbols - {x}:
                raise ValueError("La expresion debe depender solo de la variable x.")
            callable_fn = sp.lambdify(x, sym_expr, modules=["numpy"])
        except Exception as exc:
            raise ValueError("La expresion de funcion no es valida.") from exc

        def wrapped(x_value: object) -> object:
            value = callable_fn(x_value)
            try:
                if np.isscalar(value):
                    return float(value)
                return np.asarray(value, dtype=float)
            except Exception as exc:
                raise ValueError("La expresion debe evaluarse a valores numericos reales.") from exc

        return wrapped

    def _build_numeric_multivariable_function(self, expression: str, dimension_count: int) -> Callable[[object], float]:
        if dimension_count < 1:
            raise ValueError("Debes ingresar al menos una dimensión de integración.")

        symbols = [sp.Symbol(f"x{i}") for i in range(1, dimension_count + 1)]
        locals_map = {**MATH_LOCALS, **{str(symbol): symbol for symbol in symbols}}

        # Alias convencionales para facilitar carga manual en Montecarlo.
        axis_aliases = ["x", "y", "z", "w", "t"]
        for idx, alias in enumerate(axis_aliases):
            if idx < dimension_count:
                locals_map[alias] = symbols[idx]

        try:
            sym_expr = sp.sympify(self._normalize_math_text(expression), locals=locals_map)
        except Exception as exc:
            raise ValueError("La expresion de funcion no es valida.") from exc

        allowed_symbols = set(symbols)
        if sym_expr.free_symbols - allowed_symbols:
            names = ", ".join([str(symbol) for symbol in symbols])
            aliases = ", ".join(axis_aliases[:dimension_count])
            raise ValueError(f"La función debe depender solo de: {names} (o aliases: {aliases}).")

        callable_fn = sp.lambdify(symbols, sym_expr, modules=["numpy"])

        def wrapped(point: object) -> float:
            try:
                values = np.asarray(point, dtype=float).reshape(-1)
            except Exception as exc:
                raise ValueError("Punto de evaluación inválido para Montecarlo.") from exc

            if values.size != dimension_count:
                raise ValueError("La dimensión de la muestra no coincide con la función de Montecarlo.")

            try:
                value = callable_fn(*values.tolist())
                numeric = complex(value)
            except Exception as exc:
                raise ValueError("La función de Montecarlo no pudo evaluarse en una muestra.") from exc

            if abs(numeric.imag) > 1e-12:
                raise ValueError("La función de Montecarlo produjo un valor complejo.")

            real_value = float(numeric.real)
            if not np.isfinite(real_value):
                raise ValueError("La función de Montecarlo produjo un valor no finito.")

            return real_value

        return wrapped

    def _parse_numeric_scalar(self, text: str, field_name: str) -> float:
        raw = self._normalize_math_text(text)
        if not raw:
            raise ValueError(f"Debes ingresar un valor para {field_name}.")

        try:
            expr = sp.sympify(raw, locals=MATH_LOCALS)
        except Exception as exc:
            raise ValueError(
                f"Valor invalido para {field_name}. Admite decimales, fracciones (1/3), pi y e/euler."
            ) from exc

        if expr.free_symbols:
            raise ValueError(f"Valor invalido para {field_name}. Solo se permiten constantes numericas.")

        value = float(expr.evalf())
        if not np.isfinite(value):
            raise ValueError(f"Valor invalido para {field_name}. Debe ser un numero real finito.")

        return value

    def _normalize_math_text(self, text: str) -> str:
        return str(text).replace("π", "pi").replace("ℯ", "euler").strip()

    def _parse_integration_variant_and_n(self, params: dict[str, object]) -> tuple[str, int | None]:
        variante = str(params.get("variante", "Simple")).strip() or "Simple"
        variante_key = variante.lower().replace("á", "a")

        if variante_key in {"simple", "s"}:
            return variante, None

        if variante_key in {"compuesto", "compuesta", "c"}:
            n_raw = str(params.get("n", "")).strip()
            if not n_raw:
                raise ValueError("Debes ingresar la cantidad de subintervalos n para la variante compuesta.")
            return variante, self._parse_positive_int(n_raw, "subintervalos n")

        raise ValueError("La variante debe ser 'Simple' o 'Compuesto'.")

    def _parse_positive_int(self, text: str, field_name: str) -> int:
        try:
            value = int(text)
        except Exception as exc:
            raise ValueError(f"Valor inválido para {field_name}. Debe ser un entero positivo.") from exc

        if value <= 0:
            raise ValueError(f"Valor inválido para {field_name}. Debe ser > 0.")

        return value

    def _parse_int(self, text: str, field_name: str) -> int:
        try:
            return int(text)
        except Exception as exc:
            raise ValueError(f"Valor inválido para {field_name}. Debe ser un entero.") from exc

    def _parse_percentage(self, text: str, field_name: str) -> float:
        value = self._parse_numeric_scalar(text, field_name)
        if value <= 0 or value >= 100:
            raise ValueError(f"Valor inválido para {field_name}. Debe estar entre 0 y 100 (excluidos).")
        return float(value)

    def _parse_numeric_list(self, text: str, field_name: str, enforce_unique: bool = False) -> np.ndarray:
        parts = [item.strip() for item in text.split(",") if item.strip()]
        if len(parts) < 2:
            raise ValueError(f"Debes ingresar al menos dos valores en {field_name}, separados por coma.")

        try:
            nodes = np.asarray([self._parse_numeric_scalar(value, field_name) for value in parts], dtype=float)
        except Exception as exc:
            raise ValueError(
                f"Los valores de {field_name} deben ser numericos y separados por coma. "
                "Admite decimales, fracciones (1/3), pi y e/euler."
            ) from exc

        if enforce_unique and len(np.unique(nodes)) != len(nodes):
            raise ValueError("Los nodos no deben repetirse.")

        return nodes

    def _parse_numeric_csv_list(self, text: str, field_name: str) -> np.ndarray:
        parts = [item.strip() for item in text.split(",") if item.strip()]
        if not parts:
            raise ValueError(f"Debes ingresar al menos un valor en {field_name}, separado por coma.")

        try:
            values = np.asarray([self._parse_numeric_scalar(value, field_name) for value in parts], dtype=float)
        except Exception as exc:
            raise ValueError(
                f"Los valores de {field_name} deben ser numéricos y separados por coma. "
                "Admite decimales, fracciones (1/3), pi y e/euler."
            ) from exc

        return values

    @contextmanager
    def _temporary_callable(self, module: object, name: str, fn: Callable[[object], object]):
        """Temporarily monkey-patch method modules with runtime callables."""
        original = getattr(module, name)
        setattr(module, name, fn)
        try:
            yield
        finally:
            setattr(module, name, original)
