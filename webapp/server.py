from __future__ import annotations

import math

import numpy as np
import sympy as sp
from flask import Flask, jsonify, render_template, request

from app.services.method_registry import get_methods
from app.services.method_runner import MethodRunner
from metodos import lagrange as lagrange_method
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
                            "optional": field.optional,
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
            x_min, x_max = _domain_for_plot(method_key, params)

            if method_key == "lagrange":
                traces, latex_text = _build_lagrange_plot_traces(params, x_min, x_max)
            elif method_key == "diferencia_finita":
                traces, latex_text = _build_diferencia_finita_plot_traces(params, x_min, x_max)
            else:
                expr_key = _expression_key(method_key)
                expr_text = str(params.get(expr_key, "")).strip()
                if not expr_text:
                    raise ValueError("Debes ingresar una funcion para graficar.")

                points = _build_plot_points(expr_text, x_min, x_max)
                if len(points) < 2:
                    raise ValueError("No se pudo graficar: dominio sin puntos validos.")

                traces = [
                    {
                        "name": "Función",
                        "kind": "line",
                        "points": points,
                    }
                ]
                if method_key in {"newton_raphson", "biseccion"}:
                    roots = _estimate_roots_from_points(points)
                    root_trace = _root_markers_on_x_axis(roots)
                    if root_trace is not None:
                        traces.append(root_trace)

                if method_key in {"punto_fijo", "aceleracion_aitken"}:
                    identity_x = np.linspace(x_min, x_max, 401)
                    identity_points = [[float(x_val), float(x_val)] for x_val in identity_x]
                    traces.append(
                        {
                            "name": "Identidad y=x",
                            "kind": "line",
                            "points": identity_points,
                        }
                    )

                    roots = _estimate_roots_from_xy(
                        [float(point[0]) for point in points],
                        [float(point[1] - point[0]) for point in points],
                    )
                    intersection_points = [[float(root), float(root)] for root in roots if math.isfinite(root)]
                    if intersection_points:
                        traces.append(
                            {
                                "name": "Intersección g(x)=x",
                                "kind": "markers",
                                "points": intersection_points,
                            }
                        )
                latex_text = _expression_to_latex(expr_text)

            return jsonify(
                {
                    "success": True,
                    "latex": latex_text,
                    "domain": [x_min, x_max],
                    "traces": traces,
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

        expression_text = _normalize_math_text(str(expression))
        if not expression_text:
            return jsonify({"success": False, "error": "Expresion vacia."}), 400

        try:
            sym_expr = sp.sympify(expression_text, locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E})
            latex_text = sp.latex(sym_expr)
            return jsonify({"success": True, "latex": latex_text})
        except Exception:
            return jsonify({"success": False, "error": "Expresion no valida."}), 400

    @app.post("/api/fixed-point/suggest")
    def fixed_point_suggest():
        body = request.get_json(silent=True) or {}
        expression = body.get("expression")
        point = body.get("point")

        if expression is None:
            return jsonify({"success": False, "error": "Expresion invalida."}), 400

        if point is None:
            return jsonify({"success": False, "error": "Debes indicar el punto x para evaluar convergencia."}), 400

        expression_text = _normalize_math_text(str(expression))
        if not expression_text:
            return jsonify({"success": False, "error": "Expresion vacia."}), 400

        try:
            x0 = _parse_numeric_scalar(str(point), "punto x")
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

        try:
            recommendation = _suggest_fixed_point_function(expression_text, x0)
            return jsonify({"success": True, **recommendation})
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

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
    # Unified symmetric window for all methods: center from method context, fixed radius.
    fallback = (-10.0, 10.0)
    radius = 10.0

    try:
        if method_key == "biseccion":
            a = _parse_numeric_scalar(str(params.get("a", "")), "inicio del intervalo")
            b = _parse_numeric_scalar(str(params.get("b", "")), "final del intervalo")
            center = (a + b) / 2.0
            return center - radius, center + radius

        if method_key in {"newton_raphson", "punto_fijo", "aceleracion_aitken"}:
            center = _parse_numeric_scalar(str(params.get("x", "")), "punto inicial")
            return center - radius, center + radius

        if method_key == "lagrange":
            x_nodos = _parse_numeric_list(str(params.get("x_nodos", "")), "nodos x")
            center = float(np.mean(x_nodos))
            return center - radius, center + radius

        if method_key == "diferencia_finita":
            center = _parse_numeric_scalar(str(params.get("x", "")), "punto x")
            return center - radius, center + radius
    except Exception:
        return fallback

    return fallback


def _build_plot_points(expr_text: str, x_min: float, x_max: float) -> list[list[float]]:
    x_symbol = sp.Symbol("x")
    try:
        expr = sp.sympify(_normalize_math_text(expr_text), locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E})
        fn = sp.lambdify(x_symbol, expr, modules=["numpy"])
    except Exception as exc:
        raise ValueError("La expresion de la funcion no es valida.") from exc

    x_values = np.linspace(x_min, x_max, 401)
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

        # Keep plotted values within the visual working range.
        if abs(y) > 10:
            continue

        points.append([float(x_val), y])

    return points


