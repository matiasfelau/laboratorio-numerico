"""Diferencias finitas por expresión o por imágenes dadas."""

import numpy as np
from scipy.differentiate import derivative
from utils.parametros import resolver_config


def f(x):
	return np.exp(x)


def _normalizar_metodo(metodo):
	raw = str(metodo).strip().lower().replace("á", "a")
	if raw in ("progresivo", "adelante"):
		return "progresivo", "Progresivo"
	if raw in ("regresivo", "atras"):
		return "regresivo", "Regresivo"
	if raw in ("central", "centrada"):
		return "central", "Central"
	raise ValueError("Metodo no valido. Usa: Progresivo, Regresivo o Central.")


def derivada_finita(x, h, metodo, y_xm1=None, y_x=None, y_xp1=None):
	metodo_normalizado, etiqueta = _normalizar_metodo(metodo)

	if metodo_normalizado == "progresivo":
		if y_x is None or y_xp1 is None:
			raise ValueError(f"Para '{etiqueta}' debes ingresar f(x) y f(x+h) si no usas expresión.")
		return (y_xp1 - y_x) / h

	if metodo_normalizado == "regresivo":
		if y_xm1 is None or y_x is None:
			raise ValueError(f"Para '{etiqueta}' debes ingresar f(x-h) y f(x) si no usas expresión.")
		return (y_x - y_xm1) / h

	if metodo_normalizado == "central":
		if y_xm1 is None or y_xp1 is None:
			raise ValueError(f"Para '{etiqueta}' debes ingresar f(x-h) y f(x+h) si no usas expresión.")
		return (y_xp1 - y_xm1) / (2 * h)

	raise ValueError("Metodo no valido. Usa: Progresivo, Regresivo o Central.")


def diferencia_finita(x, h, metodo="central", y_xm1=None, y_x=None, y_xp1=None):
	"""Calcula derivada aproximada respetando modos y salidas actuales."""
	precision = resolver_config().precision
	metodo_normalizado, metodo_etiqueta = _normalizar_metodo(metodo)
	usa_imagenes = any(valor is not None for valor in (y_xm1, y_x, y_xp1))

	if h <= 0:
		raise ValueError("El paso h debe ser > 0.")

	# Si no llegan imágenes, se usan desde la expresión inyectada en f.
	if y_xm1 is None:
		y_xm1 = float(f(x - h))
	if y_x is None:
		y_x = float(f(x))
	if y_xp1 is None:
		y_xp1 = float(f(x + h))

	derivada_aprox = float(derivada_finita(x, h, metodo_normalizado, y_xm1=y_xm1, y_x=y_x, y_xp1=y_xp1))
	derivada_aprox = round(derivada_aprox, precision)

	print(f"DIFERENCIA_FINITA_METODO: {metodo_etiqueta}")
	print(f"DIFERENCIA_FINITA_DERIVADA: {derivada_aprox:.{precision}f}")

	if not usa_imagenes:
		try:
			derivada_exacta = round(float(derivative(f, x).df), precision)
			error_exacto = round(abs(derivada_aprox - derivada_exacta), precision)
			print(f"DIFERENCIA_FINITA_DERIVADA_EXACTA: {derivada_exacta:.{precision}f}")
			print(f"DIFERENCIA_FINITA_ERROR_ABSOLUTO: {error_exacto:.{precision}f}")
		except Exception:
			print("DIFERENCIA_FINITA_DERIVADA_EXACTA: N/A")
			print("DIFERENCIA_FINITA_ERROR_ABSOLUTO: N/A")


if __name__ == "__main__":
	diferencia_finita(x=1, h=0.5, metodo="central")
