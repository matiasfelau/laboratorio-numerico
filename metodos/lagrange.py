"""Interpolación de Lagrange y métricas de error.

Contiene dos modos:
- Con función real f(x): calcula error local y cota teórica global.
- Con imágenes y: no calcula error local/exacto no aplicable.
"""

import numpy as np
import sympy as sp
from math import factorial
from fractions import Fraction
from utils.parametros import resolver_config


F_EXPR_HARDCODEADA = "exp(x)"
X_NODOS_HARDCODEADOS = np.array([1.0, 2.0, 3.0])
X_EVAL_HARDCODEADO = 2.5
Y_NODOS_HARDCODEADOS = np.array([np.exp(1.0), np.exp(2.0), np.exp(3.0)])


def _normalizar_texto_matematico(texto):
	return str(texto).replace("π", "pi").replace("ℯ", "euler").strip()


def construir_funcion_real(f_expr_texto):
	x = sp.Symbol("x")
	try:
		f_expr = sp.sympify(
			_normalizar_texto_matematico(f_expr_texto),
			locals={"pi": sp.pi, "e": sp.E, "E": sp.E, "euler": sp.E},
		)
		if f_expr.free_symbols - {x}:
			raise ValueError("La funcion real debe depender solo de x.")
		f_real = sp.lambdify(x, f_expr, modules=["numpy"])
		return f_real, f_expr
	except Exception as exc:
		raise ValueError("La funcion real ingresada no es valida.") from exc


def interpolar_lagrange(x_nodos, y_nodos, x_eval):
	n = len(x_nodos)
	p = 0.0

	for i in range(n):
		li = 1.0
		for j in range(n):
			if i != j:
				li *= (x_eval - x_nodos[j]) / (x_nodos[i] - x_nodos[j])
		p += y_nodos[i] * li

	return p


def error_local(f_real, x, p_x):
	return abs(f_real(x) - p_x)


def error_global_teorico(f_expr, x_nodos, muestras=2000):
	# Cota teórica: M/(n+1)! * max|w(x)| en [a, b], con w(x)=prod(x-x_i).
	x = sp.Symbol("x")
	n = len(x_nodos) - 1
	a = float(np.min(x_nodos))
	b = float(np.max(x_nodos))

	f_der = sp.diff(f_expr, x, n + 1)
	f_der_num = sp.lambdify(x, f_der, modules=["numpy"])

	x_malla = np.linspace(a, b, muestras)
	M = float(np.max(np.abs(f_der_num(x_malla))))

	omega = np.ones_like(x_malla, dtype=float)
	for xi in x_nodos:
		omega *= (x_malla - xi)

	max_omega = float(np.max(np.abs(omega)))
	return (M / factorial(n + 1)) * max_omega


def expresion_polinomio_lagrange(x_nodos, y_nodos):
	x = sp.Symbol("x")
	n = len(x_nodos)
	p = 0

	for i in range(n):
		li = 1
		for j in range(n):
			if i != j:
				li *= (x - x_nodos[j]) / (x_nodos[i] - x_nodos[j])
		p += y_nodos[i] * li

	return sp.expand(sp.simplify(p))


def redondear_expresion(expr, precision):
	replacements = {}
	for number in expr.atoms(sp.Float):
		replacements[number] = sp.Float(round(float(number), precision))
	return expr.xreplace(replacements)


def simplificar_expresion_racional(expr, precision):
	# Intenta recuperar constantes conocidas (pi/e) y fracciones exactas,
	# reduciendo ruido numérico de entradas en float.
	try:
		expr = sp.nsimplify(expr, [sp.pi, sp.E], tolerance=1e-10)
	except Exception:
		pass

	max_den = max(10, 10 ** max(1, int(precision)))
	replacements = {}
	for number in expr.atoms(sp.Float):
		frac = Fraction(float(number)).limit_denominator(max_den)
		replacements[number] = sp.Rational(frac.numerator, frac.denominator)

	expr_racional = expr.xreplace(replacements)
	return sp.simplify(sp.cancel(sp.together(expr_racional)))


def _simbolizar_valor(value, precision):
	try:
		return sp.nsimplify(float(value), [sp.pi, sp.E], tolerance=1e-10)
	except Exception:
		frac = Fraction(float(value)).limit_denominator(max(10, 10 ** max(1, int(precision))))
		return sp.Rational(frac.numerator, frac.denominator)


def _simbolizar_lista(values, precision):
	return [_simbolizar_valor(v, precision) for v in values]


def lagrange(f_expr_texto, x_nodos, x_eval, y_nodos=None):
	"""Ejecuta Lagrange sin alterar reglas de evaluación ya validadas."""
	config = resolver_config()
	precision = config.precision

	f_expr_texto = str(f_expr_texto or "").strip()
	tiene_funcion_real = bool(f_expr_texto)

	if tiene_funcion_real:
		f_real, f_expr = construir_funcion_real(f_expr_texto)
	else:
		f_real = None
		f_expr = None

	x_nodos = np.asarray(x_nodos, dtype=float)
	x_eval = np.atleast_1d(x_eval).astype(float)

	if tiene_funcion_real:
		y_nodos = f_real(x_nodos)
		if np.isscalar(y_nodos):
			y_nodos = np.full_like(x_nodos, float(y_nodos), dtype=float)
		y_nodos = np.asarray(y_nodos, dtype=float)
	else:
		if y_nodos is None:
			raise ValueError("Si no ingresas la funcion real, debes ingresar las imagenes y de los nodos.")
		y_nodos = np.asarray(y_nodos, dtype=float)
		if len(y_nodos) != len(x_nodos):
			raise ValueError("La cantidad de imagenes y debe coincidir con la cantidad de nodos x.")

	errores_locales = []

	for x in x_eval:
		p_x = interpolar_lagrange(x_nodos, y_nodos, x)
		if tiene_funcion_real:
			e_local = error_local(f_real, x, p_x)
			errores_locales.append((x, e_local))
		else:
			errores_locales.append((x, None))

	if tiene_funcion_real:
		e_global = round(error_global_teorico(f_expr, x_nodos), precision)
	else:
		e_global = None

	x = sp.Symbol("x")
	x_nodos_sim = _simbolizar_lista(x_nodos, precision)
	if tiene_funcion_real:
		y_nodos_sim = [sp.simplify(f_expr.subs(x, xi)) for xi in x_nodos_sim]
	else:
		y_nodos_sim = _simbolizar_lista(y_nodos, precision)

	expresion_final = expresion_polinomio_lagrange(x_nodos_sim, y_nodos_sim)
	expresion_final = simplificar_expresion_racional(expresion_final, precision)
	expresion_final_latex = sp.latex(expresion_final)
	if errores_locales and errores_locales[0][1] is not None:
		_, e_local = errores_locales[0]
		error_local_texto = f"{round(e_local, precision):.{precision}f}"
	else:
		error_local_texto = "N/A"

	print(f"LAGRANGE_EXPRESION_FINAL: {expresion_final}")
	print(f"LAGRANGE_EXPRESION_FINAL_LATEX: {expresion_final_latex}")
	print(f"LAGRANGE_ERROR_LOCAL: {error_local_texto}")
	if e_global is None:
		print("LAGRANGE_ERROR_GLOBAL: N/A")
	else:
		print(f"LAGRANGE_ERROR_GLOBAL: {e_global:.{precision}f}")


if __name__ == "__main__":
	lagrange(F_EXPR_HARDCODEADA, X_NODOS_HARDCODEADOS, X_EVAL_HARDCODEADO, Y_NODOS_HARDCODEADOS)
    