def _estimate_roots_from_points(points: list[list[float]], max_roots: int = 10) -> list[float]:
    if not points:
        return []

    x_values: list[float] = []
    y_values: list[float] = []
    for point in points:
        if len(point) != 2:
            continue
        x_val = float(point[0])
        y_val = float(point[1])
        if not math.isfinite(x_val) or not math.isfinite(y_val):
            continue
        x_values.append(x_val)
        y_values.append(y_val)

    return _estimate_roots_from_xy(x_values, y_values, max_roots=max_roots)


def _estimate_roots_from_xy(x_values: list[float], y_values: list[float], max_roots: int = 10) -> list[float]:
    if len(x_values) < 2 or len(y_values) < 2:
        return []

    roots: list[float] = []
    eps = 1e-9

    for i in range(len(x_values) - 1):
        x1 = float(x_values[i])
        x2 = float(x_values[i + 1])
        y1 = float(y_values[i])
        y2 = float(y_values[i + 1])

        if abs(y1) <= eps:
            roots.append(x1)
            if len(roots) >= max_roots:
                break

        if y1 == y2:
            continue

        if y1 * y2 < 0:
            root = x1 - y1 * (x2 - x1) / (y2 - y1)
            if math.isfinite(root):
                roots.append(float(root))
                if len(roots) >= max_roots:
                    break

    if len(roots) < max_roots and abs(float(y_values[-1])) <= eps:
        roots.append(float(x_values[-1]))

    if not roots:
        return []

    roots.sort()
    deduped: list[float] = []
    for root in roots:
        if not deduped or abs(root - deduped[-1]) > 1e-4:
            deduped.append(root)

    return deduped[:max_roots]


def _root_markers_on_x_axis(roots: list[float], name: str = "Raíces") -> dict[str, object] | None:
    if not roots:
        return None

    points = [[float(root), 0.0] for root in roots if math.isfinite(root)]
    if not points:
        return None

    return {
        "name": name,
        "kind": "markers",
        "points": points,
    }


def _normalize_fd_method(metodo: str) -> str:
    raw = str(metodo or "").strip().lower().replace("á", "a")
    if raw in {"progresivo", "adelante"}:
        return "progresivo"
    if raw in {"regresivo", "atras"}:
        return "regresivo"
    if raw in {"central", "centrada"}:
        return "central"
    raise ValueError("Metodo no valido. Usa: Progresivo, Regresivo o Central.")


def _finite_difference_derivative(
    metodo: str,
    h: float,
    y_xm1: float | None,
    y_x: float | None,
    y_xp1: float | None,
) -> float:
    if h <= 0:
        raise ValueError("El paso h debe ser > 0.")

    metodo_normalizado = _normalize_fd_method(metodo)

    if metodo_normalizado == "progresivo":
        if y_x is None or y_xp1 is None:
            raise ValueError("Para Progresivo debes ingresar f(x) y f(x+h).")
        return (y_xp1 - y_x) / h

    if metodo_normalizado == "regresivo":
        if y_xm1 is None or y_x is None:
            raise ValueError("Para Regresivo debes ingresar f(x-h) y f(x).")
        return (y_x - y_xm1) / h

    if y_xm1 is None or y_xp1 is None:
        raise ValueError("Para Central debes ingresar f(x-h) y f(x+h).")
    return (y_xp1 - y_xm1) / (2 * h)


