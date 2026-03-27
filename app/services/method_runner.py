from contextlib import redirect_stdout
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO

import numpy as np
import sympy as sp

from metodos import aceleracion_aitken, biseccion, diferencia_finita, lagrange, newton_raphson, punto_fijo


@dataclass(frozen=True)
class MethodRunResult:
    success: bool
    output: str
    error: str | None = None


class MethodRunner:
    def run(self, method_key: str, params: dict[str, object]) -> MethodRunResult:
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
            fx = self._build_numeric_function(str(params["f_expr"]))
            with self._temporary_callable(newton_raphson, "f", fx):
                x0 = self._parse_numeric_scalar(str(params["x"]), "punto inicial")
                newton_raphson.newton_raphson(x0, tipo)
            return

        if method_key == "biseccion":
            fx = self._build_numeric_function(str(params["f_expr"]))
            a = self._parse_numeric_scalar(str(params["a"]), "inicio del intervalo")
            b = self._parse_numeric_scalar(str(params["b"]), "final del intervalo")
            biseccion.biseccion(
                fx,
                a,
                b,
                tipo,
            )
            return

        if method_key == "punto_fijo":
            gx = self._build_numeric_function(str(params["g_expr"]))
            with self._temporary_callable(punto_fijo, "g", gx):
                x0 = self._parse_numeric_scalar(str(params["x"]), "punto inicial")
                punto_fijo.punto_fijo(x0, tipo)
            return

        if method_key == "aceleracion_aitken":
            gx = self._build_numeric_function(str(params["g_expr"]))
            with self._temporary_callable(aceleracion_aitken, "g", gx):
                x0 = self._parse_numeric_scalar(str(params["x"]), "punto inicial")
                aceleracion_aitken.aceleracion_aitken(x0, tipo)
            return

        if method_key == "lagrange":
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
            return

        if method_key == "diferencia_finita":
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
            else:
                x_value = self._parse_numeric_scalar(x_text, "punto x") if x_text else 0.0

            if f_expr_text:
                fx = self._build_numeric_function(f_expr_text)
                with self._temporary_callable(diferencia_finita, "f", fx):
                    diferencia_finita.diferencia_finita(x_value, h_value, metodo)
            else:
                diferencia_finita.diferencia_finita(x_value, h_value, metodo, y_xm1=y_xm1, y_x=y_x, y_xp1=y_xp1)
            return

        raise ValueError(f"Metodo no soportado: {method_key}")

    def _build_numeric_function(self, expression: str):
        x = sp.Symbol("x")
        try:
            sym_expr = sp.sympify(self._normalize_math_text(expression), locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E})
            if sym_expr.free_symbols - {x}:
                raise ValueError("La expresion debe depender solo de la variable x.")
            callable_fn = sp.lambdify(x, sym_expr, modules=["numpy"])
        except Exception as exc:
            raise ValueError("La expresion de funcion no es valida.") from exc

        def wrapped(x_value):
            value = callable_fn(x_value)
            try:
                if np.isscalar(value):
                    return float(value)
                return np.asarray(value, dtype=float)
            except Exception as exc:
                raise ValueError("La expresion debe evaluarse a valores numericos reales.") from exc

        return wrapped

    def _parse_numeric_scalar(self, text: str, field_name: str) -> float:
        raw = self._normalize_math_text(text)
        if not raw:
            raise ValueError(f"Debes ingresar un valor para {field_name}.")

        try:
            expr = sp.sympify(raw, locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E})
        except Exception as exc:
            raise ValueError(
                f"Valor invalido para {field_name}. Admite decimales, fracciones (1/3), pi y e/euler."
            ) from exc

        if expr.free_symbols:
            raise ValueError(
                f"Valor invalido para {field_name}. Solo se permiten constantes numericas."
            )

        value = float(expr.evalf())
        if not np.isfinite(value):
            raise ValueError(f"Valor invalido para {field_name}. Debe ser un numero real finito.")

        return value

    def _normalize_math_text(self, text: str) -> str:
        return str(text).replace("π", "pi").replace("ℯ", "euler").strip()

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

    @contextmanager
    def _temporary_callable(self, module: object, name: str, fn):
        original = getattr(module, name)
        setattr(module, name, fn)
        try:
            yield
        finally:
            setattr(module, name, original)
