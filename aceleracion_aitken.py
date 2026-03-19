import numpy as np
from scipy.differentiate import derivative
from tabulate import tabulate

from utils.configuracion import establecer_configuracion

def g(x):
    return np.exp(-x)

def aceleracion_aitken(x, tipo):
    p, calcular_error, criterio_parada = establecer_configuracion(tipo)

    tabla = []

    if abs(derivative(g, x).df) > 1:
        raise ValueError("La función g no es adecuada para el método de punto fijo en el punto inicial dado.")

    for i in range(p.iteraciones):
        gx = round(g(x), p.precision)
        gx2 = round(g(gx), p.precision)

        den = gx2 - 2 * gx + x

        if den == 0:
            raise ValueError("El denominador en Aitken es cero.")

        xn = round(x - (gx - x) ** 2 / den, p.precision)

        error = calcular_error(xn, x)

        tabla.append([i + 1, x, gx, gx2, xn, error])

        if criterio_parada(error):
            break

        x = xn

    print(tabulate(tabla, headers=["i", "x", "xn+1","xn+2","x*", "e"], tablefmt="grid", floatfmt=f".{p.precision}f"))

aceleracion_aitken(1)