def _build_diferencia_finita_plot_traces(
    params: dict[str, object], x_min: float, x_max: float
) -> tuple[list[dict[str, object]], str]:
    x0 = _parse_numeric_scalar(str(params.get("x", "")), "punto x")
    h = _parse_numeric_scalar(str(params.get("h", "")), "paso h")
    metodo = str(params.get("metodo", "Central"))

    expr_text = _normalize_math_text(str(params.get("f_expr", "")))

    y_xm1_raw = str(params.get("y_xm1", "")).strip()
    y_x_raw = str(params.get("y_x", "")).strip()
    y_xp1_raw = str(params.get("y_xp1", "")).strip()

    y_xm1 = _parse_numeric_scalar(y_xm1_raw, "imagen f(x-h)") if y_xm1_raw else None
    y_x = _parse_numeric_scalar(y_x_raw, "imagen f(x)") if y_x_raw else None
    y_xp1 = _parse_numeric_scalar(y_xp1_raw, "imagen f(x+h)") if y_xp1_raw else None

    traces: list[dict[str, object]] = []

    if expr_text:
        fn, expr = _build_sympy_numeric_function(expr_text)
        x_values = np.linspace(x_min, x_max, 401)
        y_values = fn(x_values)
        if np.isscalar(y_values):
            y_values = np.full_like(x_values, y_values, dtype=float)
        function_points = _points_from_xy(x_values, y_values)
        if len(function_points) < 2:
            raise ValueError("No se pudo graficar la función de diferencia finita.")
        traces.append({"name": "Función", "kind": "line", "points": function_points})

        if y_x is None:
            y_x = _safe_real_float(fn(x0))
        if y_xm1 is None:
            y_xm1 = _safe_real_float(fn(x0 - h))
        if y_xp1 is None:
            y_xp1 = _safe_real_float(fn(x0 + h))

        x_symbol = sp.Symbol("x")
        tangent_real_slope = _safe_real_float(sp.diff(expr, x_symbol).subs(x_symbol, x0).evalf())
        if tangent_real_slope is not None and y_x is not None:
            x_line = np.linspace(x_min, x_max, 161)
            y_line = tangent_real_slope * (x_line - x0) + y_x
            tangent_real_points = _points_from_xy(x_line, y_line)
            if len(tangent_real_points) >= 2:
                traces.append(
                    {
                        "name": "Tangente real",
                        "kind": "line",
                        "dash": "dash",
                        "points": tangent_real_points,
                    }
                )

        latex_text = _expression_to_latex(expr_text)
    else:
        sample_points: list[list[float]] = []
        if y_xm1 is not None:
            sample_points.append([x0 - h, y_xm1])
        if y_x is not None:
            sample_points.append([x0, y_x])
        if y_xp1 is not None:
            sample_points.append([x0 + h, y_xp1])

        sample_points.sort(key=lambda item: item[0])
        if sample_points:
            traces.append({"name": "Muestras", "kind": "markers", "points": sample_points})

        latex_text = ""

    metodo_normalizado = _normalize_fd_method(metodo)
    if y_x is None and metodo_normalizado == "central" and y_xm1 is not None and y_xp1 is not None:
        # Midpoint estimate to anchor the tangent when only f(x-h) and f(x+h) are provided.
        y_x = (y_xm1 + y_xp1) / 2.0

    if y_x is None:
        raise ValueError("No se pudo determinar f(x) en el punto para construir la tangente aproximada.")

    tangent_aprox_slope = _finite_difference_derivative(metodo, h, y_xm1, y_x, y_xp1)
    x_line = np.linspace(x_min, x_max, 161)
    y_line = tangent_aprox_slope * (x_line - x0) + y_x
    tangent_aprox_points = _points_from_xy(x_line, y_line)
    if len(tangent_aprox_points) >= 2:
        traces.append({"name": "Tangente aproximada", "kind": "line", "points": tangent_aprox_points})
    traces.append({"name": "Punto de tangencia", "kind": "markers", "points": [[x0, y_x]]})

    return traces, latex_text


