from contextlib import redirect_stdout
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO

import numpy as np
import sympy as sp

from metodos import aceleracion_aitken, biseccion, newton_raphson, punto_fijo


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
                newton_raphson.newton_raphson(float(params["x"]), tipo)
            return

        if method_key == "biseccion":
            fx = self._build_numeric_function(str(params["f_expr"]))
            biseccion.biseccion(
                fx,
                float(params["a"]),
                float(params["b"]),
                tipo,
            )
            return

        if method_key == "punto_fijo":
            gx = self._build_numeric_function(str(params["g_expr"]))
            with self._temporary_callable(punto_fijo, "g", gx):
                punto_fijo.punto_fijo(float(params["x"]), tipo)
            return

        if method_key == "aceleracion_aitken":
            gx = self._build_numeric_function(str(params["g_expr"]))
            with self._temporary_callable(aceleracion_aitken, "g", gx):
                aceleracion_aitken.aceleracion_aitken(float(params["x"]), tipo)
            return

        raise ValueError(f"Metodo no soportado: {method_key}")

    def _build_numeric_function(self, expression: str):
        x = sp.Symbol("x")
        try:
            sym_expr = sp.sympify(expression)
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

    @contextmanager
    def _temporary_callable(self, module: object, name: str, fn):
        original = getattr(module, name)
        setattr(module, name, fn)
        try:
            yield
        finally:
            setattr(module, name, original)
