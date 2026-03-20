from __future__ import annotations

import math

import numpy as np
import sympy as sp
from flask import Flask, jsonify, render_template, request

from app.services.method_registry import get_methods
from app.services.method_runner import MethodRunner
from utils.parametros import aplicar_configuracion_global


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    runner = MethodRunner()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/methods")
    def methods():
        payload = []
        for method in get_methods():
            payload.append(
                {
                    "key": method.key,
                    "label": method.label,
                    "description": method.description,
                    "fields": [
                        {
                            "key": field.key,
                            "label": field.label,
                            "kind": field.kind,
                            "default": field.default,
                            "options": field.options,
                        }
                        for field in method.fields
                    ],
                }
            )
        return jsonify(payload)

    @app.post("/api/run")
    def run_method():
        body = request.get_json(silent=True) or {}
        method_key = body.get("method")
        params = body.get("params")
        global_config_raw = body.get("global_config")

        if not method_key or not isinstance(method_key, str):
            return jsonify({"success": False, "error": "Metodo invalido."}), 400

        if not isinstance(params, dict):
            return jsonify({"success": False, "error": "Parametros invalidos."}), 400

        try:
            global_config = _parse_global_config(global_config_raw)
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

        with aplicar_configuracion_global(global_config):
            result = runner.run(method_key, params)

        debug_mode = bool(global_config.get("debug_mode", False))
        if debug_mode:
            print(f"[api/run] metodo={method_key} success={result.success}")
            if result.output:
                print(result.output)
            if result.error:
                print(f"[api/run][error] {result.error}")

        return jsonify(
            {
                "success": result.success,
                "output": result.output,
                "error": result.error,
            }
        )

    @app.post("/api/plot")
    def plot_function():
        body = request.get_json(silent=True) or {}
        method_key = body.get("method")
        params = body.get("params")

        if not method_key or not isinstance(method_key, str):
            return jsonify({"success": False, "error": "Metodo invalido."}), 400

        if not isinstance(params, dict):
            return jsonify({"success": False, "error": "Parametros invalidos."}), 400

        try:
            expr_key = _expression_key(method_key)
            expr_text = str(params.get(expr_key, "")).strip()
            if not expr_text:
                raise ValueError("Debes ingresar una funcion para graficar.")

            x_min, x_max = _domain_for_plot(method_key, params)
            points = _build_plot_points(expr_text, x_min, x_max)
            latex_text = _expression_to_latex(expr_text)

            if len(points) < 2:
                raise ValueError("No se pudo graficar: dominio sin puntos validos.")

            return jsonify(
                {
                    "success": True,
                    "function": expr_text,
                    "latex": latex_text,
                    "domain": [x_min, x_max],
                    "points": points,
                }
            )
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

    @app.post("/api/latex")
    def latex_preview():
        body = request.get_json(silent=True) or {}
        expression = body.get("expression")

        if expression is None:
            return jsonify({"success": False, "error": "Expresion invalida."}), 400

        expression_text = str(expression).strip()
        if not expression_text:
            return jsonify({"success": False, "error": "Expresion vacia."}), 400

        try:
            sym_expr = sp.sympify(expression_text)
            latex_text = sp.latex(sym_expr)
            return jsonify({"success": True, "latex": latex_text})
        except Exception:
            return jsonify({"success": False, "error": "Expresion no valida."}), 400

    return app


def main() -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)


def _expression_key(method_key: str) -> str:
    if method_key in {"newton_raphson", "biseccion"}:
        return "f_expr"
    if method_key in {"punto_fijo", "aceleracion_aitken"}:
        return "g_expr"
    raise ValueError("Metodo no soportado para graficar.")


def _domain_for_plot(method_key: str, params: dict) -> tuple[float, float]:
    _ = method_key
    _ = params
    # Fixed plotting window requested by UI: x from -5 to 5.
    return -5.0, 5.0


def _build_plot_points(expr_text: str, x_min: float, x_max: float) -> list[list[float]]:
    x_symbol = sp.Symbol("x")
    try:
        expr = sp.sympify(expr_text)
        fn = sp.lambdify(x_symbol, expr, modules=["numpy"])
    except Exception as exc:
        raise ValueError("La expresion de la funcion no es valida.") from exc

    # Use a compact fixed grid for fast rendering.
    x_values = np.linspace(x_min, x_max, 121)
    y_values = fn(x_values)

    if np.isscalar(y_values):
        y_values = np.full_like(x_values, y_values, dtype=float)

    points: list[list[float]] = []
    for x_val, y_val in zip(x_values, y_values):
        try:
            y = float(y_val)
        except Exception:
            continue

        if not math.isfinite(y):
            continue

        # Keep only points visible in the fixed y window [-5, 5].
        if y < -5 or y > 5:
            continue

        points.append([float(x_val), y])

    return points


def _expression_to_latex(expr_text: str) -> str:
    try:
        expr = sp.sympify(expr_text)
        return sp.latex(expr)
    except Exception as exc:
        raise ValueError("La expresion de la funcion no es valida.") from exc


def _parse_global_config(raw: object) -> dict[str, int | float]:
    if raw is None:
        return {}

    if not isinstance(raw, dict):
        raise ValueError("Configuracion global invalida.")

    result: dict[str, int | float] = {}

    if raw.get("iteraciones") is not None:
        result["iteraciones"] = int(raw["iteraciones"])

    if raw.get("tolerancia") is not None:
        result["tolerancia"] = float(raw["tolerancia"])

    if raw.get("precision") is not None:
        result["precision"] = int(raw["precision"])

    if raw.get("porcentaje") is not None:
        result["porcentaje"] = float(raw["porcentaje"])

    if raw.get("debugMode") is not None:
        result["debug_mode"] = bool(raw["debugMode"])

    return result


if __name__ == "__main__":
    main()