def _build_lagrange_plot_traces(
    params: dict[str, object], x_min: float, x_max: float
) -> tuple[list[dict[str, object]], str]:
    f_expr_text = _normalize_math_text(str(params.get("f_expr", "")) )
    x_nodos = _parse_numeric_list(str(params.get("x_nodos", "")), "nodos x")
    y_nodos_text = str(params.get("y_nodos", "")).strip()

    if f_expr_text:
        f_real_num, f_real_expr = _build_sympy_numeric_function(f_expr_text)
        y_nodos = np.asarray(f_real_num(x_nodos), dtype=float)
        latex_text = _expression_to_latex(f_expr_text)
    else:
        if not y_nodos_text:
            raise ValueError("Para graficar Lagrange debes ingresar función real o imágenes de nodos.")
        y_nodos = _parse_numeric_list(y_nodos_text, "imagenes y")
        if len(y_nodos) != len(x_nodos):
            raise ValueError("La cantidad de imágenes y debe coincidir con la cantidad de nodos x.")
        f_real_num = None
        f_real_expr = None
        latex_text = ""

    p_expr = lagrange_method.expresion_polinomio_lagrange(x_nodos, y_nodos)
    x_symbol = sp.Symbol("x")
    p_num = sp.lambdify(x_symbol, p_expr, modules=["numpy"])

    x_values = np.linspace(x_min, x_max, 401)
    y_aprox = p_num(x_values)
    if np.isscalar(y_aprox):
        y_aprox = np.full_like(x_values, y_aprox, dtype=float)

    approx_points = _points_from_xy(x_values, y_aprox)
    if len(approx_points) < 2:
        raise ValueError("No se pudo graficar el polinomio interpolante.")

    traces: list[dict[str, object]] = []

    if f_real_num is not None:
        y_real = f_real_num(x_values)
        if np.isscalar(y_real):
            y_real = np.full_like(x_values, y_real, dtype=float)
        real_points = _points_from_xy(x_values, y_real)
        if real_points:
            traces.append({"name": "Curva real", "kind": "line", "dash": "dash", "points": real_points})

    traces.append({"name": "Interpolante de Lagrange", "kind": "line", "points": approx_points})
    traces.append({"name": "Nodos", "kind": "markers", "points": _points_from_xy(x_nodos, y_nodos)})

    if f_real_expr is None:
        latex_text = sp.latex(sp.simplify(p_expr))

    return traces, latex_text


def _points_from_xy(x_values: np.ndarray, y_values: np.ndarray) -> list[list[float]]:
    points: list[list[float]] = []
    for x_val, y_val in zip(x_values, y_values):
        try:
            y = float(y_val)
        except Exception:
            continue

        if not math.isfinite(y) or abs(y) > 10:
            continue

        points.append([float(x_val), y])
    return points


def _build_sympy_numeric_function(expr_text: str):
    x = sp.Symbol("x")
    try:
        expr = sp.sympify(_normalize_math_text(expr_text), locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E})
        if expr.free_symbols - {x}:
            raise ValueError("La expresión debe depender solo de x.")
        return sp.lambdify(x, expr, modules=["numpy"]), expr
    except Exception as exc:
        raise ValueError("La expresion de la funcion no es valida.") from exc


def _parse_numeric_scalar(text: str, field_name: str) -> float:
    raw = _normalize_math_text(text)
    if not raw:
        raise ValueError(f"Debes ingresar un valor para {field_name}.")

    try:
        expr = sp.sympify(raw, locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E})
    except Exception as exc:
        raise ValueError(f"Valor inválido para {field_name}.") from exc

    if expr.free_symbols:
        raise ValueError(f"Valor inválido para {field_name}: solo constantes numéricas.")

    value = float(expr.evalf())
    if not math.isfinite(value):
        raise ValueError(f"Valor inválido para {field_name}: debe ser real finito.")

    return value


def _parse_numeric_list(text: str, field_name: str) -> np.ndarray:
    parts = [item.strip() for item in text.split(",") if item.strip()]
    if len(parts) < 2:
        raise ValueError(f"Debes ingresar al menos dos valores en {field_name}.")

    values = [_parse_numeric_scalar(part, field_name) for part in parts]
    return np.asarray(values, dtype=float)


def _expression_to_latex(expr_text: str) -> str:
    try:
        expr = sp.sympify(_normalize_math_text(expr_text), locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E})
        return sp.latex(expr)
    except Exception as exc:
        raise ValueError("La expresion de la funcion no es valida.") from exc


def _safe_real_float(value: object) -> float | None:
    try:
        numeric = complex(value)
    except Exception:
        return None

    if abs(numeric.imag) > 1e-9:
        return None

    real_value = float(numeric.real)
    if not math.isfinite(real_value):
        return None
    return real_value


def _evaluate_abs_gprime(g_expr: sp.Expr, x_symbol: sp.Symbol, x0: float) -> float | None:
    try:
        g_prime_expr = sp.diff(g_expr, x_symbol)
        g_prime_value = _safe_real_float(g_prime_expr.subs(x_symbol, x0).evalf())
    except Exception:
        return None

    if g_prime_value is None:
        return None
    return abs(g_prime_value)


def _suggest_fixed_point_function(expr_text: str, x0: float) -> dict[str, object]:
    x = sp.Symbol("x")
    locals_map = {"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E}

    try:
        f_expr = sp.sympify(_normalize_math_text(expr_text), locals=locals_map)
    except Exception as exc:
        raise ValueError("La expresion f(x) no es valida.") from exc

    # Prefer exact rational coefficients whenever possible.
    try:
        f_expr = sp.nsimplify(f_expr, [sp.pi, sp.E], tolerance=1e-10)
    except Exception:
        f_expr = sp.simplify(f_expr)

    if f_expr.free_symbols - {x}:
        raise ValueError("La funcion debe depender solo de x.")

    attempts_limit = 30
    attempts = 0
    candidates: list[tuple[float, sp.Expr]] = []

    # Primer enfoque: despejar x de f(x)=0 para obtener candidatas g(x).
    try:
        solved = sp.solve(sp.Eq(f_expr, 0), x)
    except Exception:
        solved = []

    for g_raw in solved:
        if attempts >= attempts_limit:
            break
        attempts += 1

        try:
            g_expr = sp.nsimplify(sp.simplify(g_raw), [sp.pi, sp.E], tolerance=1e-10)
            g_expr = sp.cancel(sp.together(g_expr))
        except Exception:
            continue

        if g_expr.free_symbols - {x}:
            continue

        abs_gprime = _evaluate_abs_gprime(g_expr, x, x0)
        if abs_gprime is None:
            continue
        if abs_gprime <= 1.0:
            candidates.append((abs_gprime, g_expr))

    # Segundo enfoque: transformaciones alternativas si despeje no cumple.
    if not candidates and attempts < attempts_limit:
        derivative_at_point = _safe_real_float(sp.diff(f_expr, x).subs(x, x0).evalf())
        alpha_candidates: list[float] = []
        if derivative_at_point is not None and abs(derivative_at_point) > 1e-10:
            alpha_candidates.append(-1.0 / derivative_at_point)
        alpha_candidates.extend([-1.0, -0.5, -0.25, -0.1, 0.1, 0.25, 0.5, 1.0])

        for alpha in alpha_candidates:
            if attempts >= attempts_limit:
                break
            attempts += 1

            alpha_sym = sp.nsimplify(alpha, [sp.pi, sp.E], tolerance=1e-10)
            g_expr = sp.simplify(x + alpha_sym * f_expr)
            g_expr = sp.cancel(sp.together(sp.nsimplify(g_expr, [sp.pi, sp.E], tolerance=1e-10)))
            abs_gprime = _evaluate_abs_gprime(g_expr, x, x0)
            if abs_gprime is None:
                continue
            if abs_gprime <= 1.0:
                candidates.append((abs_gprime, g_expr))

    if not candidates:
        raise ValueError(
            "No se encontró una g(x) recomendada tras varios intentos con el criterio |g'(x0)| <= 1."
        )

    candidates.sort(key=lambda item: item[0])
    best_abs_gprime, best_g_expr = candidates[0]
    best_g_expr = sp.cancel(sp.together(sp.nsimplify(best_g_expr, [sp.pi, sp.E], tolerance=1e-10)))

    return {
        "g_expression": str(best_g_expr),
        "g_latex": sp.latex(best_g_expr),
        "criterion": round(best_abs_gprime, 10),
        "point": round(float(x0), 10),
        "attempts": attempts,
    }


def _normalize_math_text(text: str) -> str:
    return str(text).replace("π", "pi").replace("ℯ", "euler").strip()


